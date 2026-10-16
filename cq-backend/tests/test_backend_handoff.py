import json

import pytest
from litestar.testing import TestClient
from pydantic import ValidationError
from test_api import ML, Extractor, Parser, upload
from test_live_queue import snapshot

from cq_backend.app import create_app
from cq_backend.config import Settings
from cq_backend.domain.application import (
    CarbonEstimate,
    EffortEstimate,
    ProjectFeatures,
)
from cq_backend.domain.queue import QueueEntry, QueueResult


def test_daily_carbon_bands_and_explicit_unscored_state():
    carbon = CarbonEstimate(
        daily_tco2={"low": 1, "central": 2, "high": 3},
        methodology_reference="cq-sim/assumptions.toml",
    )
    assert carbon.tonnes_co2e is None
    assert carbon.daily_tco2.central == 2
    unscored = CarbonEstimate(
        unscored_reason="Storage has no generation carbon estimate",
        methodology_reference="cq-sim/assumptions.toml",
    )
    assert unscored.daily_tco2 is None
    with pytest.raises(ValidationError):
        CarbonEstimate(methodology_reference="missing estimate and reason")
    with pytest.raises(ValidationError):
        CarbonEstimate(
            daily_tco2={"low": 3, "central": 2, "high": 1},
            methodology_reference="bad bands",
        )


class DailyEngine:
    async def carbon(self, application, scenario):
        return CarbonEstimate(
            unscored_reason="Storage is unscored",
            methodology_reference="assumptions.toml",
        )

    async def effort(self, application):
        return EffortEstimate(reviewer_hours=12)

    async def schedule(self, applications, policy, capacity):
        return QueueResult(
            entries=[
                QueueEntry(
                    application_id=a.application_id,
                    position=i + 1,
                    lane="unscored",
                    reason="Storage review allocation",
                    planned_week=1,
                )
                for i, a in enumerate(applications)
            ]
        )


def test_correct_then_rerun_preserves_queue_reason_and_unscored_carbon(tmp_path):
    with TestClient(
        create_app(
            Settings(data_dir=tmp_path),
            parser=Parser(),
            extractor=Extractor(),
            ml=ML(),
            queue_engine=DailyEngine(),
        )
    ) as client:
        app = upload(client).json()
        payload = {
            "application_ids": [app["application_id"]],
            "capacity": 40,
            "policy": {"name": "carbonqueue"},
        }
        assert client.post("/queue/run", json=payload).status_code == 201
        current = client.get(f"/applications/{app['application_id']}").json()
        corrected = client.patch(
            f"/applications/{app['application_id']}/observations",
            json={
                "expected_revision": current["revision"],
                "actor": "Ata",
                "values": {"capacity_mw": 40, "has_storage": True},
            },
        )
        assert corrected.status_code == 200, corrected.text
        assert client.get("/queue").status_code == 409
        rerun = client.post("/queue/run", json=payload)
        assert rerun.status_code == 201, rerun.text
        assert client.get("/queue").json() == rerun.json()
        assert rerun.json()["entries"][0]["reason"] == "Storage review allocation"
        assert (
            client.get(f"/applications/{app['application_id']}").json()["carbon"][
                "tonnes_co2e"
            ]
            is None
        )


def test_cors_preflight_allows_only_configured_dashboard(tmp_path):
    with TestClient(
        create_app(Settings(data_dir=tmp_path, cors_origins=("http://localhost:5173",)))
    ) as client:
        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "content-type",
        }
        response = client.options("/applications/id/observations", headers=headers)
        assert response.headers["access-control-allow-origin"] == headers["Origin"]
        response = client.get(
            "/queue/live", headers={"Origin": "https://untrusted.test"}
        )
        assert "access-control-allow-origin" not in response.headers


def test_live_queue_preserves_storage_and_drops_unrecognized_dashboard_fields(tmp_path):
    data = snapshot()
    data["files"][0]["realization_probability"] = 0.99
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        response = client.post("/queue/live/import", json=data)
        assert response.status_code == 201, response.text
        record = response.json()["files"][0]
        assert "realization_probability" not in record
        assert record["p_withdraw_12m"] == 0.0357
        app = client.get(f"/applications/{record['application_id']}").json()
        assert app["source_values"]["has_storage"] is True


def test_storage_component_and_category_mapping_are_explicit():
    features = ProjectFeatures(technology="battery", capacity_mw=52, has_storage=True)
    assert features.simulation_category == "storage"
    assert features.has_storage is True
    assert (
        ProjectFeatures(technology="hydro", capacity_mw=5).simulation_category
        == "other_renewable"
    )


def test_historical_results_served_without_engine_or_model(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    data = {
        "year": 2023,
        "policy": "carbonqueue",
        "wait_days": {"all": {"median": 88}},
        "carbon_gain_tco2_vs_fifo": {"alpha_0.5": {"central": 44689.3}},
    }
    (results / "2023-carbonqueue.json").write_text(json.dumps(data))
    with TestClient(
        create_app(
            Settings(data_dir=tmp_path / "state", simulation_results_dir=results)
        )
    ) as client:
        response = client.get("/simulation/historical/2023/carbonqueue")
        assert response.status_code == 200, response.text
        assert response.json() == data
        assert client.get("/simulation/historical/2023/fifo").status_code == 404
        assert client.get("/simulation/historical/2023/unknown").status_code == 400
        data["year"] = 2022
        (results / "2023-carbonqueue.json").write_text(json.dumps(data))
        assert client.get("/simulation/historical/2023/carbonqueue").status_code == 502


def test_historical_run_uses_prepared_results_without_engine(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    data = {"year": 2023, "policy": "fifo", "wait_days": {"all": {"median": 82}}}
    (results / "2023-fifo.json").write_text(json.dumps(data))
    with TestClient(
        create_app(
            Settings(data_dir=tmp_path / "state", simulation_results_dir=results)
        )
    ) as client:
        response = client.post("/simulation/run", json={"year": 2023, "policy": "fifo"})
        assert response.status_code == 201, response.text
        assert response.json() == data


def test_handoff_settings_loaded_from_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(
        "CQ_CORS_ORIGINS", "http://localhost:5173, https://demo.example.org "
    )
    monkeypatch.setenv("CQ_SIMULATION_RESULTS_DIR", str(tmp_path / "results"))
    settings = Settings.from_env()
    assert settings.cors_origins == (
        "http://localhost:5173",
        "https://demo.example.org",
    )
    assert settings.simulation_results_dir == tmp_path / "results"


def test_daily_bands_have_exactly_one_representation():
    with pytest.raises(ValidationError):
        CarbonEstimate(
            tonnes_co2e=2, unscored_reason="unknown", methodology_reference="rules"
        )
    with pytest.raises(ValidationError):
        CarbonEstimate(
            daily_tco2={"low": -1, "central": 0, "high": 1},
            methodology_reference="rules",
        )


@pytest.mark.parametrize(
    "contents",
    [
        '{"year":2023,"policy":"fifo","metric":NaN}',
        '{"year":2023,"policy":"fifo","metric":1e400}',
    ],
)
def test_historical_results_reject_nonfinite_numbers(tmp_path, contents):
    (tmp_path / "2023-fifo.json").write_text(contents)
    with TestClient(
        create_app(
            Settings(data_dir=tmp_path / "state", simulation_results_dir=tmp_path)
        )
    ) as client:
        assert client.get("/simulation/historical/2023/fifo").status_code == 502


def test_historical_and_uploaded_application_requests_cannot_be_mixed(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        response = client.post(
            "/simulation/run",
            json={"year": 2023, "policy": "fifo", "application_ids": []},
        )
        assert response.status_code == 400
