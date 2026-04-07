import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.models.star import Star
from app.models.user import User

router = APIRouter(prefix="/api/stars", tags=["stars"])


@router.post("/{target_type}/{target_id}", status_code=201)
async def star(
    target_type: str,
    target_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if target_type not in ("dataset", "analysis"):
        raise HTTPException(status_code=400, detail="target_type must be 'dataset' or 'analysis'")

    # Check target exists
    if target_type == "dataset":
        target = await db.get(Dataset, target_id)
    else:
        target = await db.get(Analysis, target_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"{target_type} not found")

    # Check not already starred
    existing = await db.execute(
        select(Star).where(
            Star.user_id == user.id,
            Star.target_type == target_type,
            Star.target_id == target_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already starred")

    star = Star(user_id=user.id, target_type=target_type, target_id=target_id)
    db.add(star)
    target.star_count += 1
    await db.flush()
    return {"starred": True, "star_count": target.star_count}


@router.delete("/{target_type}/{target_id}", status_code=200)
async def unstar(
    target_type: str,
    target_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if target_type not in ("dataset", "analysis"):
        raise HTTPException(status_code=400, detail="target_type must be 'dataset' or 'analysis'")

    result = await db.execute(
        select(Star).where(
            Star.user_id == user.id,
            Star.target_type == target_type,
            Star.target_id == target_id,
        )
    )
    star = result.scalar_one_or_none()
    if not star:
        raise HTTPException(status_code=404, detail="Not starred")

    await db.delete(star)

    if target_type == "dataset":
        target = await db.get(Dataset, target_id)
    else:
        target = await db.get(Analysis, target_id)
    if target and target.star_count > 0:
        target.star_count -= 1

    await db.flush()
    return {"starred": False, "star_count": target.star_count if target else 0}


@router.get("/{target_type}/{target_id}/check")
async def check_star(
    target_type: str,
    target_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Star).where(
            Star.user_id == user.id,
            Star.target_type == target_type,
            Star.target_id == target_id,
        )
    )
    return {"starred": result.scalar_one_or_none() is not None}
