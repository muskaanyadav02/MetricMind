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

If `WAREHOUSE_BACKEND=cube`, the only required setting is `CUBE_API_URL`.
`CUBE_API_TOKEN` is optional: Cube's development mode (`CUBEJS_DEV_MODE=true`,
the default for local `cubejs` and Docker setups) is a documented
authentication bypass, so a local Cube normally accepts requests without a
token. When a token is configured it is sent as the `Authorization` header.
See [The Cube backend](#the-cube-backend) for the full behaviour.

### The Cube backend

Setting `WAREHOUSE_BACKEND=cube` routes chat execution to the Cube.dev
semantic layer (`app/adapters/cube_client.py`) instead of Snowflake. Routes
do not change when the backend switches: both adapters implement the same
`WarehouseAdapter` interface and return the same `QueryResult`, and governed
validation runs identically before either adapter is reached.

**Request path.** `QueryService.compile()` attaches a Cube payload to every
`QueryPlan` (reusing the existing `build_cube_payload()` renderer), and the
adapter POSTs `{"query": ...}` to `{CUBE_API_URL}/load` — Cube's
`/cubejs-api/v1/load` endpoint — with `WAREHOUSE_TIMEOUT_SECONDS` applied as
the HTTP timeout. The payload carries governed member names only; no SQL is
ever sent to Cube, and a plan not produced by the governed compiler is
refused without a request.

**Member mapping.** Governed names are translated to the members of the
deployed Cube model, `cube/model/FactSales.js` (the single `FactSales`
cube), and response keys are translated back to governed names:

| Governed metric | Cube member |
|---|---|
| Revenue | `FactSales.revenue` |
| Profit | `FactSales.profit` |
| Profit Margin | `FactSales.profitMargin` |
| Orders | `FactSales.orders` |
| Customers | `FactSales.customers` |
| Quantity Sold | `FactSales.quantitySold` |
| Shipping Cost | `FactSales.shippingCost` |
| Average Order Value | `FactSales.averageOrderValue` |

| Governed dimension | Cube member |
|---|---|
| Country | `FactSales.country` |
| Region | `FactSales.region` |
| Market | `FactSales.market` |
| Market2 | `FactSales.market2` |
| City | `FactSales.city` |
| State | `FactSales.state` |
| Ship Mode | `FactSales.shipMode` |
| Order Priority | `FactSales.orderPriority` |

Filter operators map as `in` → `equals` and `not_in` → `notEquals` (Cube's
set semantics); `equals`, `contains`, `gt`, `gte`, `lt` and `lte` pass
through unchanged, and `not_equals` maps to `notEquals`.

**Time dimensions.** The model exposes one time member,
`FactSales.orderDate`. The governed time attributes `Year`, `Quarter`,
`Month` and `Day` are expressed as `timeDimensions` granularities
(`year`/`quarter`/`month`/`day`) on that member, and the response key
(`FactSales.orderDate.month`) is renamed back to the governed name. The
same names used as a plain dimension or a filter member are refused — see
[Known limitations](#known-limitations-and-troubleshooting).

**Response normalisation.** Cube returns numbers as strings (documented
Cube behaviour); the adapter parses strictly numeric strings back to
numbers (`"700"` → `700`, `"12.5"` → `12.5`) and leaves everything else —
including leading-zero strings such as order ids — untouched. Every
response key the query asked for is renamed back to its governed name, so
answer summaries, row validation and the chat response shape are identical
over either backend. Response keys the query did not ask for keep their
Cube names.

**Local development.** A local Cube on its default port needs only:

```dotenv
WAREHOUSE_BACKEND=cube
CUBE_API_URL=http://localhost:4000/cubejs-api/v1
```

`localhost:4000` is a *local* service, not a repository component — no Cube
deployment ships in this repository. Leave `CUBE_API_TOKEN` unset for a
dev-mode Cube; set it only if the deployment enforces authentication.

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
| `WAREHOUSE_BACKEND` | `snowflake` | No | `snowflake` (dbt MART tables) or `cube` (Cube.dev semantic layer) |
| `SNOWFLAKE_ACCOUNT` | – | **Yes** (snowflake backend) | Snowflake account identifier |
| `SNOWFLAKE_USER` | – | **Yes** (snowflake backend) | User name |
| `SNOWFLAKE_PASSWORD` | – | **Yes** (snowflake backend) | Password |
| `SNOWFLAKE_ROLE` | – | No | Sent to the driver only when set |
| `SNOWFLAKE_DATABASE` | `METRICMIND` | No | Per `docs/data_dictionary.md` |
| `SNOWFLAKE_SCHEMA` | `MART` | No | The dbt mart schema |
| `SNOWFLAKE_AUTHENTICATOR` | – | No | Optional; omit for username/password (e.g. `externalbrowser`, `snowflake_jwt`, `oauth`) |
| `CUBE_API_URL` | – | **Yes** (cube backend) | Cube REST API base, e.g. `http://localhost:4000/cubejs-api/v1` for a local deployment (local-only; see [The Cube backend](#the-cube-backend)) |
| `CUBE_API_TOKEN` | – | No | Sent as the `Authorization` header when set; optional because dev-mode Cube (the common local setup) is a documented authentication bypass |

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
  only partially with the governed registry — see
[Known limitations and troubleshooting](#known-limitations-and-troubleshooting).
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
| `500` | Any endpoint — an unhandled exception (`internal_error`). The message is generic and the exception detail stays server-side, in the log line carrying the same `correlation_id` |
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

The same id is returned in the `X-Correlation-ID` header on every response, so a
client can quote it without parsing the body; an id supplied on the request in
that header is adopted rather than replaced. One gap, recorded in the test
rather than fixed: on an unhandled `500` the middleware never sees a response,
so the header is not echoed — the id is still in the body and in the server log,
so traceability holds. Every route's documented response models and error
statuses are contract-tested in `tests/test_openapi_contract.py`.

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
| `500` | An unhandled exception. The message is generic; the detail stays in the server log under the same `correlation_id` |
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

## Project structure

Everything the backend owns is under `backend/`. This is the complete Python
source tree — if a file is not listed here, it does not exist. Each entry is a
pointer; deeper behaviour is described in
[Architecture and request flow](#architecture-and-request-flow),
[Configuration](#configuration) and [Testing](#testing).

```text
backend/
├── .env.example                  Placeholder environment variables (copy to backend/.env)
├── pytest.ini                    Test configuration: testpaths, pythonpath, addopts
├── requirements.txt              Runtime and test dependencies
├── app/
│   ├── main.py                   create_app(): logging, CORS, correlation-id middleware,
│   │                             error handlers, v1 router, /health alias
│   ├── config.py                 Settings from environment/backend/.env (cached, never
│   │                             validated at load time)
│   ├── api/
│   │   └── v1/
│   │       ├── router.py              Combines the four route modules under /api/v1
│   │       ├── routes_health.py       GET /api/v1/health
│   │       ├── routes_semantic.py     GET /api/v1/metrics, GET /api/v1/dimensions
│   │       ├── routes_chat.py         POST /api/v1/chat/query
│   │       └── routes_validation.py   POST /api/v1/validate/query, POST /api/v1/validate/data
│   ├── schemas/                  Public request/response contracts (Pydantic)
│   │   ├── common.py             Error envelope + health payloads
│   │   ├── chat.py               Chat request/response; extra="forbid" blocks unknown fields
│   │   ├── semantic.py           Metric/dimension catalogues + GovernedQuery (names, never SQL)
│   │   └── validation.py         ValidationReport, the single normalised validation shape
│   ├── services/                 Business logic (no I/O)
│   │   ├── agent_service.py      Normalises the local agent's output
│   │   ├── metric_service.py     Governed registry from the repository dictionaries + dbt marts
│   │   ├── query_service.py      Translation -> compilation -> execution -> answer formatting
│   │   └── validation_service.py Calls the repo's validators, normalises their result shapes
│   ├── adapters/                 External-world I/O, behind interfaces
│   │   ├── agent_loader.py       Loads the ai agent/ modules by file path (dir name has a space)
│   │   ├── warehouse.py          WarehouseAdapter interface, backend selection, Snowflake execution
│   │   └── cube_client.py        Cube REST adapter: governed queries -> /cubejs-api/v1/load
│   └── core/
│       ├── errors.py             Error classes + handlers -> one envelope for every endpoint
│       └── logging.py            Logging setup and request correlation ids
└── tests/
    ├── conftest.py               Fixtures and fakes (FakeWarehouse, StubAgentAdapter); no tests
    ├── test_health.py            Health endpoint
    ├── test_metrics.py           Metric/dimension catalogues
    ├── test_chat.py              Chat endpoint, end to end
    ├── test_cube_adapter.py      Cube adapter with mocked HTTP — mapping, errors, e2e
    ├── test_validation.py        Translation, compilation, validation normalisation
    └── test_openapi_contract.py  Generated OpenAPI schema contract

(Each package directory also holds an `__init__.py`. The per-test coverage
table is in [Testing](#testing).)
```

---

## Architecture and request flow

### Current backend layers

The running backend is a synchronous FastAPI application assembled by
`app/main.py`. `create_app()` loads cached environment configuration, configures
logging and CORS, installs correlation-id middleware and the shared exception
handlers, then mounts the v1 router under `API_V1_PREFIX` (default `/api/v1`).
Importing the application does not open a warehouse connection.

```text
HTTP request
  -> FastAPI app (`app/main.py`): CORS, correlation id, error envelope
  -> API router (`app/api/v1/`): request parsing and endpoint orchestration
  -> Pydantic schemas (`app/schemas/`): public request/response contracts
  -> services (`app/services/`): registry, translation, compilation, validation
  -> adapters (`app/adapters/`): local agent loading or warehouse I/O
       -> `ai agent/` deterministic query builder
       -> Snowflake dbt MART tables or Cube /load (chat execution only)
  -> Pydantic response -> HTTP response

Validation service -> `analytics_validation/validation/`
Cube adapter       -> POST {CUBE_API_URL}/load (WAREHOUSE_BACKEND=cube)
```

The layers implemented today are:

- **API/router:** `api/v1/router.py` combines the health, semantic catalogue,
  chat and validation route modules. Route functions use `Depends(...)` to
  obtain services, adapters, the governed registry and settings; they contain
  orchestration rather than warehouse-specific code.
- **Schemas:** `schemas/common.py`, `chat.py`, `semantic.py` and `validation.py`
  define Pydantic request, response, catalogue, governed-query and validation
  contracts. Request models forbid unknown fields, so clients cannot submit raw
  SQL through an extra key.
- **Services:** `metric_service.py` owns the in-process registry sourced from the
  repository dictionaries and dbt marts. `agent_service.py` normalises the local
  agent output. `query_service.py` translates agent output, compiles governed
  queries, executes compiled plans and formats deterministic answer text.
  `validation_service.py` calls and normalises the existing validators.
- **Adapters/infrastructure:** `agent_loader.py` loads the non-package
  `ai agent/` modules by file path. `warehouse.py` defines `WarehouseAdapter`,
  selects a backend, compiles safe qualified identifiers and implements actual
  Snowflake execution. `cube_client.py` implements the same interface against
  Cube's REST API: it translates the plan's governed payload to `FactSales.*`
  members and POSTs it to `{CUBE_API_URL}/load`.
- **Core configuration, logging and errors:** `app/config.py` reads and caches
  environment-backed settings without connecting to a dependency.
  `core/logging.py` configures logging and request correlation ids.
  `core/errors.py` maps application, Pydantic, HTTP and unexpected exceptions to
  the common error envelope; sensitive warehouse exceptions remain server-side.
- **AI agent integration:** the current `ai agent/query_builder.py` is a local,
  deterministic keyword matcher, not an LLM. Its dictionary is preserved as
  evidence, then explicitly mapped onto the governed registry by
  `translate_agent_output()`; it neither compiles nor executes SQL itself.
- **Warehouse integration:** the active implementation is direct Snowflake
  access to dbt `MART` models through `SnowflakeWarehouseAdapter`. A connection
  is attempted only by chat execution. The adapter executes only a `QueryPlan`
  produced by the governed compiler and converts warehouse-native values for
  JSON responses.
- **Validation integration:** `validation_service.py` loads
  `analytics_validation/validation/metric_validation.py` and
  `data_validation.py` by file path. It calls their actual public methods and
  normalises their differing result shapes into `ValidationReport`; it does not
  use `ai agent/validator.py`.

### Dependency injection and adapter boundaries

FastAPI dependency injection is used at route and service boundaries. For
example, `chat_query()` receives `AgentService`, `QueryService`,
`ValidationService` and `Settings`; `get_query_service()` in turn receives a
`WarehouseAdapter`, `GovernedRegistry` and `Settings`. `get_warehouse()` calls
`build_warehouse()` to select the Snowflake or Cube backend. Health routes
also depend directly on the agent, registry, settings and warehouse interface.
The catalogue routes depend only on the registry, while `/validate/data`
depends only on the validation service.

This separation is exercised by tests: `app.dependency_overrides` replaces
`get_warehouse` with an in-memory `FakeWarehouse` and can replace
`get_agent_service` with a stub, while the real routes, schemas, services,
compiler and validation integration continue to run.

### Endpoint request/data flows

#### `GET /api/v1/health`

1. FastAPI resolves `AgentService`, the selected `WarehouseAdapter`, the shared
   `GovernedRegistry` and `Settings`.
2. The route checks whether the local agent module loads and whether the selected
   warehouse reports itself configured. This is a configuration/readiness check;
   it does not connect to Snowflake.
3. It returns agent vocabulary, safe warehouse metadata and registry counts.
   The status is `ok` only when both agent and warehouse are usable; otherwise it
   is `degraded`. `/health` calls the same response builder.

#### `GET /api/v1/metrics` and `GET /api/v1/dimensions`

1. FastAPI injects the process-wide `GovernedRegistry`.
2. The routes read the in-memory metric or dimension definitions and governance
   notes from `metric_service.py`.
3. Pydantic serialises the catalogue response. No agent, validator or warehouse
   is called.

#### `POST /api/v1/chat/query`

```text
ChatQueryRequest
  -> AgentService -> LocalAgentAdapter -> `ai agent/query_builder.py`
  -> AgentInterpretation
  -> translate_agent_output() + GovernedRegistry
       -> ambiguous/unsupported response, with no execution; OR
       -> GovernedQuery
  -> ValidationService.validate_governed_query()
       -> Cube-shaped payload -> MetricValidator (schema check only)
  -> QueryService.execute()
       -> compile_governed_query() -> parameterised QueryPlan
       -> WarehouseAdapter.require_configured()
       -> WarehouseAdapter.execute()
            (Snowflake: parameterised SQL against the dbt MARTs, or
             Cube: POST {CUBE_API_URL}/load with FactSales.* members)
  -> ValidationService.validate_rows() -> DataValidator
  -> combine validation reports + deterministic result summary
  -> ChatQueryResponse with rows and supporting evidence
```

The request body is first validated as `ChatQueryRequest`; unknown keys and
invalid question/limit values fail before the handler runs. The agent adapter
returns its rule-based interpretation unchanged, and `AgentService` extracts a
normalised view. `translate_agent_output()` then checks that the interpreted
metric, optional dimension and operation can be represented by the registry. It
records aliases and other translation decisions, builds a `GovernedQuery`, or
returns an `ambiguous`/`unsupported` outcome without calling the warehouse.

For an executable query, `MetricValidator` validates the governed query rendered
in Cube's payload shape. This validates payload structure; it neither proves that
Cube is running nor executes a query. The compiler separately resolves every
measure, dimension, filter and ordering member against the registry, adds the
required dbt-mart joins, validates SQL identifiers, binds filter values as
parameters and clamps the limit. The compiler also attaches a Cube payload
(from `build_cube_payload()`) to the plan for the Cube backend; the governed
`order_by` and `limit` are compiled into the SQL but are not part of that
payload (see [Known limitations](#known-limitations-and-troubleshooting)).
`QueryService.execute()` then checks warehouse
configuration and sends that compiled `QueryPlan` to the selected adapter.
Both adapters can return rows: Snowflake runs the parameterised SQL; Cube
translates and POSTs the payload.

Returned rows are audited with `DataValidator`; schema and data reports are
combined but a flagged data report does not discard the rows. The endpoint
builds deterministic answer text and returns the rows plus evidence containing
the agent output, governed query, source model, translation notes and validation
report.

#### `POST /api/v1/validate/query`

1. Pydantic parses `ValidateQueryRequest`, including its `GovernedQuery` payload.
2. `ValidationService` renders the payload in Cube-style shape and invokes
   `MetricValidator.validate_agent_query`, then normalises its result.
3. Only when that report is valid, `QueryService.compile()` resolves registry
   members and returns a parameterised SQL preview. A registry/compilation error
   changes the report to `FAIL`.
4. The endpoint returns the report, SQL preview and parameters. It never calls
   `WarehouseAdapter.require_configured()` or `execute()`, so it requires no
   warehouse credentials and performs no warehouse I/O.

#### `POST /api/v1/validate/data`

1. Pydantic parses rows and optional member names as `ValidateDataRequest`; an
   empty row list returns a failed report immediately.
2. `ValidationService.validate_rows()` optionally maps row keys to the supplied
   Cube-style member names, then passes only those supplied rows to
   `DataValidator.validate_cube_output` and normalises the result.
3. The response states which heuristic checks ran or were skipped. It neither
   compiles a query nor reads from the warehouse.

### Validation versus compilation and execution

These are separate operations in the current code:

| Operation | Current implementation | Warehouse access? |
|---|---|---|
| Query schema validation | `ValidationService.validate_governed_query()` renders a `GovernedQuery` as a Cube-shaped dictionary and calls `MetricValidator` | No |
| Query compilation | `QueryService.compile()` / `compile_governed_query()` resolves registry definitions and produces parameterised Snowflake SQL in a `QueryPlan` | No |
| Warehouse execution | `QueryService.execute()` compiles, checks configuration and calls `WarehouseAdapter.execute()`; the selected adapter performs the access — Snowflake runs the parameterised SQL, Cube POSTs the payload to `/load` | **Yes** |
| Data/result validation | `ValidationService.validate_rows()` calls `DataValidator` on rows already returned by chat or supplied to `/validate/data` | No additional access |

Consequently, `/validate/query` validates and compiles but does not execute;
`/validate/data` validates caller-supplied rows but does not compile or execute;
and `/chat/query` is the only documented endpoint that performs all three stages
and can access Snowflake or Cube.

### Current implementation and placeholders

- **Current:** FastAPI, the in-process governed registry, deterministic local
  agent, governed Snowflake SQL compiler, the Snowflake adapter, the Cube REST
  adapter (`app/adapters/cube_client.py`, selected with
  `WAREHOUSE_BACKEND=cube`), and the two validators under
  `analytics_validation/validation/`.
- **External to the repository:** a running Cube. `cube/` contains the model
  (`cube/model/FactSales.js`) and its README; no Cube server ships here, so a
  Cube deployment (local or hosted) is a prerequisite the team provides. The
  catalogue's member names (`Sales.Revenue`, `Sales.Country`) still differ
  from the model's member names (`FactSales.revenue`,
  `FactSales.country`); the adapter maps between the two vocabularies at
  execution time.
- **Future seam, not current behavior:** the `GovernedRegistry` is static
  in-process data; there is no Cube-backed registry today.

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
| `tests/test_cube_adapter.py` | 29 | The Cube adapter with `httpx` fully mocked — governed-to-`FactSales.*` member/operator/timeDimension mapping, response key renaming and string-number parsing, `Authorization` header only when a token is configured, HTTP/connect/timeout/malformed-response mapping to the structured errors, refusal of unmappable members before any request, and the chat endpoint end to end over Cube |
| `tests/test_validation.py` | 48 | Agent-output translation, governed-query compilation, validation-result normalisation, and both validation endpoints |
| `tests/test_openapi_contract.py` | 15 | The generated OpenAPI schema — that each route documents its real response model, that every declared non-`200` response with a JSON body uses the one error envelope, that the chat endpoint names all seven of its documented error codes, and that a handled error echoes the correlation id in both the header and the body |

125 tests in total. The count is of *collected* tests, so a parametrised case
counts once per case — `tests/test_openapi_contract.py` holds 12 test functions,
three of which are parametrised. `tests/conftest.py` holds the fixtures and the
fakes, and contains no tests itself.

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

**That the published API docs match the code.** `tests/test_openapi_contract.py`
reads `app.openapi()` rather than making requests, so a failure there means the
interactive docs disagree with the routes. Every route's `200` is asserted to
name its real response model (`HealthResponse`, `ChatQueryResponse`,
`ValidateQueryResponse`, …), and every declared non-`200` status that documents
a JSON body is asserted to resolve to `ErrorResponse` rather than an ad-hoc
shape. A fixed set of seven codes is asserted to be named in the chat endpoint's
documented descriptions (`request_validation_error`, `validation_failed`,
`warehouse_error`, `agent_error`, `configuration_error`, `agent_unavailable`,
`warehouse_timeout`), so typo'ing one out of a route description fails the suite
here rather than in the published docs. The envelope's own schema is pinned too
— `ErrorBody` requires exactly `code` and `message`. Correlation-id
echoing is asserted for a *handled* error: a `503` must carry both the
`X-Correlation-ID` header and the body id. The unhandled-`500` case asserts the
body id is present and records in a comment that the header is not echoed — a
known gap that is documented rather than fixed, and whose absence is not itself
asserted.

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
- **The Snowflake `504 warehouse_timeout` path has no test.** The Cube
  adapter's timeout → `WarehouseTimeoutError` mapping *is* tested with mocked
  `httpx` timeouts, but Snowflake's `_is_timeout_error` classification is
  only reachable with a live warehouse.
- **No test connects to a real Cube.** Every Cube interaction is mocked with
  `httpx.MockTransport`; nothing asserts that a live deployment accepts the
  generated payload.

---

## Known limitations and troubleshooting

These are current facts about the implementation, not aspirations. Every
limitation below is asserted by a test or reported by an endpoint, and every
troubleshooting step uses only mechanisms the code actually has.

### Warehouse and Snowflake configuration

The Snowflake backend needs all four of `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`,
`SNOWFLAKE_PASSWORD` and `SNOWFLAKE_WAREHOUSE` (see
[Configuration](#configuration) for the full reference).

When credentials are missing:

- The service starts normally and every endpoint except `chat/query` works.
- `GET /api/v1/health` reports `"status": "degraded"` with
  `warehouse.configured: false`; `warehouse.missing_settings` names the missing
  settings (names only, never values).
- `POST /api/v1/chat/query` returns `503` with code `configuration_error` and a
  message listing the same missing settings. No sample or fake data is ever
  substituted for a real result.

Two things `warehouse.configured: true` does **not** mean:

- It is a *presence* check only (`Settings.warehouse_configured`). It does not
  prove the credentials are correct or that Snowflake is reachable — the first
  real connection happens inside chat execution.
- It does not prove the selected backend is reachable. With
  `WAREHOUSE_BACKEND=cube`, `CUBE_API_URL` being set is enough for `ok` —
  health never contacts Cube, so a stopped Cube service still reports `ok`
  until the first chat query fails with `502 warehouse_error` (see below).

### Cube integration

The Cube backend is implemented (`app/adapters/cube_client.py`): with
`WAREHOUSE_BACKEND=cube` it POSTs governed payloads to `{CUBE_API_URL}/load`
(see [The Cube backend](#the-cube-backend)). Its limits are the deployed
model's limits — `cube/model/FactSales.js` defines one cube, `FactSales`,
and the adapter refuses anything the model cannot express rather than
querying the wrong member:

- **Not every governed dimension exists in the model.** `Week Number` and
  `Month Name` have no `FactSales` member; a query naming them returns
  `502 warehouse_error` before any request is sent.
- **Governed time attributes work only inside `timeDimensions`.** `Year`,
  `Quarter`, `Month` and `Day` map to `FactSales.orderDate` granularities,
  but the same names as a plain group-by dimension or a filter member are
  refused with `502`. Questions the agent translates into a `Year` filter —
  e.g. "Show total sales by country in 2023" — therefore work on Snowflake
  and fail on Cube until the model gains that mapping.
- **Ordering and row limits are not carried in the Cube payload.** The
  governed `order_by` and `limit` are compiled into the Snowflake SQL only;
  over Cube, row order and row count follow Cube's defaults, and
  `MAX_RESULT_ROWS` is enforced in the Snowflake SQL, not on the Cube path.
- **Cube errors and outages surface as `502 warehouse_error` (or `504
  warehouse_timeout`)** with generic messages; the HTTP status, response
  excerpt or connection error goes to the server log under the correlation
  id. A token is never included in a client-facing message.
- **There is no Cube-backed registry or liveness check.** `GET /metrics` and
  `/dimensions` come from the static governed registry, and health never
  contacts Cube.

### Chat/query limitations

- **Ambiguous and unsupported questions are `200`, not errors.** `status` is
  `ambiguous` or `unsupported` with an explanation, `data: []`, and the warehouse
  is never called. A `200` from `chat/query` therefore means the request was
  handled, not that a warehouse query ran — check `status` and `data` to tell the
  two apart. Only `status: "answered"` means rows were actually returned from
  Snowflake.
- **No fallback SQL generation.** When the question cannot be mapped onto the
  governed registry, the backend never invents SQL from the question text.
- **The agent can only reach three governed metrics.** It emits `Sales`,
  `Profit`, `Quantity`, `Discount` and `Shipping Cost`; the first three map to
  governed metrics and `Discount` is refused. `Revenue` is reachable only via the
  agent's `Sales`; `Profit Margin`, `Orders`, `Customers` and `Average Order
  Value` are not reachable through the agent at all.
- **The AI agent is deterministic keyword matching, not an LLM.**
  `ai agent/query_builder.py` has no model call. Answer text is generated by a
  template and every response records
  `evidence.answer_generation = "deterministic"`.
- **`conversation_id` is accepted but unused.** Multi-turn context is future
  work.

### Validation limitations

- **`/validate/query` compiles, it never executes.** A `PASS` report and an SQL
  preview mean the payload is registry-valid and compiles to parameterised SQL —
  not that the warehouse accepted it. Nothing in this repository proves Snowflake
  accepts the compiled SQL (see [Testing](#testing), "What is not covered").
- **`/validate/data` audits only the rows you send.** It reads no warehouse. Its
  discount-bounds and negative-sales checks are column-name heuristics that only
  fire on names containing `discount` or `sales`; on governed names like
  `Revenue` they are listed under `checks_skipped` with the reason rather than
  counted as passed.
- **No `relationships` or `accepted_values` dbt tests exist**, so referential
  integrity is not validated anywhere. It is reported as a skipped check.
- **`ai agent/validator.py` is not used and must not be.** It always reports
  success regardless of input (a type-guard bug makes the schema check silently
  `True` and it falls through to a hardcoded `{"is_valid": True}`).
  `validation_service.py` calls the validators' real public methods instead. The
  file was left untouched — it belongs to another component.
- **`ai agent/test_agent.py` does not run.** It imports `validate_query`, which
  was removed in commit `dfa7e33`. Left untouched for the same reason.

### Common API errors and what to do about them

Every failure uses the one envelope shown in
[Status codes across all endpoints](#status-codes-across-all-endpoints). The
practical reading of each:

| Status | `code` | What it means | First thing to check |
|---|---|---|---|
| `422` | `request_validation_error` | The payload was malformed or contained an unknown field (`details[].field` names it) | Compare against the request example in the endpoint's section. If you were trying to send SQL: there is no field for it, by design |
| `422` | `validation_failed` | A governed query referenced a member the registry does not know, or failed schema validation | Check the member names against `GET /api/v1/metrics` and `/api/v1/dimensions` |
| `500` | `internal_error` | An unhandled exception. The message is generic; detail stays in the server log | Quote the `correlation_id` from the response body and search the server log. Note: on an unhandled 500 the `X-Correlation-ID` *header* is not echoed — the id is still in the body and the log |
| `502` | `warehouse_error` | The warehouse failed while running the compiled plan: Snowflake driver errors (wrong credentials, missing grants), or Cube — HTTP error status, refused connection, malformed response, or a governed member the deployed Cube model does not define | Check `WAREHOUSE_BACKEND`: for Snowflake re-check the Snowflake settings; for Cube confirm the service is running and read the server log under the correlation id — the response never contains Cube's error detail or a token |
| `502` | `agent_error` | The agent module loaded but failed to interpret the question | Try rephrasing the question with a governed metric name |
| `503` | `configuration_error` | Warehouse settings are missing — Snowflake credentials for the Snowflake backend, or `CUBE_API_URL` for the Cube backend | Check `warehouse.missing_settings` in `/api/v1/health`; it names the exact missing setting |
| `503` | `agent_unavailable` | The `ai agent/` module could not be loaded | Verify the tracked `ai agent/` directory exists in the checkout |
| `504` | `warehouse_timeout` | The query exceeded `WAREHOUSE_TIMEOUT_SECONDS` (default 30) — the Snowflake statement timeout or the Cube HTTP timeout | Raise `WAREHOUSE_TIMEOUT_SECONDS`, or make the query cheaper (lower `limit`, fewer dimensions) |
| `404` | `http_error` | Unknown path or method | Check the path against the [Endpoints](#endpoints) table |

Two absent statuses, stated so nobody hunts for them: no route returns `400` —
the `bad_request` code exists in `app/core/errors.py` but nothing raises it, so
malformed requests are always `422`; and `agent_unavailable`/`warehouse_timeout`
are `chat/query`-only, like all 502/503/504 codes.

### Troubleshooting workflow

1. **Check health:** `curl http://localhost:8000/api/v1/health`. Read `status`,
   `agent_available` and `warehouse.missing_settings`. Remember `degraded` is the
   expected local state without Snowflake — the service itself is fine.
2. **Verify configuration:** compare `backend/.env` against the required-variables
   table in [Configuration](#configuration). Restart the server after editing —
   settings are read once at process start and cached. For
   `WAREHOUSE_BACKEND=cube`, confirm `CUBE_API_URL` is set and the service
   answers: a stopped Cube shows as `502 warehouse_error` at query time, not
   in health.
3. **Check the payload:** reproduce the request in Swagger UI
   (<http://localhost:8000/docs>). A `422` there, with `details[].field`, is a
   payload problem, not an environment problem.
4. **Follow the correlation id:** every response carries `X-Correlation-ID`, and
   every error body repeats it. Search the server log for that id to see the full
   server-side detail that responses deliberately omit.
5. **Inspect without executing:** `POST /api/v1/validate/query` returns the
   compiled SQL preview and bound parameters without touching the warehouse —
   useful to confirm what `chat/query` *would* run.
6. **Run the test suite** (`python -m pytest -q` from `backend/`). All 125 tests
   passing means the failure is in your environment or configuration, not the
   backend code. See [Testing](#testing).

### Production considerations

The current backend is a development service. Before production use it would
need, and today lacks, all of the following — none of these exist in the code:

- **Authentication and authorization.** No API keys, tokens, sessions or user
  identity on any route; every endpoint is callable by anyone who can reach the
  server.
- **Rate limiting and request quotas.** None.
- **Production deployment configuration.** `uvicorn --reload` is a development
  server; there is no multi-worker, TLS or reverse-proxy guidance built in, and
  `DEBUG` defaults to `false` but no hardened mode exists.
- **A live warehouse health check.** `/api/v1/health` never connects to Snowflake or Cube;
  it reports configuration presence, not warehouse liveness.
- **CORS hardening.** The defaults (`localhost:3000`, `localhost:5173`) are
  development origins; `CORS_ALLOW_ORIGINS` must be set explicitly for a real
  deployment.

What the code *does* already give a production deployment: one consistent error
envelope with correlation ids, parameterised SQL with identifiers restricted to
the governed registry, and error messages that never contain credential values —
all asserted by the test suite.
