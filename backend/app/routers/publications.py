import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.publication import Publication, PublicationReference
from app.schemas.publication import (
    PublicationCreate,
    PublicationListOut,
    PublicationOut,
    PublicationUpdate,
)

router = APIRouter(prefix="/api/publications", tags=["publications"])

DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return re.sub(r"-+", "-", slug)


@router.post("", response_model=PublicationOut, status_code=201)
async def create_publication(body: PublicationCreate, db: AsyncSession = Depends(get_db)):
    base_slug = slugify(body.title)
    slug = base_slug
    counter = 1
    while True:
        existing = await db.execute(select(Publication).where(Publication.slug == slug))
        if existing.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    pub = Publication(
        author_id=DEMO_USER_ID,
        title=body.title,
        slug=slug,
        body=body.body,
    )
    db.add(pub)
    await db.flush()

    for ref in body.references:
        db.add(PublicationReference(
            publication_id=pub.id,
            ref_type=ref.ref_type,
            ref_id=ref.ref_id,
        ))
    await db.flush()

    stmt = select(Publication).where(Publication.id == pub.id).options(selectinload(Publication.references))
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("", response_model=PublicationListOut)
async def list_publications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count()).select_from(Publication))).scalar()
    stmt = (
        select(Publication)
        .options(selectinload(Publication.references))
        .order_by(Publication.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return PublicationListOut(items=result.scalars().all(), total=total, page=page, page_size=page_size)


@router.get("/{slug}", response_model=PublicationOut)
async def get_publication(slug: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Publication).where(Publication.slug == slug).options(selectinload(Publication.references))
    result = await db.execute(stmt)
    pub = result.scalar_one_or_none()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")
    return pub


@router.put("/{pub_id}", response_model=PublicationOut)
async def update_publication(
    pub_id: uuid.UUID, body: PublicationUpdate, db: AsyncSession = Depends(get_db),
):
    stmt = select(Publication).where(Publication.id == pub_id).options(selectinload(Publication.references))
    result = await db.execute(stmt)
    pub = result.scalar_one_or_none()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")

    if body.title is not None:
        pub.title = body.title
    if body.body is not None:
        pub.body = body.body

    if body.references is not None:
        for ref in pub.references:
            await db.delete(ref)
        for ref in body.references:
            db.add(PublicationReference(
                publication_id=pub.id, ref_type=ref.ref_type, ref_id=ref.ref_id,
            ))

    await db.flush()
    return pub
