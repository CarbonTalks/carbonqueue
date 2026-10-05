import asyncio

from pydantic import ValidationError

from cq_backend.agent.extract import Extractor
from cq_backend.agent.reconcile import reconcile, valid_value
from cq_backend.config import Settings
from cq_backend.documents.docling import DocumentParser
from cq_backend.domain.application import (
    Application,
    CarbonEstimate,
    CarbonScenario,
    Correction,
    CorrectionRequest,
    EffortEstimate,
    Prediction,
    ProcessingStatus,
    new_id,
)
from cq_backend.domain.queue import (
    QueueRequest,
    QueueResult,
    SimulationConfig,
    SimulationInput,
    SimulationResult,
)
from cq_backend.errors import BackendError
from cq_backend.integrations.ml import MLService
from cq_backend.integrations.queue_engine import QueueEngine
from cq_backend.services.documents import DocumentService
from cq_backend.storage.zova import ZovaStorage


class OrchestrationService:
    def __init__(
        self,
        storage: ZovaStorage,
        documents: DocumentService,
        parser: DocumentParser,
        extractor: Extractor | None,
        ml: MLService | None,
        queue_engine: QueueEngine | None,
        settings: Settings,
    ):
        self.storage = storage
        self.documents = documents
        self.parser = parser
        self.extractor = extractor
        self.ml = ml
        self.queue_engine = queue_engine
        self.settings = settings
        self._processing = asyncio.Semaphore(1)

    async def _save(self, application: Application) -> None:
        previous = application.revision
        application.revision += 1
        await self.storage.save_application(application, expected_revision=previous)

    async def process_application(self, files) -> Application:
        if self.extractor is None:
            raise BackendError(
                "EXTRACTOR_UNAVAILABLE",
                "Configure CQ_EXTRACTION_MODEL to enable extraction",
            )
        async with self._processing:
            application = Application(documents=await self.documents.ingest(files))
            try:
                await self.storage.save_application(application, expected_revision=0)
            except BackendError:
                await self.documents.remove(application.documents)
                raise
            try:
                async with asyncio.timeout(self.settings.extraction_timeout_seconds):
                    application.status = ProcessingStatus.PARSING
                    await self._save(application)
                    for document in application.documents:
                        application.parsed_documents.append(
                            await self.parser.parse(
                                document.document_id,
                                self.documents.root / document.storage_reference,
                            )
                        )
                    application.status = ProcessingStatus.EXTRACTING
                    await self._save(application)
                    application.observations = await self.extractor.extract(
                        application.parsed_documents
                    )
                    application.project_features, application.readiness = reconcile(
                        application.observations, documents=application.parsed_documents
                    )
                    application.status = (
                        ProcessingStatus.READY
                        if application.readiness.ready_for_review
                        else ProcessingStatus.NEEDS_REVIEW
                    )
                    await self._save(application)
            except Exception as error:
                failure = (
                    error
                    if isinstance(error, BackendError)
                    else BackendError(
                        "PROCESSING_FAILED", "Document processing failed", 502
                    )
                )
                # A storage failure must not trigger another write with uncertain revision.
                if failure.code not in {"PERSISTENCE_FAILURE", "STALE_REVISION"}:
                    application.status = ProcessingStatus.FAILED
                    application.error = failure.code
                    await self._save(application)
                failure.application_id = application.application_id
                raise failure from error
            if (
                application.readiness.ready_for_review
                and self.ml is not None
                and self.queue_engine is not None
            ):
                application = await self.score(application, CarbonScenario())
                await self._save(application)
            return application

    async def correct(
        self, application_id: str, request: CorrectionRequest
    ) -> Application:
        application = await self.storage.get_application(application_id)
        if application.revision != request.expected_revision:
            raise BackendError(
                "STALE_REVISION", "Application revision has changed", 409
            )
        if application.status not in {
            ProcessingStatus.NEEDS_REVIEW,
            ProcessingStatus.READY,
            ProcessingStatus.SCORED,
        }:
            raise BackendError(
                "INVALID_STATE", "Application is not available for correction", 409
            )
        if any(not valid_value(name, value) for name, value in request.values.items()):
            raise BackendError(
                "INVALID_CORRECTION", "Correction contains an invalid value", 400
            )
        overrides = {
            correction.field: correction.corrected_value
            for correction in application.corrections
        }
        for name, value in request.values.items():
            application.corrections.append(
                Correction(
                    field=name,
                    original_values=[
                        item.value
                        for item in application.observations
                        if item.field == name
                    ],
                    previous_value=overrides.get(name),
                    corrected_value=value,
                    actor=request.actor,
                    reason=request.reason,
                )
            )
        overrides.update(request.values)
        application.project_features, application.readiness = reconcile(
            application.observations,
            documents=application.parsed_documents,
            overrides=overrides,
        )
        application.status = (
            ProcessingStatus.READY
            if application.readiness.ready_for_review
            else ProcessingStatus.NEEDS_REVIEW
        )
        application.prediction = application.carbon = application.effort = (
            application.scenario
        ) = None
        application.queue_run_id = None
        application.error = None
        await self._save(application)
        return application

    async def score(
        self, application: Application, scenario: CarbonScenario
    ) -> Application:
        if (
            not application.readiness.ready_for_review
            or application.project_features is None
        ):
            raise BackendError(
                "NOT_READY", "Application requires review before scoring", 409
            )
        if self.ml is None:
            raise BackendError("ML_UNAVAILABLE", "ML component unavailable")
        if self.queue_engine is None:
            raise BackendError("QUEUE_ENGINE_UNAVAILABLE", "Queue engine unavailable")
        try:
            try:
                prediction = Prediction.model_validate(
                    await self.ml.predict(application.project_features)
                )
            except BackendError:
                raise
            except ValidationError as error:
                raise BackendError(
                    "ML_INVALID_RESPONSE",
                    "ML component returned an invalid prediction",
                    502,
                ) from error
            except Exception as error:
                raise BackendError(
                    "ML_UNAVAILABLE", "ML component unavailable"
                ) from error
            try:
                enriched = application.model_copy(deep=True)
                enriched.prediction = prediction
                carbon = CarbonEstimate.model_validate(
                    await self.queue_engine.carbon(enriched, scenario)
                )
                effort = EffortEstimate.model_validate(
                    await self.queue_engine.effort(enriched)
                )
            except BackendError:
                raise
            except ValidationError as error:
                raise BackendError(
                    "QUEUE_INVALID_RESPONSE",
                    "Queue engine returned an invalid response",
                    502,
                ) from error
            except Exception as error:
                raise BackendError(
                    "QUEUE_ENGINE_UNAVAILABLE", "Queue engine unavailable"
                ) from error
        except BackendError as error:
            application.error = error.code
            await self._save(application)
            error.application_id = application.application_id
            raise
        application.prediction, application.carbon, application.effort = (
            prediction,
            carbon,
            effort,
        )
        application.scenario = scenario
        application.status = ProcessingStatus.SCORED
        application.error = None
        return application

    async def _applications(self, ids: list[str]) -> list[Application]:
        if len(set(ids)) != len(ids):
            raise BackendError(
                "DUPLICATE_APPLICATION", "Application IDs must be unique", 400
            )
        applications = [
            await self.storage.get_application(application_id) for application_id in ids
        ]
        if any(
            not application.readiness.ready_for_review for application in applications
        ):
            raise BackendError(
                "NOT_READY", "All selected applications must be ready", 409
            )
        return applications

    async def run_queue(self, request: QueueRequest) -> QueueResult:
        if self.queue_engine is None:
            raise BackendError("QUEUE_ENGINE_UNAVAILABLE", "Queue engine unavailable")
        applications = await self._applications(request.application_ids)
        for index, application in enumerate(applications):
            applications[index] = await self.score(application, request.scenario)
        try:
            result = QueueResult.model_validate(
                await self.queue_engine.schedule(
                    applications, request.policy, request.capacity
                )
            )
        except BackendError:
            raise
        except Exception as error:
            raise BackendError(
                "QUEUE_ENGINE_UNAVAILABLE", "Queue engine unavailable"
            ) from error
        ids = [entry.application_id for entry in result.entries]
        positions = [entry.position for entry in result.entries]
        if (
            not set(ids) <= set(request.application_ids)
            or len(set(ids)) != len(ids)
            or len(set(positions)) != len(positions)
        ):
            raise BackendError(
                "QUEUE_INVALID_RESPONSE", "Queue engine returned invalid entries", 502
            )
        result.queue_run_id = new_id()
        for application in applications:
            application.queue_run_id = result.queue_run_id
            application.revision += 1
        await self.storage.save_output(
            result.queue_run_id, "queue", result.model_dump_json(), applications
        )
        return result

    async def get_queue(self) -> QueueResult:
        result = QueueResult.model_validate_json(await self.storage.get_output("queue"))
        for entry in result.entries:
            application = await self.storage.get_application(entry.application_id)
            if application.queue_run_id != result.queue_run_id:
                raise BackendError(
                    "QUEUE_STALE", "Application data changed; run the queue again", 409
                )
        return result

    async def run_simulation(self, config: SimulationConfig) -> SimulationResult:
        if self.queue_engine is None:
            raise BackendError("QUEUE_ENGINE_UNAVAILABLE", "Queue engine unavailable")
        applications = await self._applications(config.application_ids)
        try:
            result = SimulationResult.model_validate(
                await self.queue_engine.simulate(
                    SimulationInput(**config.model_dump(), projects=applications)
                )
            )
        except BackendError:
            raise
        except Exception as error:
            raise BackendError(
                "QUEUE_ENGINE_UNAVAILABLE", "Queue engine unavailable"
            ) from error
        result.simulation_id = new_id()
        for application in applications:
            application.simulation_ids.append(result.simulation_id)
            application.revision += 1
        await self.storage.save_output(
            result.simulation_id, "simulation", result.model_dump_json(), applications
        )
        return result
