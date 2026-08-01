# Conversational BI — Agent Context

This file is the canonical project context for AI coding agents. Read it before making changes.

## Project overview

**Conversational BI** is a multi-tenant, agentic platform that lets users ask natural-language questions against connected data sources and receive structured JSON responses (data + chart recommendations) for visualization.

- **Current scope**: Python backend MVP + React/Vite frontend GUI with Playwright e2e tests.
- **Core flow**: User message → LangGraph agent (schema retrieval → query generation → validation → execution → response formatting) → `QueryResponse` JSON.
- **Tenant model**: Organization → Project → DataSource, with users and RBAC memberships.

## Tech stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ (backend), TypeScript (frontend) |
| API | FastAPI, Uvicorn |
| Frontend | React 19, Vite 8, React Router, Recharts |
| E2E tests | Playwright (`frontend/e2e/`) |
| ORM / DB | SQLAlchemy 2 (async), asyncpg, Alembic migrations |
| Auth | JWT (python-jose), passlib/bcrypt, Authlib (OIDC hooks) |
| Cache / queue | Redis, Celery |
| Agent / LLM | LangGraph, LangChain, LangSmith tracing |
| LLM providers | Google Gemini (default), OpenAI, Anthropic — via `app/llm/factory.py` |
| Data connectors | PostgreSQL, MySQL, MongoDB, Elasticsearch |
| SQL safety | sqlparse + keyword blocklists in `app/execution/guardrails.py` |
| Config | Pydantic Settings (`app/config.py`, `.env`) |
| Linting | Ruff (line length 100, target py311) |
| Packaging | Hatch (`pyproject.toml`) |
| Containers | Docker Compose (`backend/docker/`) |

## Repository layout

```
/
├── AGENTS.md              # This file — agent project context
├── README.md              # Human quick start
├── docs/
│   ├── architecture.md    # Mermaid diagrams (high/low level)
│   └── decisions.md       # Architecture decision record
└── backend/
    ├── app/
    │   ├── api/v1/        # REST endpoints (auth, projects, datasources, conversations, locales)
    │   ├── agents/        # LangGraph query agent (graph, nodes, prompts, state)
    │   ├── connectors/    # DataSourceConnector protocol + dialect plugins
    │   ├── core/          # security, RBAC, tenancy, encryption
    │   ├── execution/     # executor, guardrails, pool manager
    │   ├── i18n/          # Locale resolution + JSON translations (en, fr, de, es, hi, zh)
    │   ├── llm/           # LLM provider factory
    │   ├── models/        # SQLAlchemy models
    │   ├── services/      # Business logic (conversation, datasource, schema, audit, cache)
    │   └── workers/       # Celery tasks (schema refresh)
    ├── alembic/           # DB migrations
    ├── tests/
    │   ├── unit/          # Fast, isolated logic tests
    │   └── integration/   # API-level tests (ASGI client)
    ├── docs/              # API, JSON contract, audit partitioning
    ├── docker/            # Dockerfile + docker-compose.yml
    └── pyproject.toml
└── frontend/
    ├── src/               # React SPA (api client, pages, components)
    ├── widget/            # Embeddable React package (conversational-bi-widget)
    ├── e2e/               # Playwright tests with API mocks
    └── package.json
```

Run backend commands from `backend/` and frontend commands from `frontend/` unless noted otherwise.

## Development setup

```bash
cd backend
cp .env.example .env
docker compose -f docker/docker-compose.yml up -d postgres redis
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Health check: `GET /health` (no auth)

### Frontend setup

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

- GUI: http://localhost:5173 (proxies `/api` to backend in dev)
- E2E tests: `npm run test:e2e` (mocks backend API; no live services required)

### Required environment variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Platform PostgreSQL (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Redis for cache, rate limits, Celery |
| `SECRET_KEY` | JWT signing |
| `ENCRYPTION_KEY` | Fernet key for datasource credentials |
| `GEMINI_API_KEY` | Default LLM (when `LLM_PROVIDER=google`) |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing |

See `backend/.env.example` and `README.md` for the full list.

## Code practices

### General

- **Minimize scope**: Focused diffs; do not refactor unrelated code.
- **Match existing style**: async SQLAlchemy sessions, Pydantic v2 schemas, dataclasses in connectors, FastAPI routers per resource.
- **Read before writing**: Check neighboring modules for naming, patterns, and error handling.
- **Security first**: All queries must remain read-only; never bypass guardrails or RBAC checks.

### Python conventions

- Use `async`/`await` for DB and HTTP I/O.
- Settings via `app.config.settings` (Pydantic `BaseSettings`).
- API routes under `app/api/v1/`; mount via `api_router` with prefix `/api/v1`.
- Business logic in `app/services/`, not in route handlers.
- New connectors implement `DataSourceConnector` protocol in `app/connectors/base.py` and register in `app/connectors/registry.py`.

### Database migrations

- Create Alembic revisions in `backend/alembic/versions/`.
- Run `alembic upgrade head` after pulling migration changes.
- Platform metadata DB is separate from customer datasource connections.

### Agent / LLM changes

- LangGraph pipeline: `retrieve_schema` → `generate_query` → `validate_query` → `execute_query` → `format_response`.
- Dialect-specific prompts live in `app/agents/prompts/` (`system_sql.md`, `system_elasticsearch.md`).
- Agent state is `AgentState` TypedDict in `app/agents/state.py`.
- LLM output must conform to `QueryResponse` contract (`backend/docs/json-response-contract.md`).

### i18n

- Supported locales: `en`, `fr`, `de`, `es`, `hi`, `zh`.
- Translation strings in `app/i18n/translations/<locale>.json`.
- Use `app.i18n.t()` for user-facing messages; resolve locale via `Accept-Language` or user preference.

### Frontend conventions

- TypeScript types in `frontend/src/types/api.ts` mirror backend Pydantic schemas and `QueryResponse` contract.
- API client in `frontend/src/api/client.ts`; JWT stored in `localStorage` via `frontend/src/utils/storage.ts`.
- Pages use React Router; protected routes wrapped in `ProtectedRoute`.
- Chart rendering branches on `visualization.chart_type` in `QueryResult` component.
- Conversation list is client-side (`localStorage`) until a backend list endpoint exists.
- `data-testid` attributes on interactive elements for Playwright e2e tests.
- **Embed widget**: `frontend/widget/` publishes `conversational-bi-widget` — a scoped React component (`ConversationalBIWidget`) for third-party apps. Props: `apiBaseUrl`, `accessToken`, `projectId`, `datasourceId`, optional `conversationId`. Styles are prefixed `.cbi-widget`. Build with `cd frontend/widget && npm run build`.

## Testing

### Running tests

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend e2e
cd frontend
npx playwright install chromium
npm run test:e2e
```

