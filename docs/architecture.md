# Conversational BI — Architecture Diagrams

This document provides high-level and low-level architecture views of the platform as implemented in the backend MVP.

---

## 1. High-Level Architecture

The platform is a **multi-tenant, agentic data query service**. Users ask questions in natural language; the system introspects connected data sources, generates a safe read-only query via LLM, executes it, and returns structured JSON for chart rendering in the React GUI.

```mermaid
flowchart TB
  subgraph users [Users and Clients]
    Analyst[Business Analyst]
    ReactGUI["React GUI\n(Vite + Recharts)"]
    ReactWidget["React Embed Widget\n(conversational-bi-widget)"]
    APIClient[API Client / SDK]
  end

  subgraph platform [Conversational BI Platform]
    LB[Load Balancer]
    API[FastAPI API Layer]
    Agent[LangGraph Query Agent]
    Workers[Celery Workers]
  end

  subgraph intelligence [AI and Observability]
    LLM["LLM Provider\n(Gemini / OpenAI / Anthropic)"]
    LangSmith[LangSmith Tracing]
  end

  subgraph platformData [Platform Data Stores]
    MetaDB[(PostgreSQL\nMetadata DB)]
    Redis[(Redis\nCache and Queue)]
  end

  subgraph customerData [Customer Data Sources]
  PG[(PostgreSQL)]
  MySQL[(MySQL)]
  Mongo[(MongoDB)]
  ES[(Elasticsearch)]
  end

  Analyst --> ReactGUI
  Analyst --> ReactWidget
  Analyst --> APIClient
  ReactGUI --> LB
  ReactWidget --> LB
  APIClient --> LB
  LB --> API

  API --> Agent
  API --> Workers
  API --> MetaDB
  API --> Redis

  Agent --> LLM
  Agent --> LangSmith
  Agent --> Redis
  Agent --> MetaDB

  Workers --> MetaDB
  Workers --> Redis

  Agent --> PG
  Agent --> MySQL
  Agent --> Mongo
  Agent --> ES
```

### High-level responsibilities

| Layer | Responsibility |
|-------|----------------|
| **API Layer** | Auth, RBAC, tenancy enforcement, REST endpoints |
| **Agent Layer** | NL → query generation, validation, execution orchestration |
| **Connector Layer** | Pluggable adapters for each data source dialect |
| **Platform Data** | Metadata, conversations, audit logs, encrypted secrets |
| **Intelligence** | Swappable LLM + LangSmith observability |

### Tenant hierarchy

```
Organization  (billing + SSO boundary)
  └── Project   (workspace)
        └── DataSource  (encrypted connection + schema snapshots)
  └── Users + RBAC memberships
```

---

## 2. Low-Level Architecture — Component View

Internal module structure of the Python backend (`backend/app/`).

