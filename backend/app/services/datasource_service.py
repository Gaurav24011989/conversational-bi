import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import ConnectionConfig
from app.connectors.registry import get_connector
from app.core.encryption import decrypt_value, encrypt_value
from app.models import DataSource, DataSourceType
from app.schemas import ConnectionTestResponse, DataSourceCreate, DataSourceResponse


class DataSourceService:
    def _config_from_encrypted(self, encrypted: str) -> ConnectionConfig:
        data = json.loads(decrypt_value(encrypted))
        return ConnectionConfig(**data)

    def _encrypt_config(self, config: dict) -> str:
        return encrypt_value(json.dumps(config))

    async def create(
        self, db: AsyncSession, project_id: UUID, data: DataSourceCreate
    ) -> DataSource:
        ds = DataSource(
            project_id=project_id,
            name=data.name,
            type=DataSourceType(data.type.value),
            encrypted_config=self._encrypt_config(data.config.model_dump()),
            allowed_tables=data.allowed_tables,
        )
        db.add(ds)
        await db.flush()
        return ds

    async def get(self, db: AsyncSession, datasource_id: UUID) -> DataSource | None:
        result = await db.execute(select(DataSource).where(DataSource.id == datasource_id))
        return result.scalar_one_or_none()

    async def list_by_project(self, db: AsyncSession, project_id: UUID) -> list[DataSource]:
        result = await db.execute(
            select(DataSource).where(DataSource.project_id == project_id, DataSource.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def test_connection(self, db: AsyncSession, datasource_id: UUID) -> ConnectionTestResponse:
        ds = await self.get(db, datasource_id)
        if not ds:
            return ConnectionTestResponse(success=False, message="Data source not found")
        config = self._config_from_encrypted(ds.encrypted_config)
        connector = get_connector(ds.type.value)
        result = await connector.test_connection(config)
        return ConnectionTestResponse(
            success=result.success, message=result.message, latency_ms=result.latency_ms
        )

    def get_connection_config(self, ds: DataSource) -> ConnectionConfig:
        return self._config_from_encrypted(ds.encrypted_config)

    def to_response(self, ds: DataSource) -> DataSourceResponse:
        return DataSourceResponse(
            id=ds.id,
            project_id=ds.project_id,
            name=ds.name,
            type=ds.type,
            is_active=ds.is_active,
            allowed_tables=ds.allowed_tables,
            created_at=ds.created_at,
        )


datasource_service = DataSourceService()
