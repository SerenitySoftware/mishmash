import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.models.publication import Publication
from app.models.user import User
from app.schemas.user import UserProfileOut
from app.schemas.dataset import DatasetOut, DatasetListOut
from app.schemas.analysis import AnalysisOut, AnalysisListOut
from app.schemas.publication import PublicationOut, PublicationListOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/{username}", response_model=UserProfileOut)
async def get_user_profile(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ds_count = (await db.execute(
        select(func.count()).select_from(Dataset).where(Dataset.owner_id == user.id)
    )).scalar()
    an_count = (await db.execute(
        select(func.count()).select_from(Analysis).where(Analysis.owner_id == user.id)
    )).scalar()
    pub_count = (await db.execute(
        select(func.count()).select_from(Publication).where(Publication.author_id == user.id)
    )).scalar()

    return UserProfileOut(
        id=user.id,
        username=user.username,
        name=user.name,
        bio=user.bio,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        dataset_count=ds_count,
        analysis_count=an_count,
        publication_count=pub_count,
    )


@router.get("/{username}/datasets", response_model=DatasetListOut)
async def get_user_datasets(
    username: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total = (await db.execute(
        select(func.count()).select_from(Dataset).where(Dataset.owner_id == user.id)
    )).scalar()
    stmt = (
        select(Dataset)
        .where(Dataset.owner_id == user.id)
        .order_by(Dataset.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(stmt)).scalars().all()
    return DatasetListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{username}/analyses", response_model=AnalysisListOut)
async def get_user_analyses(
    username: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from sqlalchemy.orm import selectinload
    total = (await db.execute(
        select(func.count()).select_from(Analysis).where(Analysis.owner_id == user.id)
    )).scalar()
    stmt = (
        select(Analysis)
        .options(selectinload(Analysis.datasets))
        .where(Analysis.owner_id == user.id)
        .order_by(Analysis.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(stmt)).scalars().all()
    return AnalysisListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{username}/publications", response_model=PublicationListOut)
async def get_user_publications(
    username: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from sqlalchemy.orm import selectinload
    total = (await db.execute(
        select(func.count()).select_from(Publication).where(Publication.author_id == user.id)
    )).scalar()
    stmt = (
        select(Publication)
        .options(selectinload(Publication.references))
        .where(Publication.author_id == user.id)
        .order_by(Publication.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(stmt)).scalars().all()
    return PublicationListOut(items=items, total=total, page=page, page_size=page_size)