```mermaid
flowchart TB
  subgraph api [api/v1]
    AuthEP[auth.py]
    ProjEP[projects.py]
    DSEP[datasources.py]
    ConvEP[conversations.py]
  end

  subgraph core [core]
    Security[security.py\nJWT + OIDC hooks]
    RBAC[rbac.py\nRole permissions]
    Tenancy[tenancy.py\nCache key namespacing]
    Encryption[encryption.py\nFernet credentials]
  end

  subgraph services [services]
    DSSvc[datasource_service]
    SchemaSvc[schema_service]
    ConvSvc[conversation_service]
    AuditSvc[audit_service]
    CacheSvc[cache.py\nRedis + rate limits]
  end

  subgraph agents [agents]
    Graph[graph.py\nLangGraph state machine]
    Nodes[nodes/\nretrieve → generate → validate → execute → format]
    Prompts[prompts/\nDialect-specific LLM prompts]
    State[state.py\nAgentState TypedDict]
  end

  subgraph connectors [connectors]
    Registry[registry.py]
    PGConn[postgresql.py]
    MySQLConn[mysql.py]
    MongoConn[mongodb.py]
    ESConn[elasticsearch.py]
    Base[base.py\nProtocol + dataclasses]
  end

  subgraph execution [execution]
    Executor[executor.py]
    Guardrails[guardrails.py\nRead-only SQL checks]
    PoolMgr[pool_manager.py\nPer-DS concurrency]
  end

  subgraph llm [llm]
    Factory[factory.py\nProvider abstraction]
  end

  subgraph workers [workers]
    Celery[celery_app.py]
    SchemaRefresh[schema_refresh.py]
  end

  subgraph persistence [models + database]
    Models[SQLAlchemy models]
    DB[database.py\nAsync session]
  end

  ConvEP --> ConvSvc
  DSEP --> DSSvc
  DSEP --> SchemaSvc
  ProjEP --> RBAC
  AuthEP --> Security

  ConvSvc --> Graph
  ConvSvc --> AuditSvc
  ConvSvc --> CacheSvc
  SchemaSvc --> CacheSvc
  DSSvc --> Encryption
  DSSvc --> Registry

  Graph --> Nodes
  Nodes --> Factory
  Nodes --> SchemaSvc
  Nodes --> Executor
  Nodes --> Prompts

  Executor --> Guardrails
  Executor --> PoolMgr
  Executor --> Registry

  Registry --> PGConn
  Registry --> MySQLConn
  Registry --> MongoConn
  Registry --> ESConn

  SchemaRefresh --> SchemaSvc
  Celery --> SchemaRefresh

  services --> Models
  services --> DB
```

---

## 3. Low-Level Architecture — Query Agent Flow

The LangGraph agent is the core of conversational BI. Each user message triggers this state machine.

```mermaid
stateDiagram-v2
  [*] --> retrieve_schema: User NL query

  retrieve_schema --> generate_query: Top-K relevant entities selected

  generate_query --> validate_query: LLM returns query + viz hint
  generate_query --> format_response: LLM failure

  validate_query --> execute_query: Guardrails pass
  validate_query --> format_response: Validation failure

  execute_query --> format_response: Rows returned
  execute_query --> format_response: Execution error

  format_response --> [*]: QueryResponse JSON
```

### Agent nodes (detail)

```mermaid
sequenceDiagram
  participant API as ConversationService
  participant Agent as LangGraph Agent
  participant Schema as SchemaService
  participant Redis as Redis Cache
  participant LLM as LLM via LangChain
  participant Val as Guardrails + Connector Validator
  participant Exec as QueryExecutor
  participant Pool as PoolManager
  participant Conn as DataSource Connector
  participant DS as Customer DB

  API->>Agent: invoke(state)
  Agent->>Schema: get_schema_for_agent()
  Schema->>Redis: check cache
  Redis-->>Schema: schema or miss
  Schema-->>Agent: entities, columns, samples

  Agent->>LLM: structured output prompt
  Note over LLM: query, query_language,<br/>visualization, follow_ups
  LLM-->>Agent: GeneratedQueryOutput

  Agent->>Val: validate_query()
  Note over Val: Block DDL/DML,<br/>index allow-list,<br/>dialect rules
  Val-->>Agent: approved or error

  Agent->>Exec: execute(dialect, query)
  Exec->>Pool: acquire semaphore
  Pool->>Conn: execute_read_query()
  Conn->>DS: run with timeout + row limit
  DS-->>Conn: result set
  Conn-->>Agent: QueryResult

  Agent->>Agent: format_response()
  Note over Agent: Validate chart fields,<br/>build QueryResponse JSON
  Agent-->>API: response + visualization
```

---

## 4. Low-Level Architecture — Data Source Connectors

All connectors implement the same protocol. The registry selects the implementation by `DataSourceType`.

```mermaid
flowchart LR
  subgraph protocol [DataSourceConnector Protocol]
    Test[test_connection]
    Introspect[introspect_schema]
    Validate[validate_query]
    Execute[execute_read_query]
  end

  subgraph implementations [Connector Plugins]
    PG["PostgreSQL\nSQL / information_schema"]
    MySQL["MySQL\nSQL / information_schema"]
    Mongo["MongoDB\nAggregation pipeline JSON"]
    ES["Elasticsearch\nQuery DSL JSON"]
  end

  subgraph queryFormats [Query Languages]
    SQL[SQL SELECT / WITH]
    MongoPipe[JSON pipeline array]
    ESDSL["JSON index + body"]
  end

  Registry[get_connector dialect] --> PG
  Registry --> MySQL
  Registry --> Mongo
  Registry --> ES

  PG --> SQL
  MySQL --> SQL
  Mongo --> MongoPipe
  ES --> ESDSL

  PG --> protocol
  MySQL --> protocol
  Mongo --> protocol
  ES --> protocol
```

