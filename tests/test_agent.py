import pytest
from pydantic_ai.models.test import TestModel

from cq_backend.agent.extract import ExtractionAgent
from cq_backend.domain.application import ParsedDocument, ParsedPage


@pytest.mark.asyncio
async def test_pydanticai_extracts_structured_observations_from_parsed_pages():
    model = TestModel(
        custom_output_args={
            "observations": [
                {
                    "field": "technology",
                    "value": "solar",
                    "confidence": 0.99,
                    "evidence": [
                        {"document_id": "doc", "page": 1, "quote": "Solar 12 MW"}
                    ],
                }
            ]
        }
    )
    agent = ExtractionAgent(model)
    result = await agent.extract(
        [
            ParsedDocument(
                document_id="doc", pages=[ParsedPage(number=1, text="Solar 12 MW")]
            )
        ]
    )
    assert result[0].value == "solar"
    assert result[0].evidence[0].document_id == "doc"
