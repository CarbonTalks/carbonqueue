from typing import Protocol

import httpx
from pydantic import ValidationError

from cq_backend.domain.application import (
    Application,
    CarbonEstimate,
    CarbonScenario,
    EffortEstimate,
)
from cq_backend.domain.queue import (
    QueuePolicy,
    QueueResult,
    SimulationInput,
    SimulationResult,
)
from cq_backend.errors import BackendError


class QueueEngine(Protocol):
    async def carbon(
        self, project: Application, scenario: CarbonScenario
    ) -> CarbonEstimate: ...
    async def effort(self, project: Application) -> EffortEstimate: ...
    async def schedule(
        self, projects: list[Application], policy: QueuePolicy, capacity: float
    ) -> QueueResult: ...
    async def simulate(self, config: SimulationInput) -> SimulationResult: ...


class HTTPQueueEngine:
    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url.rstrip("/")

    async def _post(self, path: str, payload: dict, schema):
        try:
            response = await self.client.post(self.base_url + path, json=payload)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise BackendError(
                "QUEUE_ENGINE_UNAVAILABLE", "Queue engine unavailable"
            ) from error
        try:
            return schema.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            raise BackendError(
                "QUEUE_INVALID_RESPONSE",
                "Queue engine returned an invalid response",
                502,
            ) from error

    async def carbon(
        self, project: Application, scenario: CarbonScenario
    ) -> CarbonEstimate:
        return await self._post(
            "/carbon",
            {
                "project": project.model_dump(mode="json"),
                "scenario": scenario.model_dump(mode="json"),
            },
            CarbonEstimate,
        )

    async def effort(self, project: Application) -> EffortEstimate:
        return await self._post(
            "/effort", {"project": project.model_dump(mode="json")}, EffortEstimate
        )

    async def schedule(
        self, projects: list[Application], policy: QueuePolicy, capacity: float
    ) -> QueueResult:
        return await self._post(
            "/schedule",
            {
                "projects": [project.model_dump(mode="json") for project in projects],
                "policy": policy.model_dump(mode="json"),
                "capacity": capacity,
            },
            QueueResult,
        )

    async def simulate(self, config: SimulationInput) -> SimulationResult:
        return await self._post(
            "/simulate", config.model_dump(mode="json"), SimulationResult
        )
