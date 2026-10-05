from litestar import get, post
from litestar.di import NamedDependency

from cq_backend.domain.queue import QueueRequest, QueueResult
from cq_backend.services.orchestration import OrchestrationService


@post("/queue/run")
async def run_queue(
    data: QueueRequest, service: NamedDependency[OrchestrationService]
) -> QueueResult:
    return await service.run_queue(data)


@get("/queue")
async def get_queue(service: NamedDependency[OrchestrationService]) -> QueueResult:
    return await service.get_queue()
