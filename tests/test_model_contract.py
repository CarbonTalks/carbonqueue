import asyncio
from datetime import date

import pytest
from litestar.testing import TestClient
from pydantic import ValidationError
from test_api import Engine, Extractor, Parser, upload
from test_reconciliation import field

from cq_backend.agent.reconcile import reconcile
from cq_backend.app import create_app
from cq_backend.config import Settings
from cq_backend.domain.application import Prediction, ProjectFeatures


def test_optional_model_inputs_round_trip_and_validate_dates():
    features = ProjectFeatures(
        technology="battery",
        capacity_mw=52,
        applicant="Example Ltd",
        submission_date="2025-03-01",
    )
    assert features.submission_date == date(2025, 3, 1)
    assert features.model_dump(mode="json")["submission_date"] == "2025-03-01"
    assert ProjectFeatures(technology="solar", capacity_mw=40).applicant is None
    with pytest.raises(ValidationError):
        ProjectFeatures(technology="solar", capacity_mw=40, submission_date="yesterday")


def test_optional_inputs_are_reconciled_and_bad_date_requires_review():
    observations = [
        field("technology", "solar"),
        field("capacity_mw", 40, unit="MW"),
        field("applicant", "Example Ltd"),
        field("submission_date", "2025-03-01"),
    ]
    features, readiness = reconcile(observations)
    assert readiness.ready_for_review
    assert features.applicant == "Example Ltd"
    observations[-1].value = "2025-02-30"
    features, readiness = reconcile(observations)
    assert features is None
    assert "submission_date" in readiness.invalid_fields


@pytest.mark.parametrize(
    "technology, expected",
    [("battery", "IN_DOMAIN"), ("offshore_wind", "OUT_OF_DOMAIN")],
)
def test_requested_technology_scope(technology, expected):
    features, readiness = reconcile(
        [field("technology", technology), field("capacity_mw", 52, unit="MW")]
    )
    assert readiness.domain_status == expected
    assert (features is not None) == (expected == "IN_DOMAIN")


@pytest.mark.parametrize("length", [1, 12, 14])
def test_decision_distribution_requires_thirteen_bins(length):
    with pytest.raises(ValidationError):
        Prediction(
            withdrawal_probability_12m=0.2, decision_distribution=[1 / length] * length
        )


def test_plain_python_model_is_injected_and_runs_off_event_loop(tmp_path):
    def predict(project):
        with pytest.raises(RuntimeError):
            asyncio.get_running_loop()
        assert project.capacity_mw == 12
        return {
            "withdrawal_probability_12m": 0.2,
            "decision_distribution": [0.0] * 12 + [1.0],
        }

    with TestClient(
        create_app(
            Settings(data_dir=tmp_path),
            parser=Parser(),
            extractor=Extractor(),
            ml=predict,
            queue_engine=Engine(),
        )
    ) as client:
        body = upload(client)
        assert body.status_code == 201, body.text
        assert body.json()["status"] == "SCORED"
        assert len(body.json()["prediction"]["decision_distribution"]) == 13


def test_async_python_model_is_injected(tmp_path):
    async def predict(project):
        return Prediction(
            withdrawal_probability_12m=0.1, decision_distribution=[0.0] * 12 + [1.0]
        )

    with TestClient(
        create_app(
            Settings(data_dir=tmp_path),
            parser=Parser(),
            extractor=Extractor(),
            ml=predict,
            queue_engine=Engine(),
        )
    ) as client:
        response = upload(client)
        assert response.status_code == 201, response.text
        assert response.json()["prediction"]["withdrawal_probability_12m"] == 0.1


@pytest.mark.parametrize("invalid_response", [False, True])
def test_local_model_failures_have_safe_distinct_error_codes(
    tmp_path, invalid_response
):
    def predict(project):
        if invalid_response:
            return {"withdrawal_probability_12m": 0.2, "decision_distribution": [1.0]}
        raise ValueError("private model implementation details")

    with TestClient(
        create_app(
            Settings(data_dir=tmp_path),
            parser=Parser(),
            extractor=Extractor(),
            ml=predict,
            queue_engine=Engine(),
        )
    ) as client:
        response = upload(client)
        assert response.status_code == (502 if invalid_response else 503)
        assert response.json()["code"] == (
            "ML_INVALID_RESPONSE" if invalid_response else "ML_UNAVAILABLE"
        )
        assert "private model" not in response.text
