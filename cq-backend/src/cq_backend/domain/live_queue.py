from datetime import date

from pydantic import ConfigDict, Field, JsonValue

from cq_backend.domain.application import Contract


class LiveQueueRecord(Contract):
    # cq-sim owns the ranking metadata; preserve it without treating it as a
    # backend prediction or evidence extracted from a planning document.
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    __pydantic_extra__: dict[str, JsonValue] = Field(init=False)
    app_id: int = Field(gt=0, strict=True)
    site_name: str
    authority: str | None = None
    category: str
    submitted: date
    technology: str | None = None
    generation_mw: float | None = Field(default=None, gt=0, strict=True)


class LiveQueueSnapshot(Contract):
    as_of: date
    emission_factor_tco2_per_mwh: dict[str, float]
    calibration: dict[str, JsonValue]
    lane_counts: dict[str, int]
    files: list[LiveQueueRecord] = Field(max_length=2000)
    needs_confirmation: list[LiveQueueRecord] = Field(max_length=2000)
