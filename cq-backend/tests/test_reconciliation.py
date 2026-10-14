import pytest
from pydantic import ValidationError

from cq_backend.agent.reconcile import reconcile
from cq_backend.domain.application import (
    Evidence,
    ExtractedField,
    ParsedDocument,
    ParsedPage,
)


def field(name, value, confidence=0.99, unit=None, evidence=True):
    return ExtractedField(
        field=name,
        capacity_scope="proposed_project" if name == "capacity_mw" else "unknown",
        value=value,
        confidence=confidence,
        unit=unit,
        evidence=[
            Evidence(
                document_id="doc",
                page=1,
                quote=f"Solar {value} MW" if name == "capacity_mw" else "Solar 12 MW",
            )
        ]
        if evidence
        else [],
    )


def test_clean_observations_and_duplicates_produce_canonical_features():
    observations = [field("technology", "solar"), field("capacity_mw", 12, unit="MW")]
    features, readiness = reconcile(observations + observations)
    assert readiness.ready_for_review
    assert features.capacity_mw == 12
    assert features.technology == "solar"


@pytest.mark.parametrize(
    "observation, issue",
    [
        (field("capacity_mw", 12, confidence=0.3, unit="MW"), "low_confidence_fields"),
        (field("capacity_mw", 12, unit="kW"), "invalid_fields"),
        (field("capacity_mw", -12, unit="MW"), "invalid_fields"),
        (field("capacity_mw", True, unit="MW"), "invalid_fields"),
        (field("capacity_mw", 12, unit="MW", evidence=False), "unsupported_fields"),
    ],
)
def test_unreliable_observations_block_readiness(observation, issue):
    features, readiness = reconcile([field("technology", "solar"), observation])
    assert not readiness.ready_for_review
    assert features is None
    assert "capacity_mw" in getattr(readiness, issue)


def test_conflicting_values_are_never_silently_selected():
    observations = [
        field("technology", "solar"),
        field("capacity_mw", 12, unit="MW"),
        field("capacity_mw", 12.6, unit="MW"),
    ]
    features, readiness = reconcile(observations)
    assert features is None
    assert readiness.conflicts[0].field == "capacity_mw"
    assert len(readiness.conflicts[0].observations) == 2


def test_missing_and_out_of_domain_are_explicit():
    _, missing = reconcile([field("technology", "solar")])
    assert missing.missing_fields == ["capacity_mw"]
    features, unsupported = reconcile(
        [field("technology", "heat_pump"), field("capacity_mw", 12, unit="MW")]
    )
    assert features is None
    assert unsupported.domain_status == "OUT_OF_DOMAIN"
    assert "Historical model unavailable" in unsupported.message


def test_confidence_and_page_numbers_are_validated():
    with pytest.raises(ValidationError):
        field("technology", "solar", confidence=1.1)
    with pytest.raises(ValidationError):
        Evidence(document_id="doc", page=0, quote="quote")


def test_evidence_must_match_the_supplied_document_and_page():
    docs = [
        ParsedDocument(
            document_id="doc", pages=[ParsedPage(number=1, text="Other text")]
        )
    ]
    _, readiness = reconcile(
        [field("technology", "solar"), field("capacity_mw", 12, unit="MW")],
        documents=docs,
    )
    assert set(readiness.unsupported_fields) == {"technology", "capacity_mw"}


def test_correction_overrides_conflict_without_erasing_observations():
    observations = [
        field("technology", "solar"),
        field("capacity_mw", 12, unit="MW"),
        field("capacity_mw", 12.6, unit="MW"),
    ]
    features, readiness = reconcile(observations, overrides={"capacity_mw": 12.6})
    assert readiness.ready_for_review
    assert features.capacity_mw == 12.6
    assert len(observations) == 3
