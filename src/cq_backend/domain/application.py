from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


FieldName = Literal[
    "technology", "capacity_mw", "project_name", "planning_authority", "site_location"
]
Value = str | float | int | bool | None
SUPPORTED_TECHNOLOGIES = frozenset(
    {"solar", "onshore_wind", "offshore_wind", "hydro", "biomass", "tidal", "wave"}
)


class Evidence(Contract):
    document_id: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1)
    quote: str | None = None


class ExtractedField(Contract):
    field: FieldName
    value: Value
    confidence: float = Field(ge=0, le=1)
    evidence: list[Evidence] = Field(default_factory=list)
    unit: str | None = None
    conflict: bool = False


class ParsedBlock(Contract):
    text: str
    kind: str
    bbox: dict[str, float | str] | None = None


class ParsedPage(Contract):
    number: int = Field(ge=1)
    text: str
    blocks: list[ParsedBlock] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)


class ParsedDocument(Contract):
    document_id: str
    pages: list[ParsedPage]


class DocumentMetadata(Contract):
    document_id: str = Field(default_factory=new_id)
    filename: str
    media_type: str
    size_bytes: int = Field(gt=0)
    sha256: str
    storage_reference: str


class Conflict(Contract):
    field: FieldName
    observations: list[ExtractedField]


class ReadinessResult(Contract):
    ready_for_review: bool = False
    conflicts: list[Conflict] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    low_confidence_fields: list[str] = Field(default_factory=list)
    unsupported_fields: list[str] = Field(default_factory=list)
    invalid_fields: list[str] = Field(default_factory=list)
    domain_status: Literal["IN_DOMAIN", "OUT_OF_DOMAIN", "UNKNOWN"] = "UNKNOWN"
    message: str | None = None


class ProjectFeatures(Contract):
    technology: str
    capacity_mw: float = Field(gt=0, strict=True)
    project_name: str | None = None
    planning_authority: str | None = None
    site_location: str | None = None


class Correction(Contract):
    field: FieldName
    original_values: list[Value]
    previous_value: Value
    corrected_value: Value
    actor: str = Field(min_length=1)
    changed_at: datetime = Field(default_factory=utc_now)
    reason: str | None = None


class CorrectionRequest(Contract):
    expected_revision: int = Field(ge=1)
    actor: str = Field(min_length=1, max_length=200)
    values: dict[FieldName, Value] = Field(min_length=1)
    reason: str | None = Field(default=None, max_length=2000)


class ProcessingStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    EXTRACTING = "EXTRACTING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    READY = "READY"
    SCORED = "SCORED"
    FAILED = "FAILED"


class Prediction(Contract):
    withdrawal_probability_12m: float = Field(ge=0, le=1)
    decision_distribution: list[float] = Field(min_length=1)

    def model_post_init(self, context: object) -> None:
        if any(value < 0 or value > 1 for value in self.decision_distribution):
            raise ValueError("Decision probabilities must be between zero and one")
        if abs(sum(self.decision_distribution) - 1) > 1e-6:
            raise ValueError("Decision distribution must sum to one")


class CarbonScenario(Contract):
    name: str = "default"
    parameters: dict[str, Value] = Field(default_factory=dict)


class CarbonEstimate(Contract):
    tonnes_co2e: float
    methodology_reference: str = Field(min_length=1)


class EffortEstimate(Contract):
    reviewer_hours: float = Field(gt=0)


class Application(Contract):
    application_id: str = Field(default_factory=new_id)
    revision: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utc_now)
    status: ProcessingStatus = ProcessingStatus.UPLOADED
    documents: list[DocumentMetadata] = Field(default_factory=list)
    parsed_documents: list[ParsedDocument] = Field(default_factory=list)
    observations: list[ExtractedField] = Field(default_factory=list)
    corrections: list[Correction] = Field(default_factory=list)
    readiness: ReadinessResult = Field(default_factory=ReadinessResult)
    project_features: ProjectFeatures | None = None
    prediction: Prediction | None = None
    carbon: CarbonEstimate | None = None
    effort: EffortEstimate | None = None
    scenario: CarbonScenario | None = None
    queue_run_id: str | None = None
    simulation_ids: list[str] = Field(default_factory=list)
    error: str | None = None


class ExtractionResult(Contract):
    observations: list[ExtractedField]
