import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(".data")
    extraction_model: str | None = None
    ml_url: str | None = None
    queue_engine_url: str | None = None
    max_file_bytes: int = 20 * 1024 * 1024
    max_files: int = 10
    max_pages: int = 200
    extraction_timeout_seconds: float = 300

    def __post_init__(self):
        if (
            min(
                self.max_file_bytes,
                self.max_files,
                self.max_pages,
                self.extraction_timeout_seconds,
            )
            <= 0
        ):
            raise ValueError("Resource limits must be positive")

    @classmethod
    def from_env(cls):
        return cls(
            data_dir=Path(os.getenv("CQ_DATA_DIR", ".data")),
            extraction_model=os.getenv("CQ_EXTRACTION_MODEL"),
            ml_url=os.getenv("CQ_ML_URL"),
            queue_engine_url=os.getenv("CQ_QUEUE_ENGINE_URL"),
        )
