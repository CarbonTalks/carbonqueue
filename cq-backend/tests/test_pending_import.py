from litestar.testing import TestClient

from cq_backend.app import create_app
from cq_backend.config import Settings


def batch():
    return {
        "source": "REPD demo snapshot",
        "applications": [
            {
                "external_id": "18446",
                "technology": "solar",
                "capacity_mw": 40,
                "project_name": "Hanwell",
                "applicant": "Example Ltd",
                "submission_date": "2025-02-01",
            },
            {
                "external_id": "19786",
                "technology": "solar",
                "capacity_mw": None,
                "project_name": "Arncott",
            },
            {"external_id": "17593", "technology": "battery", "capacity_mw": 52},
        ],
    }


def test_pending_import_is_persisted_and_missing_capacity_is_not_scored(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        response = client.post("/applications/import", json=batch())
        assert response.status_code == 201, response.text
        imported = response.json()
        assert [item["status"] for item in imported] == [
            "READY",
            "NEEDS_REVIEW",
            "READY",
        ]
        assert imported[1]["readiness"]["missing_fields"] == ["capacity_mw"]
        assert imported[1]["project_features"] is None
        assert imported[1]["source_values"]["project_name"] == "Arncott"
        assert imported[0]["project_features"]["submission_date"] == "2025-02-01"
        assert imported[0]["source"] == {
            "name": "REPD demo snapshot",
            "external_id": "18446",
        }
        assert all(
            item["observations"] == [] and item["prediction"] is None
            for item in imported
        )
        assert client.get("/applications/pending").json() == imported
        assert client.get("/applications").json() == imported
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        assert client.get("/applications/pending").json() == imported


def test_reimport_preserves_human_corrections_and_does_not_duplicate(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        imported = client.post("/applications/import", json=batch()).json()
        arncott = imported[1]
        response = client.patch(
            f"/applications/{arncott['application_id']}/observations",
            json={
                "actor": "reviewer",
                "expected_revision": arncott["revision"],
                "values": {"capacity_mw": 20},
            },
        )
        assert response.status_code == 200, response.text
        corrected = response.json()
        assert corrected["status"] == "READY"
        assert corrected["project_features"]["technology"] == "solar"
        assert corrected["project_features"]["capacity_mw"] == 20
        repeated = client.post("/applications/import", json=batch())
        assert repeated.status_code == 201, repeated.text
        assert repeated.json()[1] == corrected
        assert len(client.get("/applications/pending").json()) == 3


def test_changed_snapshot_is_rejected_atomically_without_overwriting(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        original = client.post("/applications/import", json=batch()).json()
        changed = batch()
        changed["applications"].insert(
            0, {"external_id": "new", "technology": "solar", "capacity_mw": 10}
        )
        changed["applications"][1]["capacity_mw"] = 41
        response = client.post("/applications/import", json=changed)
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "IMPORT_CONFLICT"
        assert client.get("/applications/pending").json() == original


def test_duplicate_external_ids_are_rejected_without_partial_import(tmp_path):
    payload = batch()
    payload["applications"].append(payload["applications"][0])
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        response = client.post("/applications/import", json=payload)
        assert response.status_code == 400, response.text
        assert client.get("/applications").json() == []


def test_invalid_import_is_rejected_before_writing(tmp_path):
    payload = batch()
    payload["applications"][1]["capacity_mw"] = -1
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        response = client.post("/applications/import", json=payload)
        assert response.status_code == 400, response.text
        assert client.get("/applications").json() == []
