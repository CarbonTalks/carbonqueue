import asyncio
import inspect
from typing import Protocol

import httpx
from pydantic import ValidationError

from cq_backend.domain.application import Prediction, ProjectFeatures
from cq_backend.errors import BackendError


class MLService(Protocol):
    async def predict(self, project: ProjectFeatures) -> Prediction: ...


class CallableMLService:
    """Adapt a local Python predictor without blocking the request event loop."""

    def __init__(self, predict):
        self.function = predict

    async def predict(self, project: ProjectFeatures) -> Prediction:
        try:
            async with asyncio.timeout(30):
                if inspect.iscoroutinefunction(self.function):
                    result = await self.function(project)
                else:
                    result = await asyncio.to_thread(self.function, project)
                    if inspect.isawaitable(result):
                        result = await result
        except BackendError:
            raise
        except Exception as error:
            raise BackendError("ML_UNAVAILABLE", "ML component unavailable") from error
        try:
            return Prediction.model_validate(result)
        except ValidationError as error:
            raise BackendError(
                "ML_INVALID_RESPONSE",
                "ML component returned an invalid prediction",
                502,
            ) from error


class HTTPMLService:
    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.url = base_url.rstrip("/") + "/predict"

    async def predict(self, project: ProjectFeatures) -> Prediction:
        try:
            response = await self.client.post(
                self.url, json=project.model_dump(mode="json")
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise BackendError("ML_UNAVAILABLE", "ML component unavailable") from error
        try:
            return Prediction.model_validate(response.json())
        except (ValidationError, ValueError) as error:
            raise BackendError(
                "ML_INVALID_RESPONSE",
                "ML component returned an invalid prediction",
                502,
            ) from error
