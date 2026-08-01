# Conversational BI Backend

Python backend for the Conversational BI platform.

## Supported data sources

| Type | Default port | Query language |
|------|--------------|----------------|
| `postgresql` | 5432 | SQL |
| `mysql` | 3306 | SQL |
| `mongodb` | 27017 | Aggregation pipeline JSON |
| `elasticsearch` | 9200 | Query DSL JSON |

### Elasticsearch configuration

```json
{
  "name": "Logs Cluster",
  "type": "elasticsearch",
  "config": {
    "host": "localhost",
    "port": 9200,
    "database": "logs-*",
    "username": "elastic",
    "password": "secret",
    "ssl_mode": "require"
  },
  "allowed_tables": ["logs-2025", "logs-*"]
}
```

- `database` — default index pattern
- `ssl_mode: "require"` — use HTTPS
- `allowed_tables` — optional index allow-list

Generated queries use this structure:

```json
{
  "index": "logs-*",
  "body": {
    "query": { "range": { "@timestamp": { "gte": "2025-01-01" } } },
    "aggs": { "by_level": { "terms": { "field": "level.keyword" } } },
    "size": 0
  }
}
```
