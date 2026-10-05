# CarbonQueue backend

Convert planning PDFs into evidence-backed application data, reconcile observations,
record human corrections, and orchestrate external ML and carbon/queue services.
The backend supports review prioritization; it does not approve or reject projects.

## Run

Requires Python 3.14 and uv. Dependencies and tests use current stable releases,
including Zova 1.1.0; `uv.lock` records reproducible versions.

```sh
uv sync --locked
uv run cq-backend
```

The API listens on `127.0.0.1:8000`. Health is available at `/health`, and the
generated OpenAPI schema at `/schema/openapi.json`.

Set `CQ_EXTRACTION_MODEL` to a PydanticAI `provider:model` identifier and supply
the provider's credentials before starting the server. The installed agent package
includes the OpenAI provider; other providers require their corresponding
PydanticAI extras. See [PydanticAI model documentation](https://ai.pydantic.dev/models/overview/).
Without a configured model, extraction returns `EXTRACTOR_UNAVAILABLE`.
No synthetic extraction is used in the running application.

Docling downloads its OCR, layout and table models on first PDF conversion.
That first request requires network access and can be slower than later requests.
Raw PDFs and the Zova database default to `.data/`; set `CQ_DATA_DIR` to change
the location. Keep this directory durable across restarts.

```sh
curl -F 'files=@application-form.pdf' -F 'files=@technical-report.pdf' \
  http://127.0.0.1:8000/applications/extract
```

## Application workflow

Each upload creates one application containing all its documents. The processing
states are `UPLOADED`, `PARSING`, `EXTRACTING`, `NEEDS_REVIEW`, `READY`, `SCORED`
and `FAILED`. Interrupted uploads are marked `FAILED` on startup.

Docling preserves pages, text, headings, tables and bounding boxes. PydanticAI
extracts separate observations with source document IDs, one-based page numbers,
quotations and confidence. Reconciliation verifies the quotations against the
parsed source and blocks conflicting, unsupported, invalid or low-confidence
observations. Identical observations do not create conflicts.

The initial canonical contract requires `technology` and `capacity_mw`. Optional
fields are `project_name`, `planning_authority` and `site_location`. Capacity must
be positive and explicitly stated in MW. Other units require human correction;
the backend does not silently convert them. The confidence threshold is 0.8.

The initial supported categories are solar, onshore wind, offshore wind, hydro,
biomass, tidal and wave. Other categories, including heat pumps, return
`readiness.domain_status = OUT_OF_DOMAIN` with “Historical model unavailable for
this project category.” Confirm this category list with the external ML team
before integrating a narrower trained model.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/applications/extract` | Upload one or more PDFs as multipart `files` |
| GET | `/applications` | List persisted applications |
| GET | `/applications/{id}` | Read application, observations, evidence and outputs |
| PATCH | `/applications/{id}/observations` | Correct canonical values with an audit record |
| POST | `/queue/run` | Score selected ready applications and call the external scheduler |
| GET | `/queue` | Read the latest queue; returns 409 if corrected data invalidated it |
| POST | `/simulation/run` | Call the external simulation component and persist its result |
| GET | `/simulation/{id}` | Read a persisted simulation |

Correct observations using the current application's `revision`:

```json
{
  "expected_revision": 4,
  "actor": "reviewer-123",
  "values": {"capacity_mw": 12.6},
  "reason": "Confirmed the technical report"
}
```

Corrections retain every original observation and record original values, the
previous correction, the new value, actor, timestamp and reason. Readiness is
recalculated, and old predictions, carbon/effort outputs and queue membership are
invalidated. Stale revisions return 409. Correction does not automatically call
external models; `/queue/run` scores the new canonical values.

Example queue request:

```json
{
  "application_ids": ["application-id"],
  "policy": {"name": "FIFO", "parameters": {}},
  "capacity": 8,
  "scenario": {"name": "default", "parameters": {}}
}
```

Policy names, capacity semantics and scenario parameters belong to the external
engine. The backend passes them through and implements no scoring or carbon formulas.

Example simulation request:

```json
{"application_ids": ["application-id"], "parameters": {}}
```

Each response has an `X-Request-ID`. Backend failures include a code, safe message,
request ID and application ID when one has been persisted. Provider details are
not exposed. Parsing/extraction failures remain retrievable as `FAILED` applications;
integration failures preserve valid extraction and do not save partial model outputs.

## External component contracts

ML and queue algorithms are owned externally. They can be injected through
`create_app(..., ml=..., queue_engine=...)` using the async protocols in
`integrations/`. Set `CQ_ML_URL` and `CQ_QUEUE_ENGINE_URL` to use the HTTP adapters.
External endpoints are **backend-defined contracts to agree with those teams**;
no existing external service implementation was supplied with this plan.

| External call | Request JSON | Validated response |
| --- | --- | --- |
| POST ML `/predict` | `ProjectFeatures` | `withdrawal_probability_12m`, `decision_distribution` |
| POST engine `/carbon` | `project: Application`, `scenario: CarbonScenario` | `tonnes_co2e`, `methodology_reference` |
| POST engine `/effort` | `project: Application` | `reviewer_hours` |
| POST engine `/schedule` | `projects: Application[]`, `policy`, `capacity` | `entries: [{application_id, position, score?}]` |
| POST engine `/simulate` | `application_ids`, `parameters`, backend-resolved `projects: Application[]` | `metrics: {name: number}`, optional `references` |

The decision distribution is a nonempty probability mass function whose values
sum to one; its bin definitions must be agreed with the ML team. Queue entries
must reference selected applications, with unique IDs and positive unique positions.
Run IDs are generated by the backend. Model and HTTP responses are validated before
persistence. Calls use a 30-second HTTP timeout.

Ready uploads are automatically scored only when both external components are
configured. Otherwise they remain `READY`. Queue and simulation calls report
unavailability explicitly. Queue output and application links are written in one
Zova transaction with revision checks; simulations use the same atomic publication.

## Limits and deployment

This initial backend accepts PDFs only: up to 10 files, 20 MiB per file and 200
pages per PDF. The extraction prompt has a one-million-character limit, at most
three agent requests, and a 300-second processing timeout. These limits can be
changed through `Settings` when creating the app. Parsing/extraction runs one
application at a time in each process; CPU work and native database calls run off
the event loop. Zova handles stay on their dedicated thread.

Run one backend process per data directory. Startup recovery assumes exclusive
ownership of that directory. This is a synchronous-request workflow; it has no
durable worker queue or automatic retry endpoint. The correction actor is
caller-supplied, and authentication/authority identity integration is not included
in this plan. Use a trusted deployment boundary before exposing application data.

## Tests

```sh
uv run pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
```

The default suite uses real Zova and replaces parser/model/network boundaries where
needed. It covers evidence checking, units, missing/low-confidence/conflicting
values, out-of-domain projects, upload limits, corrections, stale writes,
transaction rollback and integration failures. The PydanticAI test uses its
`TestModel`; paid provider inference and the external teams' algorithms are not
tested here.

Run the real PDF → Docling → typed agent → Zova/reopen test with:

```sh
CQ_TEST_DOCLING=1 uv run pytest -q tests/test_docling_live.py
```

This test downloads Docling models when needed and replaces only the paid LLM
boundary with `TestModel`. It remains opt-in so routine tests need no model downloads.
