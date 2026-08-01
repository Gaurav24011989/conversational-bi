from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.registry import get_connector
from app.models import SchemaSnapshot
from app.services.cache import cache_service
from app.services.datasource_service import datasource_service


class SchemaService:
    async def get_latest_schema(self, db: AsyncSession, datasource_id: UUID) -> SchemaSnapshot | None:
        result = await db.execute(
            select(SchemaSnapshot)
            .where(SchemaSnapshot.datasource_id == datasource_id)
            .order_by(SchemaSnapshot.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def refresh_schema(
        self, db: AsyncSession, datasource_id: UUID, org_id: UUID, project_id: UUID
    ) -> SchemaSnapshot:
        ds = await datasource_service.get(db, datasource_id)
        if not ds:
            raise ValueError("Data source not found")

        config = datasource_service.get_connection_config(ds)
        connector = get_connector(ds.type.value)
        snapshot = await connector.introspect_schema(config)
        schema_dict = snapshot.to_dict()

        version_result = await db.execute(
            select(SchemaSnapshot.version)
            .where(SchemaSnapshot.datasource_id == datasource_id)
            .order_by(SchemaSnapshot.version.desc())
            .limit(1)
        )
        latest_version = version_result.scalar_one_or_none() or 0

        schema_snapshot = SchemaSnapshot(
            datasource_id=datasource_id,
            version=latest_version + 1,
            schema_data=schema_dict,
        )
        db.add(schema_snapshot)
        await db.flush()

        await cache_service.set_schema(org_id, project_id, datasource_id, schema_dict)
        return schema_snapshot

    async def get_schema_for_agent(
        self, db: AsyncSession, datasource_id: UUID, org_id: UUID, project_id: UUID
    ) -> dict:
        cached = await cache_service.get_schema(org_id, project_id, datasource_id)
        if cached:
            return cached

        snapshot = await self.get_latest_schema(db, datasource_id)
        if snapshot:
            await cache_service.set_schema(org_id, project_id, datasource_id, snapshot.schema_data)
            return snapshot.schema_data
        return {"entities": []}


schema_service = SchemaService()
