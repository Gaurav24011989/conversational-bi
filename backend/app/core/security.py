from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception from None

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


class OIDCProvider:
    """Hook points for OIDC SSO integration (Auth0, Azure AD, Google)."""

    def __init__(self) -> None:
        self.enabled = settings.oidc_enabled
        self.client_id = settings.oidc_client_id
        self.client_secret = settings.oidc_client_secret
        self.discovery_url = settings.oidc_discovery_url

    async def get_authorization_url(self, redirect_uri: str, state: str) -> str | None:
        if not self.enabled:
            return None
        # Placeholder for Authlib OAuth client integration
        return f"{self.discovery_url}?client_id={self.client_id}&redirect_uri={redirect_uri}&state={state}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        # Placeholder: integrate Authlib OAuth2Session here
        return {"sub": None, "email": None}


oidc_provider = OIDCProvider()
