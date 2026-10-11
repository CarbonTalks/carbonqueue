import re
from collections import defaultdict
from datetime import date

from cq_backend.domain.application import (
    SUPPORTED_TECHNOLOGIES,
    Conflict,
    ExtractedField,
    ParsedDocument,
    ProjectFeatures,
    ReadinessResult,
    Value,
)

REQUIRED_FIELDS = ("technology", "capacity_mw")
MIN_CONFIDENCE = 0.8


def is_proposed_capacity(
    observation: ExtractedField, documents: list[ParsedDocument] | None
) -> bool:
    if observation.capacity_scope != "proposed_project":
        return False
    if type(observation.value) not in (int, float):
        return True  # The ordinary value check reports invalid numeric values.
    if observation.unit != "MW" or not observation.evidence:
        return True  # Keep unit/evidence failures visible to ordinary checks.
    number = r"(?<![\d.])" + re.escape(f"{observation.value:g}") + r"(?:\.0+)?\s*MW\b"
    if not any(
        re.search(number, evidence.quote or "", re.IGNORECASE)
        for evidence in observation.evidence
    ):
        return False
    pages = {
        (doc.document_id, page.number): " ".join(page.text.split())
        for doc in documents or []
        for page in doc.pages
    }
    for evidence in observation.evidence:
        quote = " ".join((evidence.quote or "").split())
        contexts = [quote]
        source = pages.get((evidence.document_id, evidence.page), "")
        # Include nearby source context so cropping a historical quote cannot
        # turn an earlier permission into the current proposal's capacity.
        if quote:
            start = 0
            while (position := source.find(quote, start)) >= 0:
                contexts.append(source[max(0, position - 240) : position + len(quote)])
                start = position + len(quote)
        for context in contexts:
            if re.search(
                number + r"\s+(?:grid\s+)?connection\b", context, re.IGNORECASE
            ):
                return False
            if re.search(
                r"planning permission was (?:approved|granted).{0,240}" + number,
                context,
                re.IGNORECASE,
            ):
                return False
    return True


def valid_value(field: str, value: Value) -> bool:
    if field == "capacity_mw":
        return type(value) in (int, float) and value > 0
    if field == "submission_date":
        if value is None:
            return True
        try:
            return (
                isinstance(value, str)
                and date.fromisoformat(value).isoformat() == value
            )
        except ValueError:
            return False
    if value is None and field not in REQUIRED_FIELDS:
        return True
    return isinstance(value, str) and bool(value.strip())


def has_evidence(
    observation: ExtractedField, documents: list[ParsedDocument] | None
) -> bool:
    if not observation.evidence:
        return False
    pages = {
        (doc.document_id, page.number): page.text
        for doc in documents or []
        for page in doc.pages
    }
    for evidence in observation.evidence:
        if evidence.page is None or not evidence.quote or not evidence.quote.strip():
            return False
        if documents is not None:
            source = pages.get((evidence.document_id, evidence.page))
            if source is None or " ".join(evidence.quote.split()) not in " ".join(
                source.split()
            ):
                return False
    return True


def reconcile(
    observations: list[ExtractedField],
    *,
    documents: list[ParsedDocument] | None = None,
    overrides: dict[str, Value] | None = None,
) -> tuple[ProjectFeatures | None, ReadinessResult]:
    groups: dict[str, list[ExtractedField]] = defaultdict(list)
    for observation in observations:
        if observation not in groups[observation.field]:
            groups[observation.field].append(observation)
    result = ReadinessResult()
    canonical: dict[str, Value] = {}
    overrides = overrides or {}
    for name in sorted(set(groups) | set(REQUIRED_FIELDS) | set(overrides)):
        if name in overrides:
            value = overrides[name]
            if not valid_value(name, value):
                result.invalid_fields.append(name)
            else:
                canonical[name] = value
            continue
        group = [
            item
            for item in groups[name]
            if item.value is not None
            and (name != "capacity_mw" or is_proposed_capacity(item, documents))
        ]
        if not group:
            if name in REQUIRED_FIELDS:
                result.missing_fields.append(name)
            continue
        values = {str(item.value) for item in group}
        # Numeric JSON values 12 and 12.0 denote the same capacity.
        if name == "capacity_mw":
            values = {
                str(float(item.value))
                if type(item.value) in (int, float)
                else str(item.value)
                for item in group
            }
        if len(values) > 1 or any(item.conflict for item in group):
            result.conflicts.append(Conflict(field=name, observations=group))
        if any(item.confidence < MIN_CONFIDENCE for item in group):
            result.low_confidence_fields.append(name)
        if any(not has_evidence(item, documents) for item in group):
            result.unsupported_fields.append(name)
        if any(
            not valid_value(name, item.value)
            or (name == "capacity_mw" and item.unit != "MW")
            for item in group
        ):
            result.invalid_fields.append(name)
        canonical[name] = group[0].value
    technology = canonical.get("technology")
    if isinstance(technology, str):
        result.domain_status = (
            "IN_DOMAIN" if technology in SUPPORTED_TECHNOLOGIES else "OUT_OF_DOMAIN"
        )
        if result.domain_status == "OUT_OF_DOMAIN":
            result.message = "Historical model unavailable for this project category."
    result.ready_for_review = result.domain_status == "IN_DOMAIN" and not any(
        [
            result.conflicts,
            result.missing_fields,
            result.low_confidence_fields,
            result.unsupported_fields,
            result.invalid_fields,
        ]
    )
    if not result.ready_for_review:
        return None, result
    return ProjectFeatures.model_validate(canonical), result