### Connector capabilities

| Connector | Entity type | Introspection | Query format | Read-only enforcement |
|-----------|-------------|---------------|--------------|----------------------|
| PostgreSQL | `table` | `information_schema` + FK | SQL | sqlparse + keyword blocklist |
| MySQL | `table` | `information_schema` | SQL | sqlparse + keyword blocklist |
| MongoDB | `collection` | `$sample` + type inference | Pipeline JSON | Block `$out`, `$merge`, etc. |
| Elasticsearch | `index` | mappings + search samples | `index` + `body` JSON | Block `script`, `update`, etc. |

---

## 5. Low-Level Architecture — Security and Multi-Tenancy

```mermaid
flowchart TB
  subgraph request [Incoming Request]
    JWT[JWT Bearer Token]
    OrgCtx[org_id from token]
    ProjCtx[project_id from URL]
  end

  subgraph middleware [Access Control]
    AuthN[Authentication\nget_current_user]
    AuthZ[Authorization\nrequire_project_access]
    TenantCheck[Cross-tenant check\norg_id match]
    DSCheck[DataSource scope\ndatasource_id grant]
  end

  subgraph isolation [Isolation Boundaries]
    EncSecrets[Encrypted credentials\nFernet per datasource]
    PoolIsolation[Per-datasource semaphores\nno shared pools]
    CacheNS[Redis keys namespaced\norg:project:ds]
    AuditLog[Append-only audit trail]
  end

  JWT --> AuthN
  AuthN --> AuthZ
  OrgCtx --> TenantCheck
  ProjCtx --> AuthZ
  AuthZ --> DSCheck

  DSCheck --> EncSecrets
  DSCheck --> PoolIsolation
  DSCheck --> CacheNS
  DSCheck --> AuditLog
```

### RBAC roles

| Role | Configure datasources | Run queries | Manage project |
|------|----------------------|-------------|----------------|
| `org_admin` | Yes | Yes | Yes (all projects) |
| `project_admin` | Yes | Yes | Yes |
| `analyst` | No | Yes | No |
| `viewer` | No | Yes (limited) | No |

---

## 6. Low-Level Architecture — Deployment Topology

Target deployment for scale (1M+ users). MVP runs all services via Docker Compose locally.

```mermaid
flowchart TB
  subgraph internet [Internet]
    Users[Users]
  end

  subgraph k8s [Kubernetes Cluster]
    subgraph ingress [Ingress]
      IngressCtrl[Ingress Controller]
    end

    subgraph apiPods [API Tier - stateless]
      API1[FastAPI Pod 1]
      API2[FastAPI Pod 2]
      APIN[FastAPI Pod N]
    end

    subgraph workerPods [Worker Tier]
      W1[Celery Worker 1]
      W2[Celery Worker 2]
    end

    subgraph dataTier [Data Tier]
      MetaDB[(PostgreSQL\nprimary + replicas)]
      RedisCluster[(Redis Cluster)]
    end
  end

  subgraph external [External Services]
    LLMCloud[LLM API\nGemini / OpenAI]
    LangSmithCloud[LangSmith]
    CustomerDBs[(Customer Data Sources\nPG / MySQL / Mongo / ES)]
  end

  Users --> IngressCtrl
  IngressCtrl --> API1
  IngressCtrl --> API2
  IngressCtrl --> APIN

  API1 --> MetaDB
  API1 --> RedisCluster
  API1 --> LLMCloud
  API1 --> LangSmithCloud
  API1 --> CustomerDBs

  W1 --> MetaDB
  W1 --> RedisCluster
  W1 --> CustomerDBs
```

