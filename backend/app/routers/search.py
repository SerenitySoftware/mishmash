"""Unified search across datasets, analyses, and publications."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.models.publication import Publication

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchResultItem(BaseModel):
    type: str  # 'dataset', 'analysis', 'publication'
    id: str
    title: str
    description: str | None
    slug: str | None
    owner_name: str | None
    relevance: float | None

    model_config = {"from_attributes": True}


class SearchResults(BaseModel):
    query: str
    items: list[SearchResultItem]
    total: int


@router.get("", response_model=SearchResults)
async def unified_search(
    q: str = Query(..., min_length=1),
    type: str = Query("all", pattern="^(all|dataset|analysis|publication)$"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search across all entity types using full-text search with ranking."""
    results = []

    ts_query = func.plainto_tsquery("english", q)

    if type in ("all", "dataset"):
        # Use the GIN index for datasets
        ts_vector = func.to_tsvector(
            "english",
            func.concat(Dataset.name, " ", func.coalesce(Dataset.description, ""))
        )
        stmt = (
            select(
                Dataset.id,
                Dataset.name,
                Dataset.description,
                Dataset.slug,
                func.ts_rank(ts_vector, ts_query).label("rank"),
            )
            .where(ts_vector.op("@@")(ts_query))
            .where(Dataset.is_public == True)  # noqa: E712
            .order_by(text("rank DESC"))
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        for row in rows:
            results.append(SearchResultItem(
                type="dataset", id=str(row.id), title=row.name,
                description=row.description, slug=row.slug,
                owner_name=None, relevance=float(row.rank),
            ))

    if type in ("all", "analysis"):
        ts_vector = func.to_tsvector(
            "english",
            func.concat(Analysis.title, " ", func.coalesce(Analysis.description, ""))
        )
        stmt = (
            select(
                Analysis.id,
                Analysis.title,
                Analysis.description,
                func.ts_rank(ts_vector, ts_query).label("rank"),
            )
            .where(ts_vector.op("@@")(ts_query))
            .order_by(text("rank DESC"))
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        for row in rows:
            results.append(SearchResultItem(
                type="analysis", id=str(row.id), title=row.title,
                description=row.description, slug=None,
                owner_name=None, relevance=float(row.rank),
            ))

    if type in ("all", "publication"):
        ts_vector = func.to_tsvector(
            "english",
            func.concat(Publication.title, " ", func.coalesce(Publication.body, ""))
        )
        stmt = (
            select(
                Publication.id,
                Publication.title,
                Publication.slug,
                func.ts_rank(ts_vector, ts_query).label("rank"),
            )
            .where(ts_vector.op("@@")(ts_query))
            .order_by(text("rank DESC"))
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        for row in rows:
            results.append(SearchResultItem(
                type="publication", id=str(row.id), title=row.title,
                description=None, slug=row.slug,
                owner_name=None, relevance=float(row.rank),
            ))

    # Sort all results by relevance
    results.sort(key=lambda x: x.relevance or 0, reverse=True)
    results = results[:limit]

    return SearchResults(query=q, items=results, total=len(results))
