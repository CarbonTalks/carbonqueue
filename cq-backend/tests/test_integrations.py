import httpx
import pytest

from cq_backend.domain.application import Application, CarbonScenario, ProjectFeatures
from cq_backend.errors import BackendError
from cq_backend.integrations.ml import HTTPMLService
from cq_backend.integrations.queue_engine import HTTPQueueEngine


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"withdrawal_probability_12m": 2, "decision_distribution": [0.0] * 12 + [1]},
        {
            "withdrawal_probability_12m": 0.5,
            "decision_distribution": [-1, 2] + [0.0] * 11,
        },
        {
            "withdrawal_probability_12m": 0.5,
            "decision_distribution": [0.3, 0.3] + [0.0] * 11,
        },
        {},
    ],
)
async def test_invalid_ml_response_is_explicit(payload):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    ) as client:
        with pytest.raises(BackendError) as error:
            await HTTPMLService(client, "http://ml.test").predict(
                ProjectFeatures(technology="solar", capacity_mw=12)
            )
        assert error.value.code == "ML_INVALID_RESPONSE"


@pytest.mark.asyncio
async def test_ml_adapter_sends_features_to_external_predict_boundary():
    import json

    def respond(request):
        assert request.url.path == "/predict"
        assert json.loads(request.content)["capacity_mw"] == 12
        return httpx.Response(
            200,
            json={
                "withdrawal_probability_12m": 0.2,
                "decision_distribution": [0.4] + [0.0] * 11 + [0.6],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await HTTPMLService(client, "http://ml.test").predict(
            ProjectFeatures(technology="solar", capacity_mw=12)
        )
        assert result.withdrawal_probability_12m == 0.2


@pytest.mark.asyncio
async def test_unavailable_queue_engine_does_not_fabricate_carbon():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(503))
    ) as client:
        with pytest.raises(BackendError) as error:
            await HTTPQueueEngine(client, "http://queue.test").carbon(
                Application(), CarbonScenario()
            )
        assert error.value.code == "QUEUE_ENGINE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_invalid_effort_response_is_rejected():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"reviewer_hours": -2})
        )
    ) as client:
        with pytest.raises(BackendError) as error:
            await HTTPQueueEngine(client, "http://queue.test").effort(Application())
        assert error.value.code == "QUEUE_INVALID_RESPONSE"
