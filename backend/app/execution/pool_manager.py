import asyncio
from uuid import UUID

from app.connectors.base import (
    CompiledQuery,
    ConnectionConfig,
    DataSourceConnector,
    QueryLimits,
    QueryResult,
)


class ConnectionPoolManager:
    """Per-datasource concurrency limiter. Pools are never shared across tenants."""

    def __init__(self, max_concurrent_per_datasource: int = 5) -> None:
        self._semaphores: dict[str, asyncio.Semaphore] = {}
        self._max = max_concurrent_per_datasource

    def _key(self, datasource_id: UUID) -> str:
        return str(datasource_id)

    def _get_semaphore(self, datasource_id: UUID) -> asyncio.Semaphore:
        key = self._key(datasource_id)
        if key not in self._semaphores:
            self._semaphores[key] = asyncio.Semaphore(self._max)
        return self._semaphores[key]

    async def execute_with_pool(
        self,
        datasource_id: UUID,
        dialect: str,
        config: ConnectionConfig,
        connector: DataSourceConnector,
        compiled: CompiledQuery,
        limits: QueryLimits,
    ) -> QueryResult:
        sem = self._get_semaphore(datasource_id)
        async with sem:
            return await connector.execute_read_query(config, compiled, limits)

    def evict(self, datasource_id: UUID) -> None:
        self._semaphores.pop(self._key(datasource_id), None)


pool_manager = ConnectionPoolManager()
