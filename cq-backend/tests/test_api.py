from litestar.testing import TestClient

from cq_backend.app import create_app
from cq_backend.config import Settings
from cq_backend.domain.application import (
    CarbonEstimate,
    EffortEstimate,
    Evidence,
    ExtractedField,
    ParsedDocument,
    ParsedPage,
    Prediction,
)
from cq_backend.domain.queue import QueueEntry, QueueResult, SimulationResult


class Parser:
    async def parse(self, document_id, path):
        return ParsedDocument(
            document_id=document_id,
            pages=[ParsedPage(number=1, text="Solar 12 MW and 12.6 MW")],
        )


class Extractor:
    def __init__(self, conflict=False):
        self.conflict = conflict

    async def extract(self, documents):
        evidence = [
            Evidence(document_id=documents[0].document_id, page=1, quote="Solar 12 MW")
        ]
        result = [
            ExtractedField(
                field="technology", value="solar", confidence=0.99, evidence=evidence
            ),
            ExtractedField(
                field="capacity_mw",
                capacity_scope="proposed_project",
                value=12,
                unit="MW",
                confidence=0.99,
                evidence=evidence,
            ),
        ]
        if self.conflict:
            result.append(
                ExtractedField(
                    field="capacity_mw",
                    capacity_scope="proposed_project",
                    value=12.6,
                    unit="MW",
                    confidence=0.99,
                    evidence=[
                        Evidence(
                            document_id=documents[0].document_id,
                            page=1,
                            quote="12.6 MW",
                        )
                    ],
                )
            )
        return result


class ML:
    async def predict(self, project):
        return Prediction(
            withdrawal_probability_12m=0.2,
            decision_distribution=[0.4] + [0.0] * 11 + [0.6],
        )


class Engine:
    async def carbon(self, application, scenario):
        return CarbonEstimate(
            tonnes_co2e=123, methodology_reference="external-test-engine"
        )

    async def effort(self, application):
        return EffortEstimate(reviewer_hours=2)

    async def schedule(self, applications, policy, capacity):
        return QueueResult(
            entries=[
                QueueEntry(application_id=app.application_id, position=i + 1)
                for i, app in enumerate(applications)
            ]
        )

    async def simulate(self, config):
        return SimulationResult(metrics={"reviewed": 1})


def client(tmp_path, *, conflict=False, ml=None, engine=None):
    return TestClient(
        create_app(
            Settings(data_dir=tmp_path),
            parser=Parser(),
            extractor=Extractor(conflict),
            ml=ml,
            queue_engine=engine,
        )
    )


def upload(test_client):
    return test_client.post(
        "/applications/extract",
        files=[("files", ("plan.pdf", b"%PDF-1.7\nfixture", "application/pdf"))],
    )


def test_upload_list_get_and_health(tmp_path):
    with client(tmp_path) as test_client:
        response = upload(test_client)
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["status"] == "READY"
        assert body["readiness"]["ready_for_review"]
        assert response.headers["x-request-id"]
        assert (
            test_client.get("/applications").json()[0]["application_id"]
            == body["application_id"]
        )
        assert test_client.get(f"/applications/{body['application_id']}").json() == body
        assert test_client.get("/health").status_code == 200
        assert test_client.get("/applications/missing").status_code == 404


def test_correction_resolves_conflict_and_records_original_values(tmp_path):
    with client(tmp_path, conflict=True) as test_client:
        body = upload(test_client).json()
        assert body["status"] == "NEEDS_REVIEW"
        response = test_client.patch(
            f"/applications/{body['application_id']}/observations",
            json={
                "expected_revision": body["revision"],
                "actor": "reviewer-1",
                "values": {"capacity_mw": 12.6},
                "reason": "Confirmed technical report",
            },
        )
        assert response.status_code == 200, response.text
        corrected = response.json()
        assert corrected["status"] == "READY"
        assert len(corrected["observations"]) == 3
        assert corrected["corrections"][0]["original_values"] == [12, 12.6]
        assert corrected["corrections"][0]["actor"] == "reviewer-1"
        assert (
            test_client.patch(
                f"/applications/{body['application_id']}/observations",
                json={
                    "expected_revision": body["revision"],
                    "actor": "reviewer-1",
                    "values": {"capacity_mw": 13},
                },
            ).status_code
            == 409
        )


