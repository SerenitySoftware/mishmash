import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.api_key import ApiKey, generate_api_key
from app.models.user import User

router = APIRouter(prefix="/api/keys", tags=["api_keys"])


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ApiKeyOut(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class ApiKeyCreated(BaseModel):
    id: uuid.UUID
    name: str
    key: str  # Only shown once at creation time
    key_prefix: str


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


@router.post("", response_model=ApiKeyCreated, status_code=201)
async def create_api_key(
    body: ApiKeyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Limit keys per user
    existing = (await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id, ApiKey.is_active == True)  # noqa: E712
    )).scalars().all()
    if len(existing) >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 active API keys")

    raw_key = generate_api_key()
    api_key = ApiKey(
        user_id=user.id,
        name=body.name,
        key_prefix=raw_key[:12],
        key_hash=hash_key(raw_key),
    )
    db.add(api_key)
    await db.flush()

    return ApiKeyCreated(id=api_key.id, name=api_key.name, key=raw_key, key_prefix=api_key.key_prefix)


@router.get("", response_model=list[ApiKeyOut])
async def list_api_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    key = await db.get(ApiKey, key_id)
    if not key or key.user_id != user.id:
        raise HTTPException(status_code=404, detail="API key not found")
    key.is_active = False
    await db.flush()
