from litestar.testing import TestClient

from cq_backend.app import create_app
from cq_backend.config import Settings


def snapshot():
    return {
        "as_of": "2026-07-24",
        "emission_factor_tco2_per_mwh": {
            "low": 0.0579,
            "central": 0.13276,
            "high": 0.36537,
        },
        "calibration": {"capacity_hours_per_week": 332.7, "calibration_year": 2023},
        "lane_counts": {"max_wait": 1},
        "files": [
            {
                "app_id": 9897,
                "site_name": "Kilnwood Farm",
                "authority": "Rother",
                "category": "storage",
                "technology": "Battery",
                "generation_mw": None,
                "has_storage": True,
                "submitted": "2021-09-23",
                "wait_days": 1765,
                "position": {"fifo": 2, "carbon": 2, "carbonqueue": 2},
                "planned_week": {"fifo": 1, "carbon": 1, "carbonqueue": 1},
                "lane": "max_wait",
                "reason": "Azami bekleme koruması",
                "daily_tco2": None,
                "effort_hours": 12,
                "p_withdraw_12m": 0.0357,
                "stale": False,
            }
        ],
        "needs_confirmation": [
            {
                "app_id": 4158,
                "site_name": "Langthwaite Farm",
                "authority": "Cumberland",
                "category": "onshore_wind",
                "submitted": "2012-03-30",
                "wait_days": 5229,
                "reason": "Kurumla teyit edilmeli",
            }
        ],
    }


def test_cqsim_snapshot_is_served_by_backend_with_application_links(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        response = client.post("/queue/live/import", json=snapshot())
        assert response.status_code == 201, response.text
        result = response.json()
        assert result["files"][0]["position"] == snapshot()["files"][0]["position"]
        assert result["needs_confirmation"][0]["app_id"] == 4158
        assert result["changed_application_ids"] == []
        app_id = result["files"][0]["application_id"]
        application = client.get(f"/applications/{app_id}").json()
        assert application["source_values"]["technology"] == "battery"
        assert "capacity_mw" in application["readiness"]["missing_fields"]
        assert application["prediction"] is None
        assert client.get("/queue/live").json() == result
        assert len(client.get("/applications/pending").json()) == 2
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        assert client.get("/queue/live").json() == result


def test_corrections_flag_precomputed_snapshot_as_changed(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        result = client.post("/queue/live/import", json=snapshot()).json()
        app_id = result["files"][0]["application_id"]
        client.patch(
            f"/applications/{app_id}/observations",
            json={
                "actor": "reviewer",
                "expected_revision": 1,
                "values": {"capacity_mw": 52},
            },
        )
        assert client.get("/queue/live").json()["changed_application_ids"] == [app_id]
        repeated = client.post("/queue/live/import", json=snapshot())
        assert repeated.status_code == 201
        assert repeated.json()["changed_application_ids"] == [app_id]


def test_duplicate_snapshot_ids_do_not_publish_partial_state(tmp_path):
    payload = snapshot()
    payload["needs_confirmation"][0]["app_id"] = 9897
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        assert client.post("/queue/live/import", json=payload).status_code == 400
        assert client.get("/applications").json() == []
        assert client.get("/queue/live").status_code == 404


def test_missing_authority_in_source_snapshot_is_preserved(tmp_path):
    payload = snapshot()
    payload["files"][0]["authority"] = None
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        response = client.post("/queue/live/import", json=payload)
        assert response.status_code == 201, response.text
        assert response.json()["files"][0]["authority"] is None