def test_external_results_queue_and_simulation_are_persisted(tmp_path):
    with client(tmp_path, ml=ML(), engine=Engine()) as test_client:
        app = upload(test_client).json()
        assert app["status"] == "SCORED"
        assert app["prediction"]["withdrawal_probability_12m"] == 0.2
        queue = test_client.post(
            "/queue/run",
            json={
                "application_ids": [app["application_id"]],
                "capacity": 8,
                "policy": {"name": "external-policy"},
            },
        )
        assert queue.status_code == 201, queue.text
        assert test_client.get("/queue").json() == queue.json()
        simulation = test_client.post(
            "/simulation/run",
            json={"application_ids": [app["application_id"]], "parameters": {}},
        )
        assert simulation.status_code == 201, simulation.text
        assert (
            test_client.get(f"/simulation/{simulation.json()['simulation_id']}").json()
            == simulation.json()
        )


def test_missing_queue_engine_returns_explicit_unavailability(tmp_path):
    with client(tmp_path) as test_client:
        response = test_client.post(
            "/queue/run",
            json={"application_ids": [], "capacity": 8, "policy": {"name": "FIFO"}},
        )
        assert response.status_code == 503
        assert response.json()["code"] == "QUEUE_ENGINE_UNAVAILABLE"


class BrokenML:
    async def predict(self, project):
        raise RuntimeError("private provider details")


def test_integration_failure_preserves_ready_state_and_does_not_leak_details(tmp_path):
    with client(tmp_path, ml=BrokenML(), engine=Engine()) as test_client:
        response = upload(test_client)
        assert response.status_code == 503
        error = response.json()
        assert "private provider" not in response.text
        app = test_client.get(f"/applications/{error['application_id']}").json()
        assert app["status"] == "READY"
        assert app["prediction"] is None
        assert app["error"] == "ML_UNAVAILABLE"


def test_invalid_correction_does_not_modify_stored_state(tmp_path):
    with client(tmp_path) as test_client:
        body = upload(test_client).json()
        response = test_client.patch(
            f"/applications/{body['application_id']}/observations",
            json={
                "expected_revision": body["revision"],
                "actor": "reviewer",
                "values": {"capacity_mw": -1},
            },
        )
        assert response.status_code == 400
        assert test_client.get(f"/applications/{body['application_id']}").json() == body


def test_correction_invalidates_scores_and_existing_queue(tmp_path):
    with client(tmp_path, ml=ML(), engine=Engine()) as test_client:
        app = upload(test_client).json()
        test_client.post(
            "/queue/run",
            json={
                "application_ids": [app["application_id"]],
                "capacity": 8,
                "policy": {"name": "FIFO"},
            },
        )
        app = test_client.get(f"/applications/{app['application_id']}").json()
        corrected = test_client.patch(
            f"/applications/{app['application_id']}/observations",
            json={
                "expected_revision": app["revision"],
                "actor": "reviewer",
                "values": {"capacity_mw": 14},
            },
        ).json()
        assert corrected["prediction"] is None
        assert corrected["queue_run_id"] is None
        assert corrected["status"] == "READY"
        assert test_client.get("/queue").status_code == 409


class InvalidML:
    async def predict(self, project):
        return {"withdrawal_probability_12m": 3, "decision_distribution": [1]}


def test_invalid_injected_ml_is_distinguished_from_unavailability(tmp_path):
    with client(tmp_path, ml=InvalidML(), engine=Engine()) as test_client:
        response = upload(test_client)
        assert response.status_code == 502
        assert response.json()["code"] == "ML_INVALID_RESPONSE"


class SnapshotEngine(Engine):
    async def simulate(self, config):
        assert len(config.projects) == 1
        assert config.projects[0].project_features.capacity_mw == 12
        return SimulationResult(metrics={"reviewed": 1})


