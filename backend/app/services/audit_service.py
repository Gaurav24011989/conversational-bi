from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


class AuditService:
    async def log_query(
        self,
        db: AsyncSession,
        org_id: UUID,
        project_id: UUID,
        user_id: UUID,
        datasource_id: UUID | None,
        action: str,
        natural_language_query: str | None = None,
        generated_query: str | None = None,
        row_count: int | None = None,
        duration_ms: int | None = None,
        trace_id: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            org_id=org_id,
            project_id=project_id,
            user_id=user_id,
            datasource_id=datasource_id,
            action=action,
            natural_language_query=natural_language_query,
            generated_query=generated_query,
            row_count=row_count,
            duration_ms=duration_ms,
            trace_id=trace_id,
            metadata_=metadata,
        )
        db.add(entry)
        await db.flush()
        return entry


audit_service = AuditService()
