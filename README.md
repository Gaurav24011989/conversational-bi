# Conversational BI

Multi-tenant agentic platform for natural-language data queries across PostgreSQL, MySQL, MongoDB, and Elasticsearch.

## Architecture

- **API**: FastAPI with JWT auth and RBAC
- **Agent**: LangGraph pipeline (schema retrieval → query generation → validation → execution → response formatting)
- **LLM**: Configurable via LangChain (Gemini default)
- **Observability**: LangSmith tracing
- **Cache/Queue**: Redis for schema cache, rate limiting, Celery workers

See [docs/architecture.md](docs/architecture.md) for high-level and low-level architecture diagrams, [docs/decisions.md](docs/decisions.md) for architecture decisions, and [backend/docs/](backend/docs/) for API docs.

## Quick start

```bash
cd backend

# Copy environment config
cp .env.example .env

# Start Postgres + Redis
docker compose -f docker/docker-compose.yml up -d postgres redis

# Install dependencies
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

## Environment variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Platform PostgreSQL connection |
| `REDIS_URL` | Redis connection |
| `SECRET_KEY` | JWT signing key |
| `ENCRYPTION_KEY` | Fernet key for data source credentials |
| `GEMINI_API_KEY` | Google Gemini API key |
| `LLM_PROVIDER` | `google`, `openai`, or `anthropic` |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing |

## Project structure

```
backend/
  app/
    api/v1/          # REST endpoints
    agents/          # LangGraph query agent
    connectors/      # PostgreSQL, MySQL, MongoDB, Elasticsearch plugins
    core/            # Auth, RBAC, encryption, tenancy
    execution/       # Query executor, guardrails, pool manager
    llm/             # LLM provider factory
    models/          # SQLAlchemy models
    services/        # Business logic
    workers/         # Celery background tasks
  alembic/           # Database migrations
  tests/             # Unit and integration tests
  docker/            # Docker Compose and Dockerfile
```

## API workflow

1. `POST /api/v1/auth/register` — create org + user
2. `POST /api/v1/orgs/{org_id}/projects` — create project
3. `POST /api/v1/projects/{id}/datasources` — register data source
4. `POST /api/v1/datasources/{id}/schema/refresh` — introspect schema
5. `POST /api/v1/projects/{id}/conversations` — start conversation
6. `POST /api/v1/conversations/{id}/messages` — send NL query, get JSON with data + chart recommendation

## Tests

```bash
cd backend
pytest tests/ -v
```
