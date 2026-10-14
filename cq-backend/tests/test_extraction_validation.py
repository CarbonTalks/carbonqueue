import pytest
from pydantic_ai.messages import ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import FunctionModel

from cq_backend.agent.extract import ExtractionAgent
from cq_backend.agent.reconcile import reconcile
from cq_backend.domain.application import ParsedDocument, ParsedPage
from cq_backend.errors import BackendError


def documents():
    return [
        ParsedDocument(
            document_id="doc",
            pages=[
                ParsedPage(
                    number=1,
                    text="This proposed solar farm has a capacity of 40MW.\nApplicant: Example Ltd.",
                )
            ],
        )
    ]


def capacity():
    return {
        "field": "capacity_mw",
        "value": 40,
        "confidence": 0.99,
        "unit": "MW",
        "capacity_scope": "proposed_project",
        "evidence": [
            {
                "document_id": "doc",
                "page": 1,
                "quote": "This proposed solar farm has a capacity of 40MW.",
            }
        ],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "problem",
    [
        "metadata",
        "quote_case",
        "escaped_newline",
        "wrong_page",
        "missing_quote",
        "invalid_date",
    ],
)
async def test_invalid_output_is_retried_instead_of_returned(problem):
    calls = []

    def respond(messages, info):
        calls.append(messages)
        observation = capacity()
        if len(calls) == 1:
            if problem == "metadata":
                observation.pop("unit")
                observation.pop("capacity_scope")
            elif problem == "quote_case":
                observation["evidence"][0]["quote"] = (
                    "this proposed solar farm has a capacity of 40MW."
                )
            elif problem == "escaped_newline":
                observation["evidence"][0]["quote"] += "\\nApplicant: Example Ltd."
            elif problem == "wrong_page":
                observation["evidence"][0]["page"] = 2
            elif problem == "missing_quote":
                observation["evidence"][0]["quote"] = None
            else:
                observation.update(
                    field="submission_date", value="2025-09-05}]}],observations:[{"
                )
        return ModelResponse(
            parts=[
                ToolCallPart(info.output_tools[0].name, {"observations": [observation]})
            ]
        )

    observations = await ExtractionAgent(FunctionModel(respond)).extract(documents())
    assert len(calls) == 2
    assert observations[0].value == 40
    assert observations[0].unit == "MW"
    assert observations[0].capacity_scope == "proposed_project"


@pytest.mark.asyncio
async def test_persistently_bad_evidence_fails_with_bounded_requests():
    calls = []

    def respond(messages, info):
        calls.append(messages)
        observation = capacity()
        observation["evidence"][0]["quote"] = "A sentence absent from the documents."
        return ModelResponse(
            parts=[
                ToolCallPart(info.output_tools[0].name, {"observations": [observation]})
            ]
        )

    with pytest.raises(BackendError) as error:
        await ExtractionAgent(FunctionModel(respond)).extract(documents())
    assert error.value.code == "EXTRACTION_FAILED"
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_prompt_uses_readable_page_text_not_json_escaped_strings():
    def respond(messages, info):
        prompt = next(
            part.content
            for message in messages
            for part in message.parts
            if isinstance(part, UserPromptPart)
        )
        assert "40MW.\nApplicant: Example Ltd." in prompt
        assert "40MW.\\nApplicant" not in prompt
        return ModelResponse(
            parts=[
                ToolCallPart(info.output_tools[0].name, {"observations": [capacity()]})
            ]
        )

    await ExtractionAgent(FunctionModel(respond)).extract(documents())


@pytest.mark.asyncio
async def test_intentionally_missing_capacity_does_not_trigger_retry_or_guess():
    calls = []
    docs = [
        ParsedDocument(
            document_id="doc",
            pages=[
                ParsedPage(
                    number=1,
                    text="Solar development. Existing 5MW connection; neighbouring 8MW permission.",
                )
            ],
        )
    ]

    def respond(messages, info):
        calls.append(messages)
        return ModelResponse(
            parts=[
                ToolCallPart(
                    info.output_tools[0].name,
                    {
                        "observations": [
                            {
                                "field": "technology",
                                "value": "solar",
                                "confidence": 0.99,
                                "unit": None,
                                "capacity_scope": "unknown",
                                "evidence": [
                                    {
                                        "document_id": "doc",
                                        "page": 1,
                                        "quote": "Solar development.",
                                    }
                                ],
                            }
                        ]
                    },
                )
            ]
        )

    observations = await ExtractionAgent(FunctionModel(respond)).extract(docs)
    features, readiness = reconcile(observations, documents=docs)
    assert features is None
    assert readiness.missing_fields == ["capacity_mw"]
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_retry_supplies_the_actual_page_for_a_mismatched_quote():
    calls = []

    def respond(messages, info):
        calls.append(messages)
        observation = capacity()
        if len(calls) == 1:
            observation["evidence"][0]["quote"] = "Paraphrased location and capacity."
        else:
            from pydantic_ai.messages import RetryPromptPart

            feedback = next(
                part.content
                for part in messages[-1].parts
                if isinstance(part, RetryPromptPart)
            )
            assert "SOURCE DOCUMENT doc PAGE 1" in feedback
            assert documents()[0].pages[0].text in feedback
        return ModelResponse(
            parts=[
                ToolCallPart(info.output_tools[0].name, {"observations": [observation]})
            ]
        )

    await ExtractionAgent(FunctionModel(respond)).extract(documents())
    assert len(calls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("label", ["Signature date", "Cover letter date"])
async def test_document_dates_are_not_accepted_as_submission_dates(label):
    docs = [
        ParsedDocument(
            document_id="doc", pages=[ParsedPage(number=1, text=f"{label}: 2025-09-05")]
        )
    ]
    calls = []

    def respond(messages, info):
        calls.append(messages)
        observations = (
            []
            if len(calls) > 1
            else [
                {
                    "field": "submission_date",
                    "value": "2025-09-05",
                    "confidence": 0.99,
                    "unit": None,
                    "capacity_scope": "unknown",
                    "evidence": [
                        {"document_id": "doc", "page": 1, "quote": "2025-09-05"}
                    ],
                }
            ]
        )
        return ModelResponse(
            parts=[
                ToolCallPart(info.output_tools[0].name, {"observations": observations})
            ]
        )

    result = await ExtractionAgent(FunctionModel(respond)).extract(docs)
    assert result == []
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_explicit_submission_date_is_preserved():
    docs = [
        ParsedDocument(
            document_id="doc",
            pages=[ParsedPage(number=1, text="Submission date: 2025-09-05")],
        )
    ]

    def respond(messages, info):
        return ModelResponse(
            parts=[
                ToolCallPart(
                    info.output_tools[0].name,
                    {
                        "observations": [
                            {
                                "field": "submission_date",
                                "value": "2025-09-05",
                                "confidence": 0.99,
                                "unit": None,
                                "capacity_scope": "unknown",
                                "evidence": [
                                    {
                                        "document_id": "doc",
                                        "page": 1,
                                        "quote": "2025-09-05",
                                    }
                                ],
                            }
                        ]
                    },
                )
            ]
        )

    result = await ExtractionAgent(FunctionModel(respond)).extract(docs)
    assert result[0].value == "2025-09-05"
