import asyncio
from uuid import UUID

from app.connectors.base import CompiledQuery, ConnectionConfig, QueryLimits, QueryResult
from app.connectors.registry import get_connector
from app.config import settings
from app.execution.guardrails import enforce_table_allowlist, validate_sql_query
from app.execution.pool_manager import pool_manager


class QueryExecutor:
    async def execute(
        self,
        dialect: str,
        config: ConnectionConfig,
        query: str,
        query_language: str,
        datasource_id: UUID,
        allowed_tables: list[str] | None = None,
    ) -> QueryResult:
        if query_language == "sql":
            valid, msg = validate_sql_query(query)
            if not valid:
                raise ValueError(msg)
            allowed, msg = enforce_table_allowlist(query, allowed_tables)
            if not allowed:
                raise ValueError(msg)

        connector = get_connector(dialect)
        validation = connector.validate_query(query)
        if not validation.valid:
            raise ValueError(validation.message)

        limits = QueryLimits(
            timeout_seconds=settings.query_timeout_seconds,
            max_rows=settings.query_max_rows,
        )
        compiled = CompiledQuery(query=query, language=query_language)

        return await pool_manager.execute_with_pool(
            datasource_id=datasource_id,
            dialect=dialect,
            config=config,
            connector=connector,
            compiled=compiled,
            limits=limits,
        )


executor = QueryExecutor()
