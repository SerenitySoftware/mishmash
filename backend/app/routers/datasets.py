import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.dataset import (
    DatasetCreate,
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

# TODO: Replace with real auth dependency
DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("", response_model=DatasetOut, status_code=201)
async def create_dataset(body: DatasetCreate, db: AsyncSession = Depends(get_db)):
    dataset = await dataset_service.create_dataset(
        db, owner_id=DEMO_USER_ID, name=body.name, description=body.description,
        tags=body.tags, format=body.format,
    )
    return dataset


@router.get("", response_model=DatasetListOut)
async def list_datasets(
    q: str | None = None,
    tags: list[str] | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await dataset_service.list_datasets(db, query=q, tags=tags, page=page, page_size=page_size)
    return DatasetListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{slug}", response_model=DatasetOut)
async def get_dataset(slug: str, db: AsyncSession = Depends(get_db)):
    dataset = await dataset_service.get_dataset_by_slug(db, slug)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


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
    db: AsyncSession = Depends(get_db),
):
    try:
        url, key, expires = await dataset_service.get_presigned_upload(db, dataset_id, filename)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PresignedUrlOut(upload_url=url, storage_key=key, expires_in=expires)


@router.post("/{dataset_id}/upload/complete", response_model=DatasetVersionOut, status_code=201)
async def complete_upload(
    dataset_id: uuid.UUID,
    body: UploadCompleteRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        version = await dataset_service.complete_upload(
            db, dataset_id, body.storage_key, body.file_size_bytes, DEMO_USER_ID,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Trigger background processing
    from app.workers.tasks import process_upload_task
    dataset = await dataset_service.get_dataset_by_id(db, dataset_id)
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


@router.post("/{dataset_id}/references", response_model=DatasetReferenceOut, status_code=201)
async def add_reference(
    dataset_id: uuid.UUID,
    body: DatasetReferenceCreate,
    db: AsyncSession = Depends(get_db),
):
    ref = await dataset_service.add_reference(
        db, source_id=dataset_id, target_id=body.target_id,
        relationship_type=body.relationship_type, description=body.description,
    )
    return ref


@router.get("/{dataset_id}/references", response_model=list[DatasetReferenceOut])
async def get_references(dataset_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await dataset_service.get_references(db, dataset_id)
