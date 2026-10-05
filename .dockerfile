# syntax=docker/dockerfile:1
FROM python:3.14-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    CQ_DATA_DIR=/data \
    HF_HOME=/home/app/.cache/huggingface

# Native runtime libraries used by OpenCV and PyTorch/Docling.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates libgl1 libglib2.0-0t64 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 app

WORKDIR /app

# Copy only application inputs; keep local environments, documents and secrets out.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# RapidOCR downloads checkpoints into its package directory on first conversion.
RUN mkdir -p /data /home/app/.cache/huggingface \
    && chown -R app:app /app /data /home/app

USER app
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).close()"]

# Supply CQ_EXTRACTION_MODEL, provider credentials and external service URLs at runtime.
# Docling model downloads require network access on the first conversion.
# One worker per data directory, matching the application's startup recovery contract.
CMD ["uvicorn", "cq_backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
