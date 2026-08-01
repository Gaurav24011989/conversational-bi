from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DataSource, Project, ProjectMembership, User, UserRole


@dataclass
class TenantContext:
    org_id: UUID
    user_id: UUID
    project_id: UUID | None = None


ROLE_PERMISSIONS = {
    UserRole.ORG_ADMIN: {"manage_org", "manage_project", "configure_datasource", "query", "view"},
    UserRole.PROJECT_ADMIN: {"manage_project", "configure_datasource", "query", "view"},
    UserRole.ANALYST: {"query", "view"},
    UserRole.VIEWER: {"view", "query"},
}


async def get_project_membership(
    db: AsyncSession, user_id: UUID, project_id: UUID
) -> ProjectMembership | None:
    result = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.user_id == user_id,
            ProjectMembership.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def require_project_access(
    db: AsyncSession,
    user: User,
    project_id: UUID,
    permission: str,
) -> ProjectMembership:
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.org_id != user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant access denied")

    membership = await get_project_membership(db, user.id, project_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No project access")

    allowed = ROLE_PERMISSIONS.get(membership.role, set())
    if permission not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{permission}' denied for role {membership.role.value}",
        )
    return membership


async def require_datasource_access(
    db: AsyncSession,
    user: User,
    datasource_id: UUID,
    permission: str,
) -> tuple[DataSource, ProjectMembership]:
    ds_result = await db.execute(select(DataSource).where(DataSource.id == datasource_id))
    datasource = ds_result.scalar_one_or_none()
    if not datasource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")

    membership = await require_project_access(db, user, datasource.project_id, permission)

    if membership.datasource_id and membership.datasource_id != datasource_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to assigned data source",
        )
    return datasource, membership
