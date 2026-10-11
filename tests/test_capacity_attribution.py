import pytest

from cq_backend.agent.reconcile import reconcile
from cq_backend.domain.application import (
    Evidence,
    ExtractedField,
    ParsedDocument,
    ParsedPage,
)

HISTORICAL = 'Located to the west of the site, planning permission was approved by the Council on 5 September 2014 for the: "Construction of an 8MW solar photovoltaic park complete with all necessary inverters".'
GRID = "The flexible generation asset has an existing 5MW connection which is only being used when the asset runs."


@pytest.mark.parametrize(
    "value, quote, scope",
    [
        (8, HISTORICAL, "neighbouring_project"),
        (5, GRID, "grid_connection"),
        (8, HISTORICAL, "proposed_project"),
        (5, GRID, "proposed_project"),
        (8, "Solar 8 MW", "unknown"),
    ],
)
def test_unrelated_or_unverified_capacity_is_missing_not_a_project_value(
    value, quote, scope
):
    docs = [
        ParsedDocument(
            document_id="doc",
            pages=[ParsedPage(number=1, text="Solar development. " + quote)],
        )
    ]
    observations = [
        ExtractedField(
            field="technology",
            value="solar",
            confidence=0.99,
            evidence=[Evidence(document_id="doc", page=1, quote="Solar development")],
        ),
        ExtractedField(
            field="capacity_mw",
            value=value,
            confidence=0.99,
            unit="MW",
            capacity_scope=scope,
            evidence=[Evidence(document_id="doc", page=1, quote=quote)],
        ),
    ]
    features, readiness = reconcile(observations, documents=docs)
    assert features is None
    assert readiness.missing_fields == ["capacity_mw"]
    assert not readiness.conflicts
    assert not readiness.ready_for_review
    assert observations[1].value == value  # Keep rejected observations for audit.
    corrected, readiness = reconcile(
        observations, documents=docs, overrides={"capacity_mw": 20}
    )
    assert readiness.ready_for_review
    assert corrected.capacity_mw == 20


def test_proposed_capacity_survives_unrelated_observations():
    docs = [
        ParsedDocument(
            document_id="doc",
            pages=[
                ParsedPage(
                    number=1,
                    text="The proposed solar farm has a capacity of approximately 40MW. "
                    + GRID,
                )
            ],
        )
    ]
    evidence = [
        Evidence(
            document_id="doc",
            page=1,
            quote="The proposed solar farm has a capacity of approximately 40MW.",
        )
    ]
    observations = [
        ExtractedField(
            field="technology", value="solar", confidence=0.99, evidence=evidence
        ),
        ExtractedField(
            field="capacity_mw",
            value=40,
            confidence=0.99,
            unit="MW",
            capacity_scope="proposed_project",
            evidence=evidence,
        ),
        ExtractedField(
            field="capacity_mw",
            value=5,
            confidence=0.99,
            unit="MW",
            capacity_scope="grid_connection",
            evidence=[Evidence(document_id="doc", page=1, quote=GRID)],
        ),
    ]
    features, readiness = reconcile(observations, documents=docs)
    assert readiness.ready_for_review
    assert features.capacity_mw == 40


def test_legacy_capacity_without_scope_requires_review():
    observation = ExtractedField(
        field="capacity_mw",
        value=8,
        unit="MW",
        confidence=0.99,
        evidence=[Evidence(document_id="doc", page=1, quote="8 MW")],
    )
    _, readiness = reconcile([observation])
    assert "capacity_mw" in readiness.missing_fields


def test_capacity_value_must_appear_in_its_quote():
    observation = ExtractedField(
        field="capacity_mw",
        value=8,
        unit="MW",
        confidence=0.99,
        capacity_scope="proposed_project",
        evidence=[
            Evidence(
                document_id="doc",
                page=1,
                quote="The proposed solar farm has no stated capacity.",
            )
        ],
    )
    _, readiness = reconcile([observation])
    assert "capacity_mw" in readiness.missing_fields


def test_cropping_old_permission_quote_does_not_hide_source_context():
    quote = "Construction of an 8MW solar photovoltaic park"
    observation = ExtractedField(
        field="capacity_mw",
        value=8,
        unit="MW",
        confidence=0.99,
        capacity_scope="proposed_project",
        evidence=[Evidence(document_id="doc", page=8, quote=quote)],
    )
    docs = [
        ParsedDocument(document_id="doc", pages=[ParsedPage(number=8, text=HISTORICAL)])
    ]
    _, readiness = reconcile([observation], documents=docs)
    assert "capacity_mw" in readiness.missing_fields
