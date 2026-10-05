from typing import Protocol

from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits

from cq_backend.agent.prompts import EXTRACTION_INSTRUCTIONS
from cq_backend.domain.application import (
    ExtractedField,
    ExtractionResult,
    ParsedDocument,
)
from cq_backend.errors import BackendError


class Extractor(Protocol):
    async def extract(
        self, documents: list[ParsedDocument]
    ) -> list[ExtractedField]: ...


class ExtractionAgent:
    def __init__(self, model):
        self.agent = Agent(
            model, output_type=ExtractionResult, instructions=EXTRACTION_INSTRUCTIONS
        )

    async def extract(self, documents: list[ParsedDocument]) -> list[ExtractedField]:
        prompt = (
            "Planning document data:\n["
            + ",".join(document.model_dump_json() for document in documents)
            + "]"
        )
        if len(prompt) > 1_000_000:
            raise BackendError(
                "EXTRACTION_INPUT_LIMIT",
                "Parsed documents exceed the agent input limit",
                413,
            )
        try:
            result = await self.agent.run(
                prompt, usage_limits=UsageLimits(request_limit=3)
            )
            return result.output.observations
        except Exception as error:
            raise BackendError(
                "EXTRACTION_FAILED", "Structured document extraction failed", 502
            ) from error
