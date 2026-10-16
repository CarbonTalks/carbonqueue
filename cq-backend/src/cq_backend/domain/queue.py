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
    lane: str | None = None
    reason: str | None = None
    planned_week: int | None = Field(default=None, ge=1)


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


class SimulationRunRequest(Contract):
    application_ids: list[str] | None = None
    parameters: dict[str, Value] = Field(default_factory=dict)
    year: int | None = Field(default=None, ge=2019, le=2023)
    policy: str | None = None

    def model_post_init(self, context: object) -> None:
        historical = self.year is not None or self.policy is not None
        if historical:
            if (
                self.year is None
                or self.policy is None
                or self.application_ids is not None
                or self.parameters
            ):
                raise ValueError("Historical requests require only year and policy")
        elif self.application_ids is None:
            raise ValueError("Provide historical year/policy or legacy application_ids")
