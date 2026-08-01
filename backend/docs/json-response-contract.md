# JSON Response Contract

The primary contract between backend and React GUI is the `QueryResponse` object returned from `POST /api/v1/conversations/{id}/messages`.

## Success response

```json
{
  "message_id": "uuid",
  "conversation_id": "uuid",
  "role": "assistant",
  "type": "query_result",
  "natural_language_query": "Show monthly revenue for 2025",
  "generated_query": "SELECT ...",
  "query_language": "sql",
  "datasource": {
    "id": "uuid",
    "name": "Production Postgres",
    "dialect": "postgresql"
  },
  "execution": {
    "status": "success",
    "row_count": 12,
    "duration_ms": 87,
    "truncated": false
  },
  "data": {
    "columns": [
      {"name": "month", "type": "timestamp"},
      {"name": "revenue", "type": "numeric"}
    ],
    "rows": [
      {"month": "2025-01-01T00:00:00Z", "revenue": 12000.50}
    ]
  },
  "visualization": {
    "chart_type": "line",
    "title": "Monthly Revenue (2025)",
    "x_axis": {"field": "month", "label": "Month"},
    "y_axis": {"field": "revenue", "label": "Revenue"},
    "series": [{"field": "revenue"}],
    "reasoning": "Time series with one metric suits a line chart"
  },
  "follow_up_questions": [
    "Break down revenue by product category?",
    "Compare with 2024?"
  ],
  "trace_id": "langsmith-run-id"
}
```

## Chart types

`table`, `bar`, `line`, `area`, `pie`, `donut`, `scatter`, `metric`, `heatmap`

The LLM recommends a chart type; the server validates field names and falls back to `table` if invalid.

## Error response

```json
{
  "execution": {"status": "error"},
  "error": {"code": "QUERY_ERROR", "message": "Safe user-facing message"}
}
```

## Clarification response

```json
{
  "type": "clarification",
  "questions": ["Which time period?", "Which metric?"]
}
```
