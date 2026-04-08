"""Shared FastAPI dependencies."""
import hashlib
import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.api_key import ApiKey
from app.models.user import User
from app.services.auth import decode_access_token, get_user_by_id


async def _resolve_token(token: str, db: AsyncSession) -> User | None:
    """Resolve a bearer token — either a JWT or an API key."""
    # Try JWT first
    user_id = decode_access_token(token)
    if user_id is not None:
        return await get_user_by_id(db, user_id)

    # Try API key (starts with msh_)
    if token.startswith("msh_"):
        key_hash = hashlib.sha256(token.encode()).hexdigest()
        result = await db.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)  # noqa: E712
        )
        api_key = result.scalar_one_or_none()
        if api_key:
            return await get_user_by_id(db, api_key.user_id)

    return None


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ", 1)[1]
    user = await _resolve_token(token, db)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_optional_user(
    request: Request, db: AsyncSession = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None if not authenticated."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]
    user = await _resolve_token(token, db)
    if not user or not user.is_active:
        return None
    return user
