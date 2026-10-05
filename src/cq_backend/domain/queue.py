from pydantic import Field

from cq_backend.domain.application import (
    Application,
    CarbonScenario,
    Contract,
    Value,
    new_id,
)


class QueuePolicy(Contract):
    name: str = Field(min_length=1)
    parameters: dict[str, Value] = Field(default_factory=dict)


class QueueEntry(Contract):
    application_id: str
    position: int = Field(ge=1)
    score: float | None = None


class QueueResult(Contract):
    queue_run_id: str = Field(default_factory=new_id)
    entries: list[QueueEntry]


class QueueRequest(Contract):
    application_ids: list[str]
    policy: QueuePolicy
    capacity: float = Field(gt=0)
    scenario: CarbonScenario = Field(default_factory=CarbonScenario)


class SimulationConfig(Contract):
    application_ids: list[str]
    parameters: dict[str, Value] = Field(default_factory=dict)


class SimulationInput(SimulationConfig):
    projects: list[Application]


class SimulationResult(Contract):
    simulation_id: str = Field(default_factory=new_id)
    metrics: dict[str, float]
    references: list[str] = Field(default_factory=list)
