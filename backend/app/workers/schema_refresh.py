import asyncio
from uuid import UUID

from app.database import async_session_factory
from app.services.schema_service import schema_service
from app.workers.celery_app import celery_app


@celery_app.task(name="schema.refresh", bind=True, max_retries=3)
def refresh_schema_task(self, datasource_id: str, org_id: str, project_id: str):
    async def _run():
        async with async_session_factory() as db:
            try:
                await schema_service.refresh_schema(
                    db, UUID(datasource_id), UUID(org_id), UUID(project_id)
                )
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    try:
        asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60) from exc
