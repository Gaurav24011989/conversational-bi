from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_project_access
from app.core.security import get_current_user
from app.database import get_db
from app.models import Project, ProjectMembership, User, UserRole
from app.schemas import ProjectCreate, ProjectResponse

router = APIRouter(tags=["projects"])


@router.get("/orgs/{org_id}/projects", response_model=list[ProjectResponse])
async def list_projects(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.org_id != org_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")
    result = await db.execute(select(Project).where(Project.org_id == org_id))
    return list(result.scalars().all())


@router.post("/orgs/{org_id}/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    org_id: UUID,
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.org_id != org_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")
    project = Project(org_id=org_id, name=data.name, description=data.description)
    db.add(project)
    await db.flush()

    membership = ProjectMembership(
        user_id=current_user.id,
        project_id=project.id,
        role=UserRole.PROJECT_ADMIN,
    )
    db.add(membership)
    await db.flush()
    return project


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_project_access(db, current_user, project_id, "view")
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
