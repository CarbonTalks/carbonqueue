from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


FieldName = Literal[
    "technology",
    "capacity_mw",
    "project_name",
    "planning_authority",
    "site_location",
    "applicant",
    "submission_date",
    "has_storage",
]
Value = str | float | int | bool | None
SUPPORTED_TECHNOLOGIES = frozenset(
    {"solar", "onshore_wind", "battery", "hydro", "biomass", "tidal", "wave"}
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
    capacity_scope: Literal[
        "proposed_project",
        "existing_project",
        "neighbouring_project",
        "grid_connection",
        "unknown",
    ] = "unknown"


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
    applicant: str | None = None
    submission_date: date | None = None
    has_storage: bool | None = Field(default=None, strict=True)

    @property
    def simulation_category(self) -> str:
        return {
            "solar": "solar",
            "onshore_wind": "onshore_wind",
            "battery": "storage",
            "biomass": "bioenergy_waste",
            "hydro": "other_renewable",
            "tidal": "other_renewable",
            "wave": "other_renewable",
        }[self.technology]

    @field_validator("submission_date", mode="before")
    @classmethod
    def validate_submission_date(cls, value):
        if value is None or type(value) is date:
            return value
        if isinstance(value, str):
            parsed = date.fromisoformat(value)
            if parsed.isoformat() == value:
                return parsed
        raise ValueError("Submission date must be a date in YYYY-MM-DD format")


class ImportedProject(ProjectFeatures):
    external_id: str = Field(min_length=1, max_length=200)
    capacity_mw: float | None = Field(default=None, gt=0, strict=True)


class ApplicationImport(Contract):
    source: str = Field(min_length=1, max_length=200)
    applications: list[ImportedProject] = Field(min_length=1, max_length=2000)


class ApplicationSource(Contract):
    name: str
    external_id: str


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
    decision_distribution: list[float] = Field(
        min_length=13,
        max_length=13,
        description="Decision probabilities for the next twelve 30-day bins from the prediction date, conditional on still pending, followed by no decision within 360 days (including withdrawal). Values sum to one; withdrawal is reported separately.",
    )

    def model_post_init(self, context: object) -> None:
        if any(value < 0 or value > 1 for value in self.decision_distribution):
            raise ValueError("Decision probabilities must be between zero and one")
        if abs(sum(self.decision_distribution) - 1) > 1e-6:
            raise ValueError("Decision distribution must sum to one")


class CarbonScenario(Contract):
    name: str = "default"
    parameters: dict[str, Value] = Field(default_factory=dict)


class CarbonBands(Contract):
    low: float = Field(ge=0)
    central: float = Field(ge=0)
    high: float = Field(ge=0)

    def model_post_init(self, context: object) -> None:
        if not self.low <= self.central <= self.high:
            raise ValueError("Carbon bands must satisfy low <= central <= high")


class CarbonEstimate(Contract):
    # Legacy total estimates remain readable; daily rates have explicit units.
    tonnes_co2e: float | None = Field(default=None, ge=0)
    daily_tco2: CarbonBands | None = None
    unscored_reason: str | None = Field(default=None, min_length=1)
    methodology_reference: str = Field(min_length=1)

    def model_post_init(self, context: object) -> None:
        estimates = int(self.tonnes_co2e is not None) + int(self.daily_tco2 is not None)
        if estimates + int(self.unscored_reason is not None) != 1:
            raise ValueError("Provide one total, daily bands, or unscored reason")


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
    source: ApplicationSource | None = None
    source_values: dict[FieldName, Value] = Field(default_factory=dict)


class ExtractionResult(Contract):
    observations: list[ExtractedField]
