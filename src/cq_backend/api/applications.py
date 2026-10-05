from litestar import get, patch, post
from litestar.datastructures import UploadFile
from litestar.di import NamedDependency
from litestar.params import FromPath, MultipartBody

from cq_backend.domain.application import Application, CorrectionRequest
from cq_backend.services.orchestration import OrchestrationService


@post("/applications/extract")
async def extract(
    data: MultipartBody[list[UploadFile]],
    service: NamedDependency[OrchestrationService],
) -> Application:
    return await service.process_application(data)


@get("/applications")
async def list_applications(
    service: NamedDependency[OrchestrationService],
) -> list[Application]:
    return await service.storage.list_applications()


@get("/applications/{application_id:str}")
async def get_application(
    application_id: FromPath[str], service: NamedDependency[OrchestrationService]
) -> Application:
    return await service.storage.get_application(application_id)


@patch("/applications/{application_id:str}/observations")
async def correct_observations(
    application_id: FromPath[str],
    data: CorrectionRequest,
    service: NamedDependency[OrchestrationService],
) -> Application:
    return await service.correct(application_id, data)
