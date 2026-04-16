import io
import re
import uuid
from typing import Any

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dataset import Dataset, DatasetReference, DatasetVersion
from app.models.user import User
from app.services.storage import (
    create_presigned_download_url,
    create_presigned_upload_url,
    download_file,
    generate_upload_key,
)
from app.config import settings


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug


async def create_dataset(
    db: AsyncSession, owner_id: uuid.UUID, name: str, description: str | None,
    tags: list[str], format: str, license: str | None = None,
    forked_from_id: uuid.UUID | None = None,
) -> Dataset:
    base_slug = slugify(name)
    slug = base_slug

    counter = 1
    while True:
        existing = await db.execute(select(Dataset).where(Dataset.slug == slug))
        if existing.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    dataset = Dataset(
        owner_id=owner_id,
        name=name,
        slug=slug,
        description=description,
        tags=tags,
        format=format,
        license=license,
        forked_from_id=forked_from_id,
    )
    db.add(dataset)
    await db.flush()
    return dataset


async def list_datasets(
    db: AsyncSession, query: str | None = None, tags: list[str] | None = None,
    owner_username: str | None = None, sort: str = "updated",
    page: int = 1, page_size: int = 20,
    requesting_user_id: uuid.UUID | None = None,
) -> tuple[list[Dataset], int]:
    stmt = select(Dataset).options(selectinload(Dataset.owner))
    count_stmt = select(func.count()).select_from(Dataset)

    # Privacy: only show public datasets, or the user's own private ones
    if requesting_user_id:
        privacy_filter = (Dataset.is_public == True) | (Dataset.owner_id == requesting_user_id)  # noqa: E712
    else:
        privacy_filter = Dataset.is_public == True  # noqa: E712
    stmt = stmt.where(privacy_filter)
    count_stmt = count_stmt.where(privacy_filter)

    if query:
        search_filter = Dataset.name.ilike(f"%{query}%") | Dataset.description.ilike(f"%{query}%")
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    if tags:
        stmt = stmt.where(Dataset.tags.overlap(tags))
        count_stmt = count_stmt.where(Dataset.tags.overlap(tags))

    if owner_username:
        stmt = stmt.join(User).where(User.username == owner_username)
        count_stmt = count_stmt.join(User).where(User.username == owner_username)

    total = (await db.execute(count_stmt)).scalar()

    order_map = {
        "updated": Dataset.updated_at.desc(),
        "stars": Dataset.star_count.desc(),
        "downloads": Dataset.download_count.desc(),
        "created": Dataset.created_at.desc(),
    }
    stmt = stmt.order_by(order_map.get(sort, Dataset.updated_at.desc()))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_dataset_by_slug(db: AsyncSession, slug: str) -> Dataset | None:
    stmt = (
        select(Dataset)
        .where(Dataset.slug == slug)
        .options(selectinload(Dataset.versions), selectinload(Dataset.owner))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_dataset_by_id(db: AsyncSession, dataset_id: uuid.UUID) -> Dataset | None:
    stmt = (
        select(Dataset)
        .where(Dataset.id == dataset_id)
        .options(selectinload(Dataset.versions), selectinload(Dataset.owner))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_presigned_upload(
    db: AsyncSession, dataset_id: uuid.UUID, filename: str,
) -> tuple[str, str, int]:
    dataset = await get_dataset_by_id(db, dataset_id)
    if not dataset:
        raise ValueError("Dataset not found")

    version = dataset.current_version
    key = generate_upload_key(dataset_id, version, filename)
    url = create_presigned_upload_url(key)
    return url, key, 900


async def complete_upload(
    db: AsyncSession, dataset_id: uuid.UUID, storage_key: str,
    file_size_bytes: int | None, user_id: uuid.UUID,
) -> DatasetVersion:
    dataset = await get_dataset_by_id(db, dataset_id)
    if not dataset:
        raise ValueError("Dataset not found")

    version = DatasetVersion(
        dataset_id=dataset_id,
        version=dataset.current_version,
        storage_key=storage_key,
        file_size_bytes=file_size_bytes,
        created_by=user_id,
    )
    db.add(version)

    dataset.current_version += 1
    await db.flush()
    return version


async def get_dataset_preview(
    db: AsyncSession, dataset_id: uuid.UUID, limit: int = 100,
) -> dict[str, Any]:
    dataset = await get_dataset_by_id(db, dataset_id)
    if not dataset or not dataset.versions:
        raise ValueError("Dataset not found or has no versions")

    latest = dataset.versions[-1]
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=f".{dataset.format}", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        download_file(settings.s3_datasets_bucket, latest.storage_key, tmp_path)

        if dataset.format == "csv":
            df = pd.read_csv(tmp_path, nrows=limit)
        elif dataset.format == "json":
            df = pd.read_json(tmp_path, lines=True, nrows=limit)
        elif dataset.format == "parquet":
            df = pd.read_parquet(tmp_path).head(limit)
        else:
            raise ValueError(f"Unsupported format: {dataset.format}")

        return {
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "rows": df.where(df.notna(), None).to_dict(orient="records"),
            "total_rows": latest.row_count or len(df),
        }
    finally:
        os.unlink(tmp_path)


async def add_reference(
    db: AsyncSession, source_id: uuid.UUID, target_id: uuid.UUID,
    relationship_type: str, description: str | None,
) -> DatasetReference:
    ref = DatasetReference(
        source_id=source_id,
        target_id=target_id,
        relationship_type=relationship_type,
        description=description,
    )
    db.add(ref)
    await db.flush()
    return ref


async def get_references(
    db: AsyncSession, dataset_id: uuid.UUID,
) -> list[DatasetReference]:
    stmt = select(DatasetReference).where(
        (DatasetReference.source_id == dataset_id) | (DatasetReference.target_id == dataset_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