def test_simulation_receives_canonical_application_snapshots(tmp_path):
    with client(tmp_path, ml=ML(), engine=SnapshotEngine()) as test_client:
        application = upload(test_client).json()
        response = test_client.post(
            "/simulation/run", json={"application_ids": [application["application_id"]]}
        )
        assert response.status_code == 201, response.text


def test_multiple_document_application_preserves_both_sources(tmp_path):
    with client(tmp_path) as test_client:
        response = test_client.post(
            "/applications/extract",
            files=[
                ("files", ("form.pdf", b"%PDF-1.7\nform", "application/pdf")),
                ("files", ("report.pdf", b"%PDF-1.7\nreport", "application/pdf")),
            ],
        )
        assert response.status_code == 201
        assert len(response.json()["documents"]) == 2
        assert len(response.json()["parsed_documents"]) == 2


class FailedParser:
    async def parse(self, document_id, path):
        from cq_backend.errors import BackendError

        raise BackendError("PARSE_FAILED", "Unable to parse PDF", 422)


def test_parsing_failure_is_persisted_with_a_retrievable_application_id(tmp_path):
    with TestClient(
        create_app(
            Settings(data_dir=tmp_path), parser=FailedParser(), extractor=Extractor()
        )
    ) as test_client:
        response = upload(test_client)
        assert response.status_code == 422
        application = test_client.get(
            f"/applications/{response.json()['application_id']}"
        ).json()
        assert application["status"] == "FAILED"
        assert application["error"] == "PARSE_FAILED"


def test_initial_persistence_failure_cleans_up_documents(tmp_path, monkeypatch):
    from cq_backend.storage.zova import ZovaStorage

    def fail(*args):
        raise OSError("disk failure")

    monkeypatch.setattr(ZovaStorage, "_save_application", fail)
    with client(tmp_path) as test_client:
        response = upload(test_client)
        assert response.status_code == 503
        assert response.json()["code"] == "PERSISTENCE_FAILURE"
        assert test_client.get("/applications").json() == []
        assert list((tmp_path / "documents").iterdir()) == []


class HeatPumpExtractor(Extractor):
    async def extract(self, documents):
        result = await super().extract(documents)
        result[0].value = "heat_pump"
        return result


def test_heat_pump_returns_out_of_domain_without_ml_prediction(tmp_path):
    with TestClient(
        create_app(
            Settings(data_dir=tmp_path),
            parser=Parser(),
            extractor=HeatPumpExtractor(),
            ml=BrokenML(),
            queue_engine=Engine(),
        )
    ) as test_client:
        response = upload(test_client)
        assert response.status_code == 201
        app = response.json()
        assert app["readiness"]["domain_status"] == "OUT_OF_DOMAIN"
        assert app["prediction"] is None


class FailedEffortEngine(Engine):
    async def effort(self, application):
        from cq_backend.errors import BackendError

        raise BackendError("QUEUE_ENGINE_UNAVAILABLE", "Queue engine unavailable")


def test_queue_failure_does_not_persist_partial_prediction_or_carbon(tmp_path):
    with client(tmp_path, ml=ML(), engine=FailedEffortEngine()) as test_client:
        response = upload(test_client)
        assert response.status_code == 503
        app = test_client.get(
            f"/applications/{response.json()['application_id']}"
        ).json()
        assert app["status"] == "READY"
        assert app["prediction"] is None
        assert app["carbon"] is None


def test_interrupted_processing_is_marked_failed_on_restart(tmp_path):
    import asyncio

    from cq_backend.domain.application import Application, ProcessingStatus
    from cq_backend.storage.zova import ZovaStorage

    async def write_interrupted():
        storage = ZovaStorage(tmp_path / "carbonqueue.zova")
        await storage.open()
        try:
            application = Application(status=ProcessingStatus.EXTRACTING)
            await storage.save_application(application, expected_revision=0)
            return application.application_id
        finally:
            await storage.close()

    application_id = asyncio.run(write_interrupted())
    with client(tmp_path) as test_client:
        app = test_client.get(f"/applications/{application_id}").json()
        assert app["status"] == "FAILED"
        assert app["error"] == "PROCESSING_INTERRUPTED"
