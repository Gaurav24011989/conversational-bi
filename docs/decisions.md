# Architecture Decisions

Adopted defaults for Conversational BI backend implementation (per architecture plan).

| Decision | Choice |
|----------|--------|
| DB connectivity | Hybrid: direct connection + connector agent hook points for Phase 2 |
| Phase 1 data sources | PostgreSQL, MySQL, MongoDB, Elasticsearch |
| Auth | Built-in JWT + OIDC SSO hook points (Authlib) |
| Query mode | Read-only analytics (SELECT / aggregation pipelines only) |
| Deployment | Kubernetes-ready, cloud-agnostic Docker images |
| Metadata store | PostgreSQL |
| LLM provider | Google Gemini (swappable via LangChain factory) |
| Agent framework | LangGraph + LangChain + LangSmith |
| Frontend | React 19 + Vite 8 + Recharts; Playwright e2e with API mocks |
