import asyncio
import json
import math

from litestar import get, post
from litestar.di import NamedDependency
from litestar.params import FromPath

from cq_backend.domain.queue import (
    SimulationConfig,
    SimulationResult,
    SimulationRunRequest,
)
from cq_backend.errors import BackendError
from cq_backend.services.orchestration import OrchestrationService


@post("/simulation/run")
async def run_simulation(
    data: SimulationRunRequest,
    service: NamedDependency[OrchestrationService],
) -> SimulationResult | dict:
    if data.year is not None:
        return await load_historical_simulation(data.year, data.policy, service)
    return await service.run_simulation(
        SimulationConfig(
            application_ids=data.application_ids, parameters=data.parameters
        )
    )


@get("/simulation/{simulation_id:str}")
async def get_simulation(
    simulation_id: FromPath[str], service: NamedDependency[OrchestrationService]
) -> SimulationResult:
    return SimulationResult.model_validate_json(
        await service.storage.get_output("simulation", simulation_id)
    )


@get("/simulation/historical/{year:int}/{policy:str}")
async def get_historical_simulation(
    year: FromPath[int],
    policy: FromPath[str],
    service: NamedDependency[OrchestrationService],
) -> dict:
    return await load_historical_simulation(year, policy, service)


async def load_historical_simulation(
    year: int, policy: str, service: OrchestrationService
) -> dict:
    """Serve cq-sim's prepared results without predicting uploaded outcomes."""
    if not 2019 <= year <= 2023 or policy not in {
        "fifo",
        "carbon",
        "carbon_withdrawal",
        "carbon_withdrawal_effort",
        "carbonqueue",
    }:
        raise BackendError(
            "INVALID_SIMULATION", "Unknown historical year or policy", 400
        )
    directory = service.settings.simulation_results_dir
    if directory is None:
        raise BackendError(
            "SIMULATION_UNAVAILABLE", "Configure CQ_SIMULATION_RESULTS_DIR"
        )
    try:
        contents = await asyncio.to_thread(
            (directory / f"{year}-{policy}.json").read_text, encoding="utf-8"
        )
    except FileNotFoundError as error:
        raise BackendError("NOT_FOUND", "Historical result not found", 404) from error
    except OSError as error:
        raise BackendError(
            "SIMULATION_UNAVAILABLE", "Historical results unavailable"
        ) from error
    try:
        result = json.loads(
            contents,
            parse_constant=reject_nonfinite,
            parse_float=finite_float,
        )
        if (
            not isinstance(result, dict)
            or result.get("year") != year
            or result.get("policy") != policy
        ):
            raise ValueError("Historical result identity mismatch")
        return result
    except ValueError as error:
        raise BackendError(
            "SIMULATION_INVALID_RESULT", "Invalid historical result", 502
        ) from error


def reject_nonfinite(value: str):
    raise ValueError(f"Non-finite JSON number: {value}")


def finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Non-finite JSON number")
    return number
