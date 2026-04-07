import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.analysis import Analysis, AnalysisDataset, AnalysisRun
from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisListOut,
    AnalysisOut,
    AnalysisRunOut,
    AnalysisUpdate,
)

router = APIRouter(prefix="/api/analyses", tags=["analyses"])

DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("", response_model=AnalysisOut, status_code=201)
async def create_analysis(body: AnalysisCreate, db: AsyncSession = Depends(get_db)):
    analysis = Analysis(
        owner_id=DEMO_USER_ID,
        title=body.title,
        description=body.description,
        language=body.language,
        source_code=body.source_code,
    )
    db.add(analysis)
    await db.flush()

    for ds in body.datasets:
        link = AnalysisDataset(
            analysis_id=analysis.id,
            dataset_id=ds.dataset_id,
            version=ds.version,
            alias=ds.alias,
        )
        db.add(link)

    await db.flush()
    # Reload with relationships
    stmt = select(Analysis).where(Analysis.id == analysis.id).options(selectinload(Analysis.datasets))
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("", response_model=AnalysisListOut)
async def list_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count()).select_from(Analysis))).scalar()
    stmt = (
        select(Analysis)
        .options(selectinload(Analysis.datasets))
        .order_by(Analysis.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    return AnalysisListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{analysis_id}", response_model=AnalysisOut)
async def get_analysis(analysis_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Analysis).where(Analysis.id == analysis_id).options(selectinload(Analysis.datasets))
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.put("/{analysis_id}", response_model=AnalysisOut)
async def update_analysis(
    analysis_id: uuid.UUID, body: AnalysisUpdate, db: AsyncSession = Depends(get_db),
):
    stmt = select(Analysis).where(Analysis.id == analysis_id).options(selectinload(Analysis.datasets))
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if body.title is not None:
        analysis.title = body.title
    if body.description is not None:
        analysis.description = body.description
    if body.source_code is not None:
        analysis.source_code = body.source_code

    if body.datasets is not None:
        # Replace dataset links
        for link in analysis.datasets:
            await db.delete(link)
        for ds in body.datasets:
            db.add(AnalysisDataset(
                analysis_id=analysis.id, dataset_id=ds.dataset_id,
                version=ds.version, alias=ds.alias,
            ))

    await db.flush()
    return analysis


@router.post("/{analysis_id}/run", response_model=AnalysisRunOut, status_code=201)
async def trigger_run(analysis_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Analysis).where(Analysis.id == analysis_id).options(selectinload(Analysis.datasets))
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    run = AnalysisRun(analysis_id=analysis.id, triggered_by=DEMO_USER_ID)
    db.add(run)
    await db.flush()

    # Prepare dataset file info for the runner
    from app.services.dataset_service import get_dataset_by_id
    from app.config import settings

    dataset_files = []
    for link in analysis.datasets:
        ds = await get_dataset_by_id(db, link.dataset_id)
        if ds and ds.versions:
            # Use pinned version or latest
            if link.version:
                version = next((v for v in ds.versions if v.version == link.version), ds.versions[-1])
            else:
                version = ds.versions[-1]
            dataset_files.append({
                "storage_key": version.storage_key,
                "bucket": settings.s3_datasets_bucket,
                "alias": link.alias or ds.slug,
                "format": ds.format,
            })

    # Queue the task
    from app.workers.tasks import run_analysis_task
    run_analysis_task.delay(
        str(analysis.id), str(run.id), analysis.language,
        analysis.source_code, dataset_files,
    )

    analysis.status = "queued"
    await db.flush()
    return run


@router.get("/{analysis_id}/runs", response_model=list[AnalysisRunOut])
async def list_runs(analysis_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(AnalysisRun)
        .where(AnalysisRun.analysis_id == analysis_id)
        .order_by(AnalysisRun.created_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{analysis_id}/runs/{run_id}", response_model=AnalysisRunOut)
async def get_run(analysis_id: uuid.UUID, run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(AnalysisRun).where(
        AnalysisRun.id == run_id, AnalysisRun.analysis_id == analysis_id
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
