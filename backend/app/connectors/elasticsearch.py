import json
import time
from typing import Any

from elasticsearch import AsyncElasticsearch

from app.connectors.base import (
    ColumnInfo,
    CompiledQuery,
    ConnectionConfig,
    ConnectionTestResult,
    EntityInfo,
    QueryLimits,
    QueryResult,
    ResultColumn,
    SchemaSnapshot,
    ValidationResult,
)

BLOCKED_ES_BODY_KEYS = {
    "script",
    "delete",
    "update",
    "index",
    "create",
    "bulk",
    "pipeline",
}


class ElasticsearchConnector:
    dialect = "elasticsearch"

    def _scheme(self, config: ConnectionConfig) -> str:
        if config.ssl_mode in ("require", "verify", "verify-full", "true", "1"):
            return "https"
        return "http"

    def _client(self, config: ConnectionConfig) -> AsyncElasticsearch:
        hosts = [{"host": config.host, "port": config.port, "scheme": self._scheme(config)}]
        kwargs: dict[str, Any] = {"hosts": hosts, "request_timeout": 30}
        if config.username and config.password:
            kwargs["basic_auth"] = (config.username, config.password)
        return AsyncElasticsearch(**kwargs)

    def _default_index(self, config: ConnectionConfig) -> str:
        return config.database if config.database and config.database != "*" else "*"

    async def test_connection(self, config: ConnectionConfig) -> ConnectionTestResult:
        start = time.monotonic()
        client = self._client(config)
        try:
            ok = await client.ping()
            if not ok:
                return ConnectionTestResult(success=False, message="Elasticsearch ping failed")
            latency = (time.monotonic() - start) * 1000
            return ConnectionTestResult(success=True, message="Connection successful", latency_ms=latency)
        except Exception as e:
            return ConnectionTestResult(success=False, message=str(e))
        finally:
            await client.close()

    def _infer_type(self, value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "float"
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "object"
        return "string"

    def _mapping_to_columns(self, properties: dict[str, Any], prefix: str = "") -> list[ColumnInfo]:
        columns: list[ColumnInfo] = []
        for field_name, field_def in properties.items():
            full_name = f"{prefix}{field_name}" if not prefix else f"{prefix}.{field_name}"
            field_type = field_def.get("type", "object")
            if field_type == "object" and "properties" in field_def:
                columns.extend(self._mapping_to_columns(field_def["properties"], full_name))
            else:
                columns.append(
                    ColumnInfo(
                        name=full_name,
                        data_type=field_type,
                        nullable=True,
                        is_pk=field_name == "_id",
                    )
                )
        return columns

    async def introspect_schema(self, config: ConnectionConfig) -> SchemaSnapshot:
        client = self._client(config)
        entities: list[EntityInfo] = []
        try:
            indices_info = await client.cat.indices(format="json", h="index")
            index_names = sorted(
                row["index"]
                for row in indices_info
                if not row["index"].startswith(".")
            )

            for index_name in index_names:
                mapping_resp = await client.indices.get_mapping(index=index_name)
                index_mapping = mapping_resp.get(index_name, {}).get("mappings", {})
                properties = index_mapping.get("properties", {})
                columns = self._mapping_to_columns(properties)
                if not any(c.name == "_id" for c in columns):
                    columns.insert(0, ColumnInfo(name="_id", data_type="keyword", is_pk=True))

                sample_rows: list[dict] = []
                try:
                    search_resp = await client.search(
                        index=index_name,
                        body={"query": {"match_all": {}}, "size": 3},
                    )
                    for hit in search_resp.get("hits", {}).get("hits", []):
                        row = dict(hit.get("_source", {}))
                        row["_id"] = hit.get("_id")
                        row["_index"] = hit.get("_index")
                        sample_rows.append(self._serialize_row(row))
                except Exception:
                    pass

                entities.append(
                    EntityInfo(
                        name=index_name,
                        type="index",
                        columns=columns,
                        sample_rows=sample_rows,
                    )
                )
            return SchemaSnapshot(entities=entities)
        finally:
            await client.close()

    def _serialize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        serialized = {}
        for k, v in row.items():
            if hasattr(v, "isoformat"):
                serialized[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                serialized[k] = json.dumps(v, default=str)
            else:
                serialized[k] = v
        return serialized

    def validate_query(self, query: str) -> ValidationResult:
        try:
            payload = json.loads(query)
        except json.JSONDecodeError as e:
            return ValidationResult(valid=False, message=f"Invalid JSON query: {e}")

        if not isinstance(payload, dict):
            return ValidationResult(valid=False, message="Query must be a JSON object")

        if "index" not in payload:
            return ValidationResult(valid=False, message='Query must include "index" field')
        if "body" not in payload:
            return ValidationResult(valid=False, message='Query must include "body" field')
        if not isinstance(payload["body"], dict):
            return ValidationResult(valid=False, message='"body" must be a JSON object')

        for key in payload["body"]:
            if key in BLOCKED_ES_BODY_KEYS:
                return ValidationResult(valid=False, message=f"Blocked key in body: {key}")

        return ValidationResult(valid=True)

    def _flatten_aggregations(self, aggs: dict[str, Any], prefix: str = "") -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for agg_name, agg_data in aggs.items():
            col_name = f"{prefix}{agg_name}" if prefix else agg_name

            if "buckets" in agg_data:
                for bucket in agg_data["buckets"]:
                    row: dict[str, Any] = {col_name: bucket.get("key_as_string", bucket.get("key"))}
                    row[f"{col_name}_doc_count"] = bucket.get("doc_count")
                    sub_aggs = {
                        k: v for k, v in bucket.items() if k not in ("key", "key_as_string", "doc_count")
                    }
                    if sub_aggs:
                        sub_rows = self._flatten_aggregations(sub_aggs)
                        for sub_row in sub_rows:
                            rows.append({**row, **sub_row})
                    else:
                        rows.append(row)
            elif "value" in agg_data:
                rows.append({col_name: agg_data["value"]})
            else:
                for k, v in agg_data.items():
                    if isinstance(v, dict) and ("buckets" in v or "value" in v):
                        rows.extend(self._flatten_aggregations({k: v}, f"{col_name}_"))

        return rows

    def _hits_to_rows(self, hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for hit in hits:
            row = dict(hit.get("_source", {}))
            row["_id"] = hit.get("_id")
            row["_score"] = hit.get("_score")
            rows.append(self._serialize_row(row))
        return rows

    async def execute_read_query(
        self, config: ConnectionConfig, query: CompiledQuery, limits: QueryLimits
    ) -> QueryResult:
        validation = self.validate_query(query.query)
        if not validation.valid:
            raise ValueError(validation.message)

        payload = json.loads(query.query)
        index = payload["index"]
        body = dict(payload["body"])
        body.setdefault("size", limits.max_rows + 1)
        if body["size"] > limits.max_rows + 1:
            body["size"] = limits.max_rows + 1

        start = time.monotonic()
        client = self._client(config)
        try:
            response = await client.search(
                index=index,
                body=body,
                request_timeout=limits.timeout_seconds,
            )

            rows: list[dict[str, Any]] = []
            if response.get("aggregations"):
                rows = self._flatten_aggregations(response["aggregations"])
            else:
                hits = response.get("hits", {}).get("hits", [])
                rows = self._hits_to_rows(hits)

            truncated = len(rows) > limits.max_rows
            rows = rows[: limits.max_rows]

            columns: list[ResultColumn] = []
            if rows:
                for key in rows[0]:
                    columns.append(ResultColumn(name=key, type=self._infer_type(rows[0][key])))

            duration = int((time.monotonic() - start) * 1000)
            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                truncated=truncated,
                duration_ms=duration,
            )
        finally:
            await client.close()
