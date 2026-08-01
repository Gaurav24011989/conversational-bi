from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_current_user, get_password_hash, verify_password
from app.database import get_db
from app.i18n import is_supported_locale, t
from app.models import Organization, Project, ProjectMembership, User, UserRole
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserLocaleUpdate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Organization).where(Organization.slug == data.org_slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Organization slug already exists")

    org = Organization(name=data.org_name, slug=data.org_slug)
    db.add(org)
    await db.flush()

    user = User(
        org_id=org.id,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()

    default_project = Project(org_id=org.id, name="Default Project", description="Auto-created default workspace")
    db.add(default_project)
    await db.flush()

    membership = ProjectMembership(
        user_id=user.id,
        project_id=default_project.id,
        role=UserRole.ORG_ADMIN,
    )
    db.add(membership)
    await db.flush()

    token = create_access_token({"sub": str(user.id), "org_id": str(org.id)})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": str(user.id), "org_id": str(user.org_id)})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me/locale", response_model=UserResponse)
async def update_locale(
    data: UserLocaleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_supported_locale(data.preferred_locale):
        locale = current_user.preferred_locale or "en"
        raise HTTPException(
            status_code=400,
            detail=t("errors.unsupported_locale", locale, locale=data.preferred_locale),
        )
    current_user.preferred_locale = data.preferred_locale
    await db.flush()
    return current_user
