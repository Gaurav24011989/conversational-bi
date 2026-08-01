# Audit Log Partitioning Strategy

The `audit_logs` table is designed for high-volume append-only writes at scale (1M+ users).

## MVP

Single table with indexes on `org_id`, `project_id`, and `created_at`.

## Production scaling

Partition by `created_at` monthly using PostgreSQL native partitioning:

```sql
CREATE TABLE audit_logs (
    id UUID NOT NULL,
    org_id UUID NOT NULL,
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    datasource_id UUID,
    action VARCHAR(100) NOT NULL,
    natural_language_query TEXT,
    generated_query TEXT,
    row_count INTEGER,
    duration_ms INTEGER,
    trace_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
```

- Create monthly partitions via scheduled job
- Drop partitions older than retention policy (e.g. 90 days)
- Use read replicas for audit analytics queries

## Tenant isolation

All audit queries MUST filter by `org_id` to prevent cross-tenant data access.
