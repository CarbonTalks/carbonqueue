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

For Gemini, copy `.env.example` to `.env` and paste your Google AI Studio key into
`GOOGLE_API_KEY`:

```dotenv
CQ_EXTRACTION_MODEL=google:gemini-3.8-flash
GOOGLE_API_KEY=your-key-here
```

Run `uv sync --locked` and `uv run cq-backend` from the project root. The backend
loads `.env` from the current working directory; existing process environment
variables take precedence. `.env` is excluded from Git and container build contexts.
For containers, pass credentials at runtime with `--env-file .env`; they are not
baked into the image. Restart the server after editing `.env`.

Gemini and OpenAI providers are installed. You can change `CQ_EXTRACTION_MODEL` to
another supported PydanticAI `provider:model` identifier. Other providers require
their corresponding extras. See [PydanticAI Google configuration](https://pydantic.dev/docs/ai/models/google/).
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

The agent receives readable page text with document/page headers. Its output schema
requires nonempty evidence quotes and explicit unit/scope metadata. Invalid values
or quotes are returned to the model for correction, with the cited source page when
available, within the existing three-request limit. Quote matching remains exact
apart from whitespace. Missing capacity and genuine conflicts are not retried into
guessed values; reconciliation still sends them to human review. Submission dates
need explicit submitted/received context; signature and cover-letter dates are not
accepted as substitutes.

The initial canonical contract requires `technology` and `capacity_mw`. Optional
fields are `project_name`, `planning_authority`, `site_location`, `applicant` and
`submission_date` (a date in `YYYY-MM-DD` format) and `has_storage` (a boolean).
Missing optional fields are null.
Capacity must
be positive and explicitly stated in MW. Other units require human correction;
the backend does not silently convert them. The confidence threshold is 0.8.

Supported categories are solar, onshore wind, battery, hydro, biomass, tidal and
wave. Offshore wind and other categories, including heat pumps, return
`readiness.domain_status = OUT_OF_DOMAIN` with “Historical model unavailable for
this project category.”

Capacity observations carry `capacity_scope`: `proposed_project`, `existing_project`,
`neighbouring_project`, `grid_connection` or `unknown`. Only proposed-project values
can become canonical capacity. The stated number must occur in its quotation;
explicit grid-connection and earlier-permission context is rejected, including
context immediately before a cropped quote. If only unrelated or uncertain
capacities exist, capacity is missing and the application remains `NEEDS_REVIEW`.
Rejected observations are retained for audit. Older observations without a scope
default to `unknown` and require human confirmation when reconciled again.
These conservative checks supplement the extractor; they do not establish perfect
semantic understanding of every possible document.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/applications/extract` | Upload one or more PDFs as multipart `files` |
| GET | `/applications` | List persisted applications |
| POST | `/applications/import` | Atomically import a normalized pending-application batch |
| GET | `/applications/pending` | List imported pending applications, including those awaiting confirmation |
| GET | `/applications/{id}` | Read application, observations, evidence and outputs |
| PATCH | `/applications/{id}/observations` | Correct canonical values with an audit record |
| POST | `/queue/run` | Score selected ready applications and call the external scheduler |
| GET | `/queue` | Read the latest queue; returns 409 if corrected data invalidated it |
| POST | `/queue/live/import` | Import a cq-sim live-queue snapshot and its application records |
| GET | `/queue/live` | Serve the imported dashboard snapshot with backend application links |
| POST | `/simulation/run` | Serve prepared year/policy results; legacy application requests call the external simulator |
| GET | `/simulation/historical/{year}/{policy}` | Read a prepared cq-sim historical result |
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

## Pending applications and the dashboard

Load cq-sim's prepared queue through the backend, then have the dashboard read
`GET /queue/live`:

```sh
curl --fail -H 'Content-Type: application/json' \
  --data-binary @../cq-sim/results/live-queue.json \
  http://127.0.0.1:8000/queue/live/import
```

The backend preserves `as_of`, calibration, emission factors, ranks, planned weeks,
reasons and the separate `needs_confirmation` list. Each record gains an
`application_id` linking to `/applications/{id}`. The snapshot stays dated source
data; it is not a newly calculated queue. `changed_application_ids` lists records
with human corrections, whose prepared ranks may no longer reflect current data.
The externally supplied scoring and scheduling algorithms remain necessary to
calculate a new queue.

The supplied July 24, 2026 snapshot has 765 ranked records and 35 requiring
confirmation, not 936. `generation_mw` becomes capacity only when supplied;
`technology = Battery` maps to `battery`, without inventing missing storage
capacity. Other category names are preserved. Missing capacities remain
`NEEDS_REVIEW`, while the dashboard can still display their source records.

For another pending dataset, `POST /applications/import` accepts:

```json
{
  "source": "REPD",
  "applications": [
    {"external_id": "19786", "technology": "solar", "capacity_mw": null,
     "project_name": "Arncott", "submission_date": "2025-09-01"}
  ]
}
```

The example date is illustrative. Batches contain 1–2000 records. Source name and
external ID determine stable backend IDs. Imports are transactional and idempotent:
repeating identical source data preserves corrections; changed source values return
`IMPORT_CONFLICT` (409) without overwriting or partially importing records. An import
does not replace or delete an older dataset. Imported values retain their source
provenance separately from PDF observations and do not trigger model calls.

## External component contracts

ML and queue algorithms are owned externally. They can be injected through
`create_app(..., ml=..., queue_engine=...)` using the async protocols in
`integrations/`. Set `CQ_ML_URL` and `CQ_QUEUE_ENGINE_URL` to use the HTTP adapters.
External endpoints are **backend-defined contracts to agree with those teams**;
The model can run in a separate Python process using the bridge below.
The queue engine is cq-sim's HTTP adapter (`PYTHONPATH=src python -m cqsim serve` in cq-sim,
port 9002; set `CQ_QUEUE_ENGINE_URL=http://127.0.0.1:9002`). It implements `carbon`, `effort`
and `schedule`; `simulate` is only needed when retaining the legacy uploaded-application
simulation path.

`ml` can also be a synchronous or asynchronous Python function taking a
`ProjectFeatures` object and returning a `Prediction` or matching dictionary:

```python
from cq_backend.app import create_app
from cq_backend.domain.application import Prediction, ProjectFeatures

def predict(project: ProjectFeatures) -> Prediction:
    return trained_model.predict(project)  # Your supplied model implementation.

app = create_app(ml=predict, queue_engine=engine)
```

Here `trained_model` and `engine` are the externally supplied implementations.
Synchronous functions run on a worker thread. Function and HTTP outputs use the
same validation; calls have a 30-second timeout. Cancelling a timed-out synchronous
call cannot terminate its worker thread. The optional applicant and submission date
can be null; HTTP dates are ISO strings, while Python receives a `date` object.

| External call | Request JSON | Validated response |
| --- | --- | --- |
| POST ML `/predict` | `ProjectFeatures` | `withdrawal_probability_12m`, `decision_distribution` |
| POST engine `/carbon` | `project: Application`, `scenario: CarbonScenario` | `daily_tco2: {low, central, high}` or `unscored_reason`, plus `methodology_reference` |
| POST engine `/effort` | `project: Application` | `reviewer_hours` |
| POST engine `/schedule` | `projects: Application[]`, `policy`, `capacity` | `entries: [{application_id, position, score?, lane?, reason?, planned_week?}]` |
| POST engine `/simulate` | `application_ids`, `parameters`, backend-resolved `projects: Application[]` | `metrics: {name: number}`, optional `references` |

The decision distribution has exactly 13 probabilities: the next twelve 30-day
bins from the prediction date, conditional on the application still being pending,
then no decision within the next 360 days. This matches cq-model's rolling horizon;
it is not measured from the original submission date. Values lie in [0, 1] and sum
to one. Withdrawal is reported separately and is included in the final no-decision
bin; do not add its probability to the 13 bins.

Carbon is an avoided-emissions estimate, expressed in **tonnes CO2e per day** when
using `daily_tco2`; it is not electricity consumption. Bands must satisfy
`0 <= low <= central <= high`. Storage has no generation-carbon estimate in the
current methodology: return `unscored_reason`, with both numeric fields null.
Exactly one of `daily_tco2`, the legacy total `tonnes_co2e`, or `unscored_reason`
must be supplied, together with a methodology reference. `SCORED` means the
model/effort assessment finished; an application can be SCORED while its carbon
estimate is explicitly unscored. The scheduler must handle that lane.

`ProjectFeatures.has_storage` is optional: `null` means unknown, `false` means
confirmed absent. Imports, extraction observations and human corrections preserve
it. A battery-only project's technology identifies storage even if this optional
field is unknown. For Python adapters, `project.project_features.simulation_category`
maps solar → solar, onshore_wind → onshore_wind, battery → storage,
biomass → bioenergy_waste, and hydro/tidal/wave → other_renewable. HTTP adapters
apply the same mapping themselves; the wire `technology` stays in backend terms.
Do not reverse-map all bioenergy/waste to biomass or other_renewable to a particular
technology: those categories are broader than the backend's technology labels.
Offshore wind remains outside scope.

Queue entries reference selected applications, with unique IDs and positive unique
positions. `lane`, `reason` and `planned_week` carry the scheduler's explanation.
Run IDs are generated by the backend. Model and HTTP responses are validated before
persistence. Calls use a 30-second HTTP timeout.

Ready uploads are automatically scored only when both external components are
configured. Otherwise they remain `READY`. Queue and simulation calls report
unavailability explicitly. Queue output and application links are written in one
Zova transaction with revision checks; simulations use the same atomic publication.

## Limits and deployment

Document extraction accepts PDFs only: up to 10 files, 20 MiB per file and 200
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

Check the Arncott capacity safety guards against the supplied PDFs without an LLM
or Docling model downloads:

```sh
CQ_DEMO_DOCS=/path/to/cq-demo-docs uv run pytest -q tests/test_arncott_safety.py
```

This test reads real PDF text with PDFium and deliberately supplies incorrect 8 MW
and 5 MW observations. It verifies `NEEDS_REVIEW`, missing capacity, preserved
observations, blocked scoring and the audited correction path. It tests the backend
guards, not live LLM extraction accuracy.

## Separate-process ML connection

Run [integration/ml_server.py](integration/ml_server.py) with the model team's
Python environment. It uses only the standard library, so the backend's Python
3.14 and Docling dependencies do not need to be installed in that environment.

The model team supplies a **synchronous callable** accepting the feature dictionary
sent by the backend. It loads the trained model and builds its model-specific
features, then returns the two prediction fields shown above. The existing
`cq.model.predict(model, feats, app_ids, ...)` is not itself this callable; a wrapper
must build those inputs and translate its outputs. No training or synthetic
predictions are performed by this bridge.

```sh
# From cq-model, in its Python environment (pandas, pyarrow, catboost).
# cq.serve:predict loads the data and model_live.cbm once, on the first request.
cd ../cq-model
PYTHONPATH=src python ../cq-backend/integration/ml_server.py --predictor cq.serve:predict --port 9001
```

Set `CQ_ML_URL=http://127.0.0.1:9001` in the backend `.env`, then start the backend
normally. The bridge serves `POST /predict` and `GET /health`, validates returned
probabilities, and keeps model exceptions out of responses. It binds to localhost
by default. For a backend container, supply a URL reachable from that container;
its `127.0.0.1` refers to the container itself. Use `--host` only when the bridge
must bind to another interface. The bridge handles requests sequentially, avoiding
concurrent access to a shared model instance.

## Full demo stack

Four processes, each in its own terminal, with the four repositories side by side:

```sh
# 1. Model (cq-model environment; generate data and model_live.cbm first, see cq-model README)
cd cq-model && PYTHONPATH=src python ../cq-backend/integration/ml_server.py --predictor cq.serve:predict --port 9001

# 2. Queue engine (cq-sim)
cd cq-sim && PYTHONPATH=src python -m cqsim serve

# 3. Backend (this repository), with .env:
#    CQ_ML_URL=http://127.0.0.1:9001
#    CQ_QUEUE_ENGINE_URL=http://127.0.0.1:9002
#    CQ_CORS_ORIGINS=http://localhost:5173
#    CQ_SIMULATION_RESULTS_DIR=../cq-sim/results
#    CQ_EXTRACTION_MODEL=google:gemini-3.8-flash and GOOGLE_API_KEY=... for PDF extraction
uv run cq-backend

# 4. Dashboard (cq-website)
cd cq-website && npm install && npm run dev
```

Load the live queue once:

```sh
curl --fail -H 'Content-Type: application/json'   --data-binary @../cq-sim/results/live-queue.json   http://127.0.0.1:8000/queue/live/import
```

Checked end to end on 15 October 2026: import → model prediction → carbon band or unscored
reason → `/queue/run` with lane, reason and planned week → historical simulation → CORS for
the dashboard origin. PDF extraction needs the Gemini key and was not part of that check.

## Dashboard and historical simulation handoff

Set `CQ_CORS_ORIGINS=http://localhost:5173` to permit that dashboard origin;
multiple origins are comma-separated. The backend allows GET, POST and PATCH
with JSON bodies and exposes `X-Request-ID`. Without this setting it does not add
cross-origin permissions.

The website reads `/queue/live`, `/applications/pending`, and individual
`/applications/{application_id}` records. The live snapshot contains **765 ranked
records plus 35 awaiting confirmation** in the supplied dataset. Its values are
from cq-sim, not fresh backend predictions. Only the known cq-sim row fields are
served; unrecognized additions such as `realization_probability` or compliance
badges are omitted. `p_withdraw_12m` is a withdrawal probability, not a permission
or realization probability. Frontend code still needs to remove its hardcoded
fields and use these responses.

After a human correction, `/queue/live` keeps its historical snapshot and reports
`changed_application_ids`. A dynamic `/queue` becomes stale (409). Recalculate
with `POST /queue/run`, supplying the selected IDs, policy, capacity and scenario;
this reruns the model and engine with corrected features and publishes a new
queue. The external engine adapter must be configured for that operation.

Set `CQ_SIMULATION_RESULTS_DIR=../cq-sim/results` to serve the prepared historical
results. In containers, mount that directory read-only and configure its container
path. The backend preserves the source JSON's nested metrics and assumptions.

```sh
curl http://localhost:8000/simulation/historical/2023/carbonqueue
curl -X POST http://localhost:8000/simulation/run \
  -H 'Content-Type: application/json' \
  -d '{"year":2023,"policy":"carbonqueue"}'
```

Historical requests use no model or engine and do not change applications. Supported
years are 2019–2023; policies are `fifo`, `carbon`, `carbon_withdrawal`,
`carbon_withdrawal_effort`, and `carbonqueue`. Missing files return 404; missing
configuration returns 503; malformed or mismatched results return 502. The older
`application_ids` request form remains available for existing external simulation
adapters. New demo screens should use the historical form because newly uploaded
projects do not have observed outcomes for a retrospective carbon-gain comparison.
