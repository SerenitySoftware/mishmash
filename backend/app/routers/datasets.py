import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.dataset import Dataset, DatasetVersion
from app.models.user import User
from app.schemas.dataset import (
    DatasetCreate,
    DatasetForkRequest,
    DatasetListOut,
    DatasetOut,
    DatasetReferenceCreate,
    DatasetReferenceOut,
    DatasetUpdate,
    DatasetVersionOut,
    PresignedUrlOut,
    UploadCompleteRequest,
)
from app.services import dataset_service

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("", response_model=DatasetOut, status_code=201)
async def create_dataset(
    body: DatasetCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dataset = await dataset_service.create_dataset(
        db, owner_id=user.id, name=body.name, description=body.description,
        tags=body.tags, format=body.format, license=body.license,
    )
    return dataset


@router.get("", response_model=DatasetListOut)
async def list_datasets(
    q: str | None = None,
    tags: list[str] | None = Query(None),
    owner: str | None = None,
    sort: str = Query("updated", pattern="^(updated|stars|downloads|created)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await dataset_service.list_datasets(
        db, query=q, tags=tags, owner_username=owner, sort=sort,
        page=page, page_size=page_size,
        requesting_user_id=user.id if user else None,
    )
    return DatasetListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{slug}", response_model=DatasetOut)
async def get_dataset(slug: str, db: AsyncSession = Depends(get_db)):
    dataset = await dataset_service.get_dataset_by_slug(db, slug)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.put("/{dataset_id}", response_model=DatasetOut)
async def update_dataset(
    dataset_id: uuid.UUID,
    body: DatasetUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dataset = await dataset_service.get_dataset_by_id(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your dataset")

    if body.name is not None:
        dataset.name = body.name
    if body.description is not None:
        dataset.description = body.description
    if body.tags is not None:
        dataset.tags = body.tags
    if body.license is not None:
        dataset.license = body.license
    await db.flush()
    return dataset


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dataset = await dataset_service.get_dataset_by_id(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your dataset")
    await db.delete(dataset)
    await db.flush()


@router.get("/{dataset_id}/versions", response_model=list[DatasetVersionOut])
async def list_versions(dataset_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    dataset = await dataset_service.get_dataset_by_id(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset.versions


@router.post("/{dataset_id}/upload", response_model=PresignedUrlOut)
async def get_upload_url(
    dataset_id: uuid.UUID,
    filename: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dataset = await dataset_service.get_dataset_by_id(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your dataset")
    try:
        url, key, expires = await dataset_service.get_presigned_upload(db, dataset_id, filename)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PresignedUrlOut(upload_url=url, storage_key=key, expires_in=expires)


@router.post("/{dataset_id}/upload/complete", response_model=DatasetVersionOut, status_code=201)
async def complete_upload(
    dataset_id: uuid.UUID,
    body: UploadCompleteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dataset = await dataset_service.get_dataset_by_id(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your dataset")

    try:
        version = await dataset_service.complete_upload(
            db, dataset_id, body.storage_key, body.file_size_bytes, user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from app.workers.tasks import process_upload_task
    process_upload_task.delay(
        str(dataset_id), str(version.id), body.storage_key, dataset.format,
    )

    return version


@router.get("/{dataset_id}/preview")
async def get_preview(
    dataset_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await dataset_service.get_dataset_preview(db, dataset_id, limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{dataset_id}/download")
async def get_download_url(
    dataset_id: uuid.UUID,
    version: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    dataset = await dataset_service.get_dataset_by_id(db, dataset_id)
    if not dataset or not dataset.versions:
        raise HTTPException(status_code=404, detail="Dataset not found or no versions")

    if version:
        ver = next((v for v in dataset.versions if v.version == version), None)
    else:
        ver = dataset.versions[-1]
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")

    from app.services.storage import create_presigned_download_url
    from app.config import settings
    url = create_presigned_download_url(settings.s3_datasets_bucket, ver.storage_key)

    dataset.download_count += 1
    await db.flush()

    return {"download_url": url, "expires_in": 3600}


@router.post("/{dataset_id}/fork", response_model=DatasetOut, status_code=201)
async def fork_dataset(
    dataset_id: uuid.UUID,
    body: DatasetForkRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    original = await dataset_service.get_dataset_by_id(db, dataset_id)
    if not original:
        raise HTTPException(status_code=404, detail="Dataset not found")

    fork_name = body.name or f"{original.name} (fork)"
    forked = await dataset_service.create_dataset(
        db, owner_id=user.id, name=fork_name,
        description=body.description or original.description,
        tags=list(original.tags), format=original.format,
        license=original.license, forked_from_id=original.id,
    )

    # Copy latest version reference
    if original.versions:
        latest = original.versions[-1]
        fork_version = DatasetVersion(
            dataset_id=forked.id,
            version=1,
            storage_key=latest.storage_key,
            file_size_bytes=latest.file_size_bytes,
            checksum_sha256=latest.checksum_sha256,
            row_count=latest.row_count,
            column_meta=latest.column_meta,
            created_by=user.id,
        )
        db.add(fork_version)
        forked.row_count = latest.row_count
        forked.column_meta = latest.column_meta

    original.fork_count += 1
    await db.flush()

    # Add reference
    await dataset_service.add_reference(
        db, source_id=forked.id, target_id=original.id,
        relationship_type="forked_from", description=f"Forked from {original.name}",
    )

    return forked


@router.post("/{dataset_id}/references", response_model=DatasetReferenceOut, status_code=201)
async def add_reference(
    dataset_id: uuid.UUID,
    body: DatasetReferenceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dataset = await dataset_service.get_dataset_by_id(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your dataset")

    ref = await dataset_service.add_reference(
        db, source_id=dataset_id, target_id=body.target_id,
        relationship_type=body.relationship_type, description=body.description,
    )
    return ref


@router.get("/{dataset_id}/references", response_model=list[DatasetReferenceOut])
async def get_references(dataset_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await dataset_service.get_references(db, dataset_id)
