from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_datasource_access, require_project_access
from app.core.security import get_current_user
from app.database import get_db
from app.models import Project, User
from app.schemas import (
    ConnectionTestResponse,
    DataSourceCreate,
    DataSourceResponse,
    SchemaSnapshotResponse,
)
from app.services.datasource_service import datasource_service
from app.services.schema_service import schema_service

router = APIRouter(tags=["datasources"])


@router.post("/projects/{project_id}/datasources", response_model=DataSourceResponse, status_code=201)
async def create_datasource(
    project_id: UUID,
    data: DataSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_project_access(db, current_user, project_id, "configure_datasource")
    ds = await datasource_service.create(db, project_id, data)
    return datasource_service.to_response(ds)


@router.get("/projects/{project_id}/datasources", response_model=list[DataSourceResponse])
async def list_datasources(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_project_access(db, current_user, project_id, "view")
    sources = await datasource_service.list_by_project(db, project_id)
    return [datasource_service.to_response(ds) for ds in sources]


@router.get("/datasources/{datasource_id}", response_model=DataSourceResponse)
async def get_datasource(
    datasource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds, _ = await require_datasource_access(db, current_user, datasource_id, "view")
    return datasource_service.to_response(ds)


@router.post("/datasources/{datasource_id}/test", response_model=ConnectionTestResponse)
async def test_datasource(
    datasource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_datasource_access(db, current_user, datasource_id, "view")
    return await datasource_service.test_connection(db, datasource_id)


@router.post("/datasources/{datasource_id}/schema/refresh", response_model=SchemaSnapshotResponse)
async def refresh_schema(
    datasource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds, _ = await require_datasource_access(db, current_user, datasource_id, "configure_datasource")
    from sqlalchemy import select
    from app.models import Project

    project_result = await db.execute(select(Project).where(Project.id == ds.project_id))
    project = project_result.scalar_one()
    snapshot = await schema_service.refresh_schema(db, datasource_id, project.org_id, project.id)
    return snapshot


@router.get("/datasources/{datasource_id}/schema", response_model=SchemaSnapshotResponse)
async def get_schema(
    datasource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_datasource_access(db, current_user, datasource_id, "view")
    snapshot = await schema_service.get_latest_schema(db, datasource_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No schema snapshot found. Run refresh first.")
    return snapshot