### Scaling levers

| Concern | Mechanism |
|---------|-----------|
| API throughput | Horizontal pod autoscaling (stateless) |
| LLM latency | Flash model, schema pruning, response cache |
| Schema introspection | Redis cache (1h TTL) + async Celery refresh |
| DB connections | Per-datasource pool limits + semaphores |
| Rate limiting | Redis token bucket per user and per org |
| Audit volume | Monthly table partitioning (see `backend/docs/audit-partitioning.md`) |

---

## 7. Low-Level Architecture — API Response Contract

The agent produces a `QueryResponse` JSON consumed by the React GUI to render charts.

```mermaid
flowchart LR
  subgraph input [User Input]
    NLQ[Natural language question]
  end

  subgraph agentOutput [Agent Output]
    GenQ[generated_query]
    Data[data.columns + data.rows]
    Viz[visualization.chart_type\nx_axis / y_axis / series]
    Meta[execution metadata\nfollow_up_questions]
  end

  subgraph gui [React GUI]
    AuthPages[Login / Register]
    Projects[Project management]
    Datasources[Datasource config]
    Chat[NL query chat]
    ChartPicker[Chart component selector]
    Bar[Bar Chart]
    Line[Line Chart]
    Table[Data Table]
    Metric[KPI Card]
    Other[Pie / Scatter / Heatmap]
  end

  NLQ --> GenQ
  GenQ --> Data
  Data --> Viz
  Viz --> Chat
  Chat --> ChartPicker
  ChartPicker --> Bar
  ChartPicker --> Line
  ChartPicker --> Table
  ChartPicker --> Metric
  ChartPicker --> Other
```

---

## 8. Frontend Architecture

The React SPA (`frontend/`) consumes the REST API and renders `QueryResponse` payloads.

```mermaid
flowchart TB
  subgraph frontend [frontend/src]
    APIClient[api/client.ts]
    AuthCtx[AuthContext\nJWT in localStorage]
    Pages[pages/\nLogin, Projects, Conversation]
    Components[components/\nQueryResult, ChartView, DataTable]
    Storage[utils/storage.ts\nconversation list cache]
  end

  subgraph vite [Vite Dev Server]
    Proxy["/api proxy → backend:8000"]
  end

  subgraph tests [frontend/e2e]
    Playwright[Playwright tests]
    Mocks[API route mocks]
  end

  Pages --> APIClient
  APIClient --> Proxy
  Proxy --> BackendAPI[FastAPI /api/v1]
  Pages --> Components
  Pages --> Storage
  Playwright --> Mocks
  Mocks --> Pages
```

### Frontend routes

| Route | Page | Auth |
|-------|------|------|
| `/login` | Login | Public |
| `/register` | Register | Public |
| `/projects` | Project list | Protected |
| `/projects/:id` | Project detail (datasources, conversations) | Protected |
| `/projects/:id/conversations/:id` | NL query chat | Protected |

### Embed widget (`frontend/widget/`)

The `conversational-bi-widget` package exposes a drop-in `<ConversationalBIWidget />` for host React applications. It reuses the same conversation UI patterns (messages, clarifications, `QueryResponse` charts/tables) but does not depend on React Router or the SPA auth flow — the host app supplies `apiBaseUrl` and `accessToken`.

```tsx
import { ConversationalBIWidget } from 'conversational-bi-widget'
import 'conversational-bi-widget/style.css'

<ConversationalBIWidget
  apiBaseUrl="https://api.example.com"
  accessToken={jwt}
  projectId="..."
  datasourceId="..."
/>
```

Styles are scoped under `.cbi-widget` to avoid leaking into the host app. See [frontend/widget/README.md](../frontend/widget/README.md).

---

## Related documentation

- [Architecture decisions](decisions.md)
- [API reference](../backend/docs/api.md)
- [JSON response contract](../backend/docs/json-response-contract.md)
- [Frontend README](../frontend/README.md)
- [Embed widget README](../frontend/widget/README.md)
- [Audit log partitioning](../backend/docs/audit-partitioning.md)