- Pytest config: `asyncio_mode = "auto"` in `pyproject.toml`.
- Dev dependencies: `pip install -e ".[dev]"` (pytest, pytest-asyncio, httpx, ruff).

### Test types and strategies

| Type | Location | Purpose | Strategy |
|------|----------|---------|----------|
| **Unit** | `tests/unit/` | Pure logic, no external services | Test guardrails, connectors' `validate_query`, i18n helpers, encryption utilities. Use plain `pytest` classes/functions; mock external deps when needed. |
| **Integration** | `tests/integration/` | API wiring | Use `httpx.AsyncClient` with `ASGITransport(app=app)` against the FastAPI app. Test health, auth flows, and endpoint contracts. |
| **E2E** | `frontend/e2e/` | GUI flows | Playwright with route-mocked API. Cover auth, projects, datasources, conversations (positive, negative, edge cases). |

### What to test

- **Always test**: Security guardrails (SQL injection patterns, DDL/DML blocking, table allowlists), connector validation, RBAC edge cases when touching auth.
- **Prefer unit tests** for new pure functions and validation logic.
- **Add integration tests** when adding or changing API endpoints.
- **Do not require** live Postgres/Redis/LLM for unit tests; integration tests currently use in-process ASGI (no docker dependency for `test_health`).

### What not to add

- Trivial tests that only assert constants or obvious behavior.
- Tests that call real LLM APIs in CI (mock or skip).
- Tests that mutate customer databases.

## Architecture constraints

Agents and contributors must respect these boundaries:

1. **Read-only queries only** — SELECT / aggregation pipelines; block INSERT, UPDATE, DELETE, DDL, and dangerous DSL operations.
2. **Multi-tenancy** — Enforce `org_id` / `project_id` scoping; namespace Redis cache keys per tenant.
3. **Encrypted secrets** — Datasource credentials stored with Fernet (`app/core/encryption.py`); never log passwords or connection strings.
4. **RBAC** — Roles: `org_admin`, `project_admin`, `analyst`, `viewer`. Check permissions via `app/core/rbac.py`.
5. **Rate limiting** — Redis token bucket per user (60/min) and org (1000/min) by default.
6. **Query limits** — 30s timeout, 10k max rows (configurable in settings).

## API workflow (happy path)

1. `POST /api/v1/auth/register` — create org + user
2. `POST /api/v1/orgs/{org_id}/projects` — create project
3. `POST /api/v1/projects/{id}/datasources` — register datasource
4. `POST /api/v1/datasources/{id}/schema/refresh` — introspect schema
5. `POST /api/v1/projects/{id}/conversations` — start conversation
6. `POST /api/v1/conversations/{id}/messages` — send NL query → `QueryResponse`

Auth: Bearer JWT on all endpoints except `/auth/register`, `/auth/login`, `/health`.

## Key documentation

| Document | Contents |
|----------|----------|
| [docs/architecture.md](docs/architecture.md) | System diagrams, agent flow, connector matrix, deployment |
| [docs/decisions.md](docs/decisions.md) | Architecture decision record |
| [backend/docs/api.md](backend/docs/api.md) | API usage and rate limits |
| [backend/docs/json-response-contract.md](backend/docs/json-response-contract.md) | `QueryResponse` schema for GUI |
| [backend/docs/audit-partitioning.md](backend/docs/audit-partitioning.md) | Audit log scaling strategy |
| [backend/README.md](backend/README.md) | Datasource config examples (incl. Elasticsearch) |
| [frontend/README.md](frontend/README.md) | Frontend setup, scripts, e2e tests |
| [frontend/widget/README.md](frontend/widget/README.md) | Embeddable React widget for third-party apps |

## Agent workflow tips

1. **Start here** and skim [docs/architecture.md](docs/architecture.md) for the subsystem you are changing.
2. **Run backend tests** from `backend/`: `pytest tests/ -v`.
3. **Run frontend e2e** from `frontend/`: `npm run test:e2e`.
4. **Lint** with `ruff check app tests` (if ruff is installed).
4. **Do not commit** `.env` files or secrets.
5. **New features** that affect the API should update `backend/docs/api.md` and/or OpenAPI via route docstrings.
6. **Schema changes** require an Alembic migration.
7. **New datasource type** → connector plugin + registry entry + prompt file + guardrails + unit tests.

## Out of scope (for now)

- Write operations on customer databases
- Backend conversation list endpoint (frontend uses localStorage)
- CI/CD pipelines (not yet in repo)
- Production Kubernetes manifests (architecture documented, not implemented in repo)
