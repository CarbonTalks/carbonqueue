import logging
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
from litestar import Litestar, Request, Response, get
from litestar.di import NamedDependency, Provide
from litestar.middleware import DefineMiddleware

from cq_backend.agent.extract import ExtractionAgent
from cq_backend.api.applications import (
    correct_observations,
    extract,
    get_application,
    list_applications,
)
from cq_backend.api.queue import get_queue, run_queue
from cq_backend.api.simulations import get_simulation, run_simulation
from cq_backend.config import Settings
from cq_backend.documents.docling import DoclingParser
from cq_backend.domain.application import ProcessingStatus
from cq_backend.errors import BackendError
from cq_backend.integrations.ml import HTTPMLService
from cq_backend.integrations.queue_engine import HTTPQueueEngine
from cq_backend.services.documents import DocumentService
from cq_backend.services.orchestration import OrchestrationService
from cq_backend.storage.zova import ZovaStorage

logger = logging.getLogger("cq_backend")


class RequestIDMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append(
                    (b"x-request-id", request_id.encode())
                )
                logger.info(
                    "request_id=%s method=%s path=%s status=%s",
                    request_id,
                    scope["method"],
                    scope["path"],
                    message["status"],
                )
            await send(message)

        await self.app(scope, receive, send_with_request_id)


def handle_backend_error(request: Request, error: BackendError) -> Response:
    return Response(
        {
            "code": error.code,
            "message": error.message,
            "application_id": error.application_id,
            "request_id": request.scope.get("state", {}).get("request_id"),
        },
        status_code=error.status_code,
    )


@get("/health")
async def health(service: NamedDependency[OrchestrationService]) -> dict[str, str]:
    await service.storage.list_applications()
    return {"status": "ok"}


def create_app(
    settings: Settings | None = None,
    *,
    parser=None,
    extractor=None,
    ml=None,
    queue_engine=None,
) -> Litestar:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: Litestar):
        storage = ZovaStorage(settings.data_dir / "carbonqueue.zova")
        async with httpx.AsyncClient(timeout=30) as http_client:
            try:
                await storage.open()
                for application in await storage.list_applications():
                    if application.status in {
                        ProcessingStatus.UPLOADED,
                        ProcessingStatus.PARSING,
                        ProcessingStatus.EXTRACTING,
                    }:
                        previous_revision = application.revision
                        application.revision += 1
                        application.status = ProcessingStatus.FAILED
                        application.error = "PROCESSING_INTERRUPTED"
                        await storage.save_application(
                            application, expected_revision=previous_revision
                        )
                configured_extractor = extractor
                if configured_extractor is None and settings.extraction_model:
                    configured_extractor = ExtractionAgent(settings.extraction_model)
                app.state.service = OrchestrationService(
                    storage,
                    DocumentService(
                        settings.data_dir / "documents",
                        settings.max_file_bytes,
                        settings.max_files,
                    ),
                    parser or DoclingParser(settings.max_pages),
                    configured_extractor,
                    ml
                    or (
                        HTTPMLService(http_client, settings.ml_url)
                        if settings.ml_url
                        else None
                    ),
                    queue_engine
                    or (
                        HTTPQueueEngine(http_client, settings.queue_engine_url)
                        if settings.queue_engine_url
                        else None
                    ),
                    settings,
                )
                yield
            finally:
                await storage.close()

    async def provide_service(request: Request) -> OrchestrationService:
        return request.app.state.service

    return Litestar(
        route_handlers=[
            health,
            extract,
            list_applications,
            get_application,
            correct_observations,
            run_queue,
            get_queue,
            run_simulation,
            get_simulation,
        ],
        dependencies={"service": Provide(provide_service)},
        lifespan=[lifespan],
        exception_handlers={BackendError: handle_backend_error},
        middleware=[DefineMiddleware(RequestIDMiddleware)],
        request_max_body_size=settings.max_file_bytes * settings.max_files
        + 1024 * 1024,
        multipart_form_part_limit=settings.max_files,
    )


app = create_app()
