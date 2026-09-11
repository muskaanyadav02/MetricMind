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

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Health, agent status, governed counts, warehouse summary |
| `GET` | `/health` | Alias of the above, for simple local probes |
| `GET` | `/api/v1/metrics` | The governed metric catalogue |
| `GET` | `/api/v1/dimensions` | The governed dimension catalogue |
| `POST` | `/api/v1/chat/query` | Ask a governed business question |
| `POST` | `/api/v1/validate/query` | Validate a governed query payload |
| `POST` | `/api/v1/validate/data` | Audit a set of result rows |

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
