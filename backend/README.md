# MetricMind Backend

FastAPI service for MetricMind. It answers business questions through a
**governed semantic layer** — the eight metrics and the dimensions defined in
[`docs/metric_dictionary.md`](../docs/metric_dictionary.md) — on top of the dbt
`MART` models in Snowflake.

Two properties are load-bearing, and the test suite asserts both:

1. **No raw SQL from clients.** There is no request field anywhere that accepts
   SQL. Request models set `extra="forbid"`, SQL identifiers come only from the
   governed registry, and every filter value is a bound parameter.
2. **No fake results.** When the warehouse is unreachable or unconfigured the
   API returns a typed error (`503` / `502` / `504`). It never substitutes
   sample data for a real query result.

---

## Quick start

### 1. Create and activate a virtual environment (recommended)

From the repository root:

```bash
# macOS / Linux / Git Bash
python -m venv backend/.venv
source backend/.venv/bin/activate

# Windows PowerShell
python -m venv backend/.venv
backend\.venv\Scripts\Activate.ps1
```

A virtual environment keeps the backend's dependencies isolated from other
projects on the same machine. `backend/.venv` is covered by the repository's
existing `.venv` gitignore rule and must never be committed.

### 2. Install dependencies

From the repository root, with the virtual environment active:

```bash
pip install -r backend/requirements.txt
```

### 3. Start the API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The server listens at <http://localhost:8000>.

### 4. Open the interactive API documentation

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI schema: <http://localhost:8000/openapi.json>

### 5. Verify the health endpoint

```bash
curl http://localhost:8000/api/v1/health
```

Without Snowflake credentials the response reports `"status": "degraded"` with
`warehouse.configured: false`. With the warehouse configured (and the agent
module available) it reports `"status": "ok"`. `GET /health` is an alias of the
same endpoint for simple local probes.

### 6. Run the test suite

```bash
cd backend
python -m pytest -q
```

