from litestar import get, post
from litestar.di import NamedDependency
from litestar.params import FromPath

from cq_backend.domain.queue import SimulationConfig, SimulationResult
from cq_backend.services.orchestration import OrchestrationService


@post("/simulation/run")
async def run_simulation(
    data: SimulationConfig, service: NamedDependency[OrchestrationService]
) -> SimulationResult:
    return await service.run_simulation(data)


@get("/simulation/{simulation_id:str}")
async def get_simulation(
    simulation_id: FromPath[str], service: NamedDependency[OrchestrationService]
) -> SimulationResult:
    return SimulationResult.model_validate_json(
        await service.storage.get_output("simulation", simulation_id)
    )
