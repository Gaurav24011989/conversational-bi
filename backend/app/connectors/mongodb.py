import json
import time
from collections import Counter
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

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

BLOCKED_MONGO_OPS = {"$out", "$merge", "$delete", "$update", "$replaceRoot"}


class MongoDBConnector:
    dialect = "mongodb"

    def _uri(self, config: ConnectionConfig) -> str:
        auth_source = config.auth_source or "admin"
        if config.username and config.password:
            return (
                f"mongodb://{config.username}:{config.password}"
                f"@{config.host}:{config.port}/{config.database}?authSource={auth_source}"
            )
        return f"mongodb://{config.host}:{config.port}/{config.database}"

    async def test_connection(self, config: ConnectionConfig) -> ConnectionTestResult:
        start = time.monotonic()
        try:
            client = AsyncIOMotorClient(self._uri(config), serverSelectionTimeoutMS=10000)
            await client.admin.command("ping")
            client.close()
            latency = (time.monotonic() - start) * 1000
            return ConnectionTestResult(success=True, message="Connection successful", latency_ms=latency)
        except Exception as e:
            return ConnectionTestResult(success=False, message=str(e))

    def _infer_type(self, value: Any) -> str:
        if value is None:
            return "null"
        return type(value).__name__

    async def introspect_schema(self, config: ConnectionConfig) -> SchemaSnapshot:
        client = AsyncIOMotorClient(self._uri(config), serverSelectionTimeoutMS=30000)
        db = client[config.database]
        entities: list[EntityInfo] = []

        try:
            collections = await db.list_collection_names()
            for coll_name in sorted(collections):
                if coll_name.startswith("system."):
                    continue
                coll = db[coll_name]
                samples = await coll.aggregate([{"$sample": {"size": 20}}]).to_list(20)

                field_types: Counter[str] = Counter()
                for doc in samples:
                    for key, val in doc.items():
                        field_types[key] = self._infer_type(val)

                columns = [
                    ColumnInfo(name=k, data_type=v, nullable=True, is_pk=(k == "_id"))
                    for k, v in field_types.items()
                ]

                sample_rows = []
                for doc in samples[:3]:
                    row = {}
                    for k, v in doc.items():
                        if k == "_id":
                            row[k] = str(v)
                        elif hasattr(v, "isoformat"):
                            row[k] = v.isoformat()
                        elif isinstance(v, (dict, list)):
                            row[k] = json.dumps(v, default=str)
                        else:
                            row[k] = v
                    sample_rows.append(row)

                entities.append(
                    EntityInfo(
                        name=coll_name,
                        type="collection",
                        columns=columns,
                        sample_rows=sample_rows,
                    )
                )
            return SchemaSnapshot(entities=entities)
        finally:
            client.close()

    def validate_query(self, query: str) -> ValidationResult:
        try:
            pipeline = json.loads(query)
        except json.JSONDecodeError as e:
            return ValidationResult(valid=False, message=f"Invalid JSON pipeline: {e}")
        if not isinstance(pipeline, list):
            return ValidationResult(valid=False, message="Pipeline must be a JSON array")

        def check_stage(stage: dict) -> str | None:
            for op in stage:
                if op in BLOCKED_MONGO_OPS:
                    return f"Blocked operator: {op}"
            return None

        for stage in pipeline:
            if not isinstance(stage, dict):
                return ValidationResult(valid=False, message="Each pipeline stage must be an object")
            err = check_stage(stage)
            if err:
                return ValidationResult(valid=False, message=err)
        return ValidationResult(valid=True)

    async def execute_read_query(
        self, config: ConnectionConfig, query: CompiledQuery, limits: QueryLimits
    ) -> QueryResult:
        validation = self.validate_query(query.query)
        if not validation.valid:
            raise ValueError(validation.message)

        pipeline = json.loads(query.query)
        if not any("$limit" in stage for stage in pipeline):
            pipeline.append({"$limit": limits.max_rows + 1})

        start = time.monotonic()
        client = AsyncIOMotorClient(self._uri(config), serverSelectionTimeoutMS=limits.timeout_seconds * 1000)
        try:
            # Pipeline must target a collection; first stage should be $match on collection
            # Convention: query includes collection name prefix as comment or we use first collection
            db = client[config.database]
            collections = await db.list_collection_names()
            if not collections:
                raise ValueError("No collections found")
            coll_name = collections[0]
            for stage in pipeline:
                if "$collection" in stage:
                    coll_name = stage.pop("$collection")
                    break

            coll = db[coll_name]
            cursor = coll.aggregate(pipeline, maxTimeMS=limits.timeout_seconds * 1000)
            rows_raw = await cursor.to_list(length=limits.max_rows + 1)

            truncated = len(rows_raw) > limits.max_rows
            rows_raw = rows_raw[: limits.max_rows]

            columns: list[ResultColumn] = []
            if rows_raw:
                for key in rows_raw[0]:
                    columns.append(ResultColumn(name=key, type=self._infer_type(rows_raw[0][key])))

            rows: list[dict] = []
            for r in rows_raw:
                row = {}
                for k, v in r.items():
                    if k == "_id":
                        row[k] = str(v)
                    elif hasattr(v, "isoformat"):
                        row[k] = v.isoformat()
                    elif isinstance(v, (dict, list)):
                        row[k] = json.dumps(v, default=str)
                    else:
                        row[k] = v
                rows.append(row)

            duration = int((time.monotonic() - start) * 1000)
            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                truncated=truncated,
                duration_ms=duration,
            )
        finally:
            client.close()