The suite replaces the warehouse with an in-memory fake via FastAPI dependency
overrides. It requires **no** Snowflake account and makes **no** network calls.
See [Testing](#testing) for the full guide — what each file covers, how to run a
single test, and what is not covered.

### Snowflake credentials: required vs. not required

- **Not required** to start the service, to run the test suite, or to serve
  `GET /api/v1/health`, `GET /api/v1/metrics`, `GET /api/v1/dimensions`,
  `POST /api/v1/validate/query` (returns a compiled SQL preview, executes
  nothing) and `POST /api/v1/validate/data` (audits the rows supplied in the
  request body).
- **Required** for `POST /api/v1/chat/query` to run against the real warehouse.
  Without credentials it returns `503 configuration_error` naming the missing
  settings — it never substitutes sample data for a real query result. See
  [Configuration](#configuration) for the environment variables to set in
  `backend/.env`.

---

## Configuration

### Where settings come from

All settings are environment variables, optionally loaded from `backend/.env`.
The application finds `backend/.env` by its own location (not the working
directory), so the server can be started from anywhere. Unknown environment
variables are ignored (`extra="ignore"`), and names are matched
 case-insensitively.

Variables are read at process start and cached (`get_settings()`); the
application never connects to Snowflake or validates credentials while loading
configuration. Credential presence is only *reported* (health payload,
`warehouse.configured`) or checked at the moment a real connection is attempted.

### Local setup with `backend/.env`

```bash
cp backend/.env.example backend/.env
```

Then edit `backend/.env` and fill in the Snowflake values you need.
`backend/.env` is gitignored (via the repository's `.env` rule) and **must never
be committed**. It contains only values, never real credentials — the same is
true of [`backend/.env.example`](.env.example), which holds placeholders only.
There are no real credentials anywhere in this repository.

### Which variables are required for Snowflake execution

The Snowflake backend is usable when all four of these are set (a *presence*
check, per `Settings.warehouse_configured` in `app/config.py` — the values are
never validated until a connection is attempted):

| Required | Purpose |
|---|---|
| `SNOWFLAKE_ACCOUNT` | Snowflake account identifier |
| `SNOWFLAKE_USER` | User name |
| `SNOWFLAKE_PASSWORD` | Password. Note: the current presence check requires all four settings unconditionally — setting `SNOWFLAKE_AUTHENTICATOR` does not lift this requirement |
| `SNOWFLAKE_WAREHOUSE` | e.g. `METRICMIND_WH` |

When any of them is missing:

- `GET /api/v1/health` reports `"status": "degraded"` with
  `warehouse.configured: false`, and `warehouse.missing_settings` lists the
  missing setting **names** (never values).
- `POST /api/v1/chat/query` returns `503 configuration_error` naming the missing
  settings. The application still starts and every other endpoint works.

If `WAREHOUSE_BACKEND=cube`, the required pair is `CUBE_API_URL` and
`CUBE_API_TOKEN` — but the Cube adapter is a placeholder that always reports
itself unconfigured until the semantic layer exists (see Known limitations and
`app/adapters/cube_client.py`).

### Full variable reference

Everything `.env.example` documents, matched against `app/config.py`:

| Variable | Default | Required? | Purpose |
|---|---|---|---|
| `APP_NAME` | `MetricMind Backend` | No | Service name in health output and OpenAPI docs |
| `APP_VERSION` | `0.1.0` | No | Version string in health output and OpenAPI docs |
| `API_V1_PREFIX` | `/api/v1` | No | URL prefix for the versioned API routes |
| `DEBUG` | `false` | No | Verbose logging |
| `CORS_ALLOW_ORIGINS` | `http://localhost:3000,http://localhost:5173` | No | Comma-separated allowed browser origins. Do not use `"*"` together with credentials |
| `CORS_ALLOW_CREDENTIALS` | `true` | No | Whether CORS requests may include credentials |
| `REQUEST_TIMEOUT_SECONDS` | `30` | No | Documented request timeout (see `.env.example`) |
| `WAREHOUSE_TIMEOUT_SECONDS` | `30` | No | Applied as both the Snowflake login timeout and the server-side `STATEMENT_TIMEOUT_IN_SECONDS` |
| `MAX_RESULT_ROWS` | `500` | No | Hard server-side cap on returned rows; the request `limit` is clamped to this |
| `DEFAULT_RESULT_ROWS` | `100` | No | Applied when a chat request omits `limit` |
| `WAREHOUSE_BACKEND` | `snowflake` | No | `snowflake` (implemented) or `cube` (not implemented) |
| `SNOWFLAKE_ACCOUNT` | – | **Yes** (snowflake backend) | Snowflake account identifier |
| `SNOWFLAKE_USER` | – | **Yes** (snowflake backend) | User name |
| `SNOWFLAKE_PASSWORD` | – | **Yes** (snowflake backend) | Password |
| `SNOWFLAKE_ROLE` | – | No | Sent to the driver only when set |
| `SNOWFLAKE_DATABASE` | `METRICMIND` | No | Per `docs/data_dictionary.md` |
| `SNOWFLAKE_SCHEMA` | `MART` | No | The dbt mart schema |
| `SNOWFLAKE_AUTHENTICATOR` | – | No | Optional; omit for username/password (e.g. `externalbrowser`, `snowflake_jwt`, `oauth`) |
| `CUBE_API_URL` | – | Yes for `cube` backend | Cube.dev REST endpoint (not implemented; see above) |
| `CUBE_API_TOKEN` | – | Yes for `cube` backend | Cube.dev auth token (not implemented; see above) |

Credential-shaped values (`SNOWFLAKE_PASSWORD`, `CUBE_API_TOKEN`) must never be
committed, echoed in logs, or pasted into issues. The code already enforces the
user-facing half of this: error messages and the health payload never contain
credential values, only missing-setting names — asserted by tests.

---

## Endpoints

This API is **governed by construction**: requests can reference only metric and
dimension names from the governed registry (`GET /api/v1/metrics`,
`GET /api/v1/dimensions`). There is no request field on any endpoint that
accepts SQL — request models set `extra="forbid"`, so an unknown field such as
`sql` is rejected with `422` before any handler runs. The SQL the backend runs
is compiled exclusively from the registry, with filter values passed as bound
parameters.

| Method | Path | Purpose | Executes a warehouse query? |
|---|---|---|---|
| `GET` | `/api/v1/health` | Health, agent status, governed counts, warehouse summary | No |
| `GET` | `/health` | Alias of the above, for simple local probes | No |
| `GET` | `/api/v1/metrics` | The governed metric catalogue | No |
| `GET` | `/api/v1/dimensions` | The governed dimension catalogue | No |
| `POST` | `/api/v1/chat/query` | Ask a governed business question | **Yes** — the only endpoint that runs SQL against the warehouse |
| `POST` | `/api/v1/validate/query` | Validate a governed query payload and preview its compiled SQL | No — compiles, never executes |
| `POST` | `/api/v1/validate/data` | Audit a set of result rows supplied in the request body | No — audits the rows you send |

Detailed request/response contracts follow in the per-endpoint sections below:
[`POST /api/v1/chat/query`](#post-apiv1chatquery),
[`GET /api/v1/metrics` and `/dimensions`](#get-apiv1metrics-and-dimensions),
[`POST /api/v1/validate/query`](#post-apiv1validatequery) and
[`POST /api/v1/validate/data`](#post-apiv1validatedata).

The same routes are explorable interactively: Swagger UI at
<http://localhost:8000/docs>, ReDoc at <http://localhost:8000/redoc>, and the
raw OpenAPI schema at <http://localhost:8000/openapi.json> — all served by the
application itself, so they are always in sync with the routes.

### `GET /api/v1/health`

No request parameters. The response is safe to expose: it reports *whether*
things are configured, never credential values.

```json
{
  "status": "degraded",
  "service": "MetricMind Backend",
  "version": "0.1.0",
  "agent_available": true,
  "agent_detail": null,
  "agent_declared_metrics": ["Sales", "Profit", "Quantity", "Discount", "Shipping Cost"],
  "agent_declared_dimensions": ["Year", "Country", "Market", "Region", "Category"],
  "warehouse": {
    "backend": "snowflake",
    "database": "METRICMIND",
    "schema": "MART",
    "configured": false,
    "missing_settings": ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD", "SNOWFLAKE_WAREHOUSE"]
  },
  "governed_metric_count": 8,
  "governed_dimension_count": 17
}
```

- `status` is `ok` when the agent module loaded **and** the warehouse reports
  itself configured; otherwise `degraded`. Both mean the service is running —
  missing Snowflake credentials are an expected local state, not an error.
- `agent_declared_metrics` / `agent_declared_dimensions` are the vocabulary the
  AI agent itself declares (quoted from `ai agent/schema.py`), which overlaps
  only partially with the governed registry — see Known limitations.
- `warehouse.missing_settings` lists setting **names** only, never values.

Returns `200` in all cases; check the `status` field.

### `GET /api/v1/metrics` and `GET /api/v1/dimensions`

No request parameters. Both return a `count` field plus the catalogue and the
governance notes. Per-item fields are documented in the section below.

Returns `200`. These are plain registry lookups — no warehouse access.

### Status codes across all endpoints

| Code | When |
|---|---|
| `200` | Success. For `chat/query`, ambiguous and unsupported are also 200 — they are valid outcomes, not errors |
| `422` | Request payload invalid (`request_validation_error`), or on `chat/query`, the governed payload failed schema validation (`validation_failed`) |
| `502` | `chat/query` only — the warehouse returned an error (`warehouse_error`), or the agent failed to interpret the question (`agent_error`) |
| `503` | `chat/query` only — warehouse not configured (`configuration_error`), or the agent module could not be loaded (`agent_unavailable`) |
| `504` | `chat/query` only — the warehouse query exceeded `WAREHOUSE_TIMEOUT_SECONDS` (`warehouse_timeout`) |

Every error, on every endpoint, uses one envelope:

```json
{
  "error": {
    "code": "configuration_error",
    "message": "The snowflake warehouse backend is not configured. Missing environment settings: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_WAREHOUSE.",
    "details": [],
    "correlation_id": "3f9c1a2b4d5e4f60"
  }
}
```

`correlation_id` also appears in the server log, so a support request can be
traced. Messages never contain credentials — the health payload and every error
are covered by tests that assert this.

---

## `POST /api/v1/chat/query`

The flow, in order:

```
question
  -> AI agent adapter          (backend/app/adapters/agent_loader.py)
  -> governed semantic query   (backend/app/services/query_service.py)
  -> schema validation         (analytics_validation MetricValidator)
  -> warehouse query           (backend/app/adapters/warehouse.py)
  -> result validation         (analytics_validation DataValidator)
  -> structured response
```

`status` is one of `answered`, `ambiguous` or `unsupported`. The last two return
HTTP 200 with an explanation and **no query is executed** — the backend never
falls back to generating SQL from the question text.

### Request

```json
{ "question": "Show total sales by country in 2023" }
```

| Field | Type | Notes |
|---|---|---|
| `question` | string, 3–500 chars | Required |
| `conversation_id` | string, ≤128 chars | Reserved for v1; not used |
| `limit` | int, 1–10000 | Capped by `MAX_RESULT_ROWS` |

Any other field is rejected with `422 request_validation_error`. That is what
makes `{"question": "...", "sql": "SELECT ..."}` impossible to submit.

### Response — `answered`

```json
{
  "status": "answered",
  "answer": "Returned 2 rows of Revenue grouped by Country. The first row is United States with Revenue = 12642905.0.",
  "message": null,
  "ambiguity": { "ambiguous": false, "reason": null, "possible_metrics": [] },
  "data": [
    { "Country": "United States", "Revenue": 12642905.0 },
    { "Country": "Australia", "Revenue": 925000.5 }
  ],
  "evidence": {
    "question": "Show total sales by country in 2023",
    "interpreted_metric": "Sales",
    "governed_metric": "Revenue",
    "metric_formula": "SUM(SALES)",
    "interpreted_dimension": "Country",
    "dimensions": ["Country"],
    "filters": [{ "member": "Year", "operator": "equals", "values": [2023] }],
    "governed_query": {
      "measures": ["Revenue"],
      "dimensions": ["Country"],
      "filters": [{ "member": "Year", "operator": "equals", "values": [2023] }],
      "time_dimensions": [],
      "order_by": [{ "member": "Revenue", "direction": "desc" }],
      "limit": 100
    },
    "source_model": "METRICMIND.MART.FACT_SALES",
    "row_count": 2,
    "agent_output": {
      "question": "Show total sales by country in 2023",
      "metric": "Sales",
      "dimension": "Country",
      "filters": { "Year": 2023 },
      "operation": "total",
      "ambiguity": { "ambiguous": false, "reason": null, "possible_metrics": [] }
    },
    "translation_notes": [
      "Agent metric 'Sales' was interpreted as the governed metric 'Revenue' (SUM(SALES)).",
      "Agent year filter 2023 was applied to the governed 'Year' dimension (fact_sales.YEAR).",
      "Results ordered by Revenue DESC for a deterministic row limit.",
      "Answer text is generated deterministically from the returned rows; no language model is invoked by the current agent implementation."
    ],
    "answer_generation": "deterministic",
    "validation": {
      "is_valid": true,
      "status": "PASS",
      "schema_validation": {
        "is_valid": true,
        "message": "Valid Payload",
        "validator": "MetricValidator.validate_agent_query"
      },
      "data_validation": {
        "status": "PASS",
        "row_count": 2,
        "null_count": 0,
        "invalid_discount_detected": false,
        "negative_sales_detected": false,
        "reason": null,
        "raw": { "status": "PASS", "row_count": 2, "null_count": 0, "invalid_discount_detected": false, "negative_sales_detected": false },
        "validator": "DataValidator.validate_cube_output"
      },
      "errors": [],
      "warnings": [],
      "checks_applied": [
        "MetricValidator.validate_agent_query (Cube payload schema)",
        "DataValidator.validate_cube_output (row count, null count)"
      ],
      "checks_skipped": [
        { "check": "DataValidator discount bounds check (0.0 - 1.0)", "reason": "No result column name contains 'discount'. ..." },
        { "check": "DataValidator non-negative sales check", "reason": "No result column name contains 'sales' outside its blocklist. ..." },
        { "check": "Referential integrity / accepted values", "reason": "No relationships or accepted_values tests exist in the dbt project ..." }
      ],
      "notes": ["..."]
    }
  }
}
```

`evidence` is the payload for the frontend Evidence/Confidence panel: what was
asked, what the agent said, what it was translated into, the exact governed query
that ran, which mart it came from, how many rows came back, and what validation
did and did not check.

### Response — `ambiguous`

```json
{
  "status": "ambiguous",
  "answer": null,
  "message": "'best' does not specify which metric should be used. Please name the metric explicitly.",
  "ambiguity": {
    "ambiguous": true,
    "reason": "'best' does not specify which metric should be used.",
    "possible_metrics": ["Sales", "Profit", "Quantity"]
  },
  "data": [],
  "evidence": { "...": "validation.status is SKIPPED; governed_query is null" }
}
```

### Response — `unsupported`

```json
{
  "status": "unsupported",
  "answer": null,
  "message": "'Discount' is not a governed metric. docs/metric_dictionary.md governs no 'Discount' metric. Discount is a column on the fact table, but the dictionary defines only the eight governed metrics.",
  "data": [],
  "evidence": { "...": "..." }
}
```

### Status codes

| Code | When |
|---|---|
| `200` | Answered, ambiguous, or unsupported — all three are valid outcomes |
| `422` | Malformed request body, or the governed payload failed schema validation |
| `502` | The warehouse returned an error |
| `503` | The warehouse is not configured, or the agent module could not be loaded |
| `504` | The warehouse query exceeded `WAREHOUSE_TIMEOUT_SECONDS` |

---

## `GET /api/v1/metrics` and `/dimensions`

The governed catalogues, served straight from
`backend/app/services/metric_service.py`.

`GET /api/v1/metrics` returns the eight metrics from the metric dictionary —
Revenue, Profit, Profit Margin, Orders, Customers, Quantity Sold, Shipping Cost,
Average Order Value — each with its `formula`, `sql_expression`, `additive`
flag, `catalog_member` and `source_document`. `notes` records the metric set the
AI agent declares instead, including the one genuine conflict: the agent offers
`Discount`, which the dictionary does not govern, and the agent cannot name
`Revenue`, `Profit Margin`, `Orders`, `Customers` or `Average Order Value` at all.

`GET /api/v1/dimensions` returns 17 dimensions. Twelve are governed by the
metric dictionary (the geographic attributes and the time attributes); the other
five — Category, Sub-Category, Product Name, Ship Mode, Order Priority — are
real dbt mart columns that the dictionary does not list, and are returned with
`"governed": false` so the gap stays visible.

---

## `POST /api/v1/validate/query`

Validates a governed query without executing it.

```json
{ "payload": { "measures": ["Revenue"], "dimensions": ["Country"] } }
```

```json
{
  "report": { "is_valid": true, "status": "PASS", "...": "..." },
  "compiled_sql_preview": "SELECT\n    f.COUNTRY AS \"Country\",\n    SUM(f.SALES) AS \"Revenue\"\nFROM METRICMIND.MART.FACT_SALES AS f\nGROUP BY f.COUNTRY\nLIMIT 100",
  "compiled_parameters": []
}
```

The SQL is a *preview of what the payload compiles to*. It is never executed by
this endpoint, and it contains no client text: identifiers come from the
registry, values become `compiled_parameters`.

Note the table name is `FACT_SALES`, not `fact_sales`. dbt model names are
lowercase, and `dbt_project.yml` sets no `quoting` config, so dbt-snowflake
emits unquoted identifiers and Snowflake folds them to uppercase. The compiler
upper-cases the model name for exactly this reason; the uppercase-only
identifier rule in `adapters/warehouse.py` is not relaxed to accommodate it.

## `POST /api/v1/validate/data`

Audits supplied rows with the repository's `DataValidator`.

```json
{ "data": [{ "Sales.Sales": 1500.50, "Sales.Discount": 0.20 }] }
```

`members` optionally renames row keys to Cube-style member names before
auditing. That matters: `DataValidator`'s discount-bounds and negative-sales
checks are name heuristics that only match columns literally containing
`discount` or `sales`, so they do not fire on governed column names like
`Revenue`. When a check cannot apply it is listed under `checks_skipped` with
the reason, rather than being counted as passed.

---

## Architecture

```
backend/
  app/
    main.py                    FastAPI app factory, CORS, exception handlers
    config.py                  pydantic-settings configuration
    api/v1/
      router.py                aggregates the route modules
      routes_health.py         GET /health
      routes_semantic.py       GET /metrics, GET /dimensions
      routes_chat.py           POST /chat/query
      routes_validation.py     POST /validate/query, /validate/data
    schemas/                   pydantic request/response models
    services/
      metric_service.py        the governed registry (8 metrics, 17 dimensions)
      agent_service.py         wraps the AI agent adapter
      query_service.py         translation, compilation, execution, answer text
      validation_service.py    normalises the existing validators
    adapters/
      agent_loader.py          loads "ai agent/" despite the space in its name
      warehouse.py             WarehouseAdapter interface + Snowflake implementation
      cube_client.py           Cube adapter placeholder (reports unconfigured)
    core/
      errors.py                error taxonomy + handlers
      logging.py               correlation ids
  tests/                       no Snowflake credentials required
```

### Swapping the warehouse or the semantic layer

`app/adapters/warehouse.py` defines `WarehouseAdapter`. `SnowflakeWarehouseAdapter`
implements it today; `CubeWarehouseAdapter` is a placeholder that reports itself
unconfigured so no caller can mistake it for working. When Cube.dev lands, the
new adapter implements the same interface and `build_warehouse()` selects it —
**no route, schema or service changes are required**.

`app/services/metric_service.py` is likewise plain data plus lookups
(`GovernedRegistry`). A Cube-backed registry can replace `get_metric_service()`
without touching the API surface.

---

## Testing

### Where the tests live

All backend tests are in `backend/tests/`. Nothing else in the repository tests
this service.

| File | Tests | Covers |
|---|---|---|
| `tests/test_health.py` | 5 | `GET /api/v1/health` and the `/health` alias — status, agent availability, governed counts, and that no credential-shaped value reaches the payload |
| `tests/test_metrics.py` | 8 | `GET /api/v1/metrics` and `GET /api/v1/dimensions` — counts, formulas pinned to `docs/metric_dictionary.md`, additivity flags, the agent/dictionary conflict, each dimension's source model and column |
| `tests/test_chat.py` | 20 | `POST /api/v1/chat/query` end to end — answered, ambiguous and unsupported outcomes, the evidence payload, invalid request bodies, raw-SQL rejection, warehouse `502` and `503` |
| `tests/test_validation.py` | 48 | Agent-output translation, governed-query compilation, validation-result normalisation, and both validation endpoints |

81 tests in total. `tests/conftest.py` holds the fixtures and the fakes, and
contains no tests itself.

### Running the tests

```bash
cd backend
python -m pytest -q
```

A single file, a single test, or a subset by name:

```bash
python -m pytest tests/test_chat.py -q
python -m pytest tests/test_validation.py::test_filter_values_are_bound_parameters_and_never_sql_text -q
python -m pytest -k ambiguous -q
```

Install `backend/requirements.txt` first (step 2 above). The suite needs `pytest`,
`fastapi` and `httpx` (for the in-process test client), plus `jsonschema` and
`pandas` — the latter two because it loads the repository's real validators. Run
it from `backend/`.

`backend/pytest.ini` is the entire configuration:

| Setting | Value | Effect |
|---|---|---|
| `testpaths` | `tests` | A bare `pytest` collects only this suite |
| `pythonpath` | `.` | Puts `backend/` on `sys.path`, so `import app...` and `from tests.conftest import ...` resolve without installing the package |
| `addopts` | `-ra` | Prints a summary of every non-passing test at the end of a run |

There is no `conftest.py` at the repository root — the backend suite is
self-contained. A full run currently reports `2 warnings`; both are third-party
deprecations (`starlette`'s `httpx` shim and an `anyio` alias), not from this
suite.

### Credentials, network, and how the warehouse is replaced

No Snowflake credentials and no network access are required, and none are used:
`snowflake-connector-python` is imported lazily inside
`SnowflakeWarehouseAdapter.execute()`, so the tests never import the driver, and
`TestClient` drives the ASGI app in process — no server is started and no port is
opened. Nothing is mocked at the socket level, and no environment variables are
set: the "unconfigured warehouse" case is produced by constructing the fake with
`configured=False` rather than by removing credentials.

`tests/conftest.py` builds the real application and swaps dependencies through
FastAPI's override mechanism:

```python
app = create_app()
app.dependency_overrides[get_warehouse] = lambda: fake_warehouse
```

`FakeWarehouse` is an in-memory implementation of the same `WarehouseAdapter`
interface (`name = "fake"`), not a mock — there is no `unittest.mock` and no
monkeypatching anywhere in the suite. It records every `QueryPlan` it is asked to
run in `executed_plans`, can report itself unconfigured (`configured=False`), and
can be told to raise on execute (`raises=...`).

Because only the adapter *implementation* is replaced, the tests exercise the
real routes, the real governed registry, the real translation and compilation
logic, and the real `analytics_validation` validators.

| Fixture | Provides |
|---|---|
| `client` | The app with the warehouse faked. The **real** AI agent is used |
| `stub_client` | The app with both the warehouse and the agent faked |
| `unavailable_client` | A warehouse that reports itself unconfigured — the `503` path |
| `failing_client` | A warehouse that raises `WarehouseError` on execute — the `502` path |
| `fake_warehouse` | The `FakeWarehouse` instance, so a test can assert on `executed_plans` |
| `stub_agent` | The `StubAgentAdapter`, returning canned agent output per question |

`stub_client` overrides the agent service as well, which makes agent output
deterministic:

```python
app.dependency_overrides[get_agent_service] = lambda: AgentService(adapter=stub_agent)
```

The split matters. Tests that verify warehouse-side behaviour use `stub_client`;
tests that must prove the real integration works use `client`, so
`test_chat_with_the_real_agent` and `test_real_agent_year_filter_becomes_a_governed_filter`
drive `ai agent/query_builder.py` itself, loaded by file path because the
directory name contains a space. The suite therefore needs the tracked
`ai agent/` directory to be present in the checkout.

### What the tests assert

**The API contracts.** `/health` is asserted to serve the same health payload as
`/api/v1/health`. Without credentials `status` becomes `"degraded"` while the
response is still HTTP `200`. The metric
catalogue returns exactly eight metrics, and each `formula` is asserted
string-for-string against `docs/metric_dictionary.md`, so an accidental edit to a
formula fails the suite. `Profit Margin` and `Average Order Value` are asserted
`additive: false`. The five dimensions the dictionary does not govern are
asserted `governed: false`, and the `MARKET = 'EU'` trap is asserted to be
surfaced in the notes.

**That raw SQL cannot be submitted.** `{"question": ..., "sql": ...}` returns
`422 request_validation_error` with `details[].field == "sql"`, as do `query`,
`measures_raw`, `filters_raw` and `governed_query` — `extra="forbid"` leaves no
smuggling channel. The same is asserted for `POST /validate/query` and
`POST /validate/data`.

**That governed queries are built safely.** A hostile filter value
(`United States' OR 1=1 --`) is asserted to appear in `plan.parameters` and *not*
in `plan.sql` — that single test pins "values are bound, never interpolated".
`in` filters bind one parameter per value (`f.MARKET IN (%s, %s)`) and `contains`
binds `%New York%` rather than inlining it. Unknown measure, dimension, filter
member and `order_by` member each raise `ValidationFailedError` before any SQL is
built, and `validate_identifier` is asserted to reject lowercase names, `;`,
`--`, dotted names, `1=1` and the empty string. The compiled table is qualified
and upper-cased (`METRICMIND.MART.FACT_SALES`), a `dim_product` dimension adds a
`LEFT JOIN`, a `dim_date` dimension casts `ORDER_DATE`, and `LIMIT` is clamped to
`settings.max_result_rows`. The `Sales` → `Revenue` rename and the ordering
decision are asserted to appear in `notes`, so nothing is inferred silently.

**The three chat outcomes.** `answered` carries data, a deterministic answer
string and full evidence. `ambiguous` and `unsupported` return `200` with an
explanation and `data: []`, and the warehouse is asserted never to have been
called (`executed_plans == []`) — no fallback SQL is generated from question
text. The agent's `Discount` metric is asserted to be *refused*, because the
dictionary governs no such metric even though the column exists.

**Error handling.** Every error uses the one envelope
`{"error": {code, message, details, correlation_id}}`. `503 configuration_error`
names the missing settings and returns no `data` key. `502 warehouse_error`
carries the generic message `"The warehouse query failed."` with no driver text.
Error responses carry a non-empty `correlation_id`. The health payload is
asserted not to contain `password`, `snowflake_account`, `account=`, `user=`,
`token` or `secret`, and `warehouse` is asserted to have exactly five keys.

**Validation normalisation.** The existing validators return three incompatible
shapes; the tests assert each normalises into one report, and that an
*unrecognised* shape **fails closed** — a changed validator contract can never be
read as "valid". `checks_applied` versus `checks_skipped` is asserted too:
governed column names do not match `DataValidator`'s name heuristics and the
report must say so, while passing Cube-style member names (`Sales.Discount`)
makes the check fire and produce `FLAGGED`. `combine()` must return the weaker of
two reports. These tests import the private helpers `_normalize_schema_result`
and `_normalize_data_result` deliberately; the module docstring explains that
this is the only way to prove a tuple and a dict converge on the same report
without a warehouse.

### What is not covered

Stated plainly so the suite is not read as broader than it is:

- **No test connects to Snowflake.** `SnowflakeWarehouseAdapter.execute()` and
  `to_json_safe()` are never executed, and nothing asserts that Snowflake accepts
  the compiled SQL.
- **The `504 warehouse_timeout` path has no test.** `WarehouseTimeoutError` and
  its `_is_timeout_error` classification are only reachable with a live
  warehouse, so only `502` and `503` are asserted.
- **`CubeWarehouseAdapter` has no test.** The one Cube-related test asserts the
  *payload shape* that `MetricValidator` validates, not the adapter.
- **`build_warehouse()`'s backend selection is not asserted.**

---

## Known limitations

These are current facts, not aspirations. Each is asserted by a test or reported
by an endpoint.

- **The AI agent is deterministic keyword matching, not an LLM.**
  `ai agent/query_builder.py` has no model call. Answer text is therefore
  generated by a template (`summarize_result`) and every response records
  `evidence.answer_generation = "deterministic"`. No response claims otherwise.
- **`ai agent/validator.py` is not used and must not be.** It always reports
  success: it calls `MetricValidator.validate_agent_query`, which returns a
  `(bool, str)` tuple, then guards the result with `isinstance(result, dict)`, so
  the schema check silently becomes `True`; and it probes `DataValidator` for
  `validate_dataframe` / `validate`, neither of which exists, falling through to
  a hardcoded `{"is_valid": True}`. `validation_service.py` calls the validators'
  real public methods instead. The file was left untouched — it belongs to
  another component.
- **`ai agent/test_agent.py` does not run.** It imports `validate_query`, which
  was removed in commit `dfa7e33`. Left untouched for the same reason.
- **The agent can only reach three governed metrics.** It emits `Sales`,
  `Profit`, `Quantity`, `Discount` and `Shipping Cost`; the first three map to
  governed metrics and `Discount` is refused. `Revenue` is reachable only via the
  agent's `Sales`; `Profit Margin`, `Orders`, `Customers` and `Average Order
  Value` are not reachable through the agent at all.
- **`DataValidator`'s heuristics mostly cannot fire.** See
  `POST /validate/data` above.
- **No `relationships` or `accepted_values` dbt tests exist**, so referential
  integrity is not validated anywhere. It is reported as a skipped check.
- **`conversation_id` is accepted but unused.** Multi-turn context is future work.
