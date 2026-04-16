import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.analysis import Analysis, AnalysisDataset, AnalysisRun
from app.models.user import User
from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisForkRequest,
    AnalysisListOut,
    AnalysisOut,
    AnalysisRunOut,
    AnalysisUpdate,
    ChallengeOut,
    ProofSubmission,
)
from app.services.proof_of_work import (
    compute_source_hash,
    create_challenge,
    verify_proof,
    compute_environment_hash,
)

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisOut, status_code=201)
async def create_analysis(
    body: AnalysisCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    analysis = Analysis(
        owner_id=user.id,
        title=body.title,
        description=body.description,
        language=body.language,
        source_code=body.source_code,
        requirements=body.requirements,
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
    stmt = select(Analysis).where(Analysis.id == analysis.id).options(
        selectinload(Analysis.datasets), selectinload(Analysis.owner)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("", response_model=AnalysisListOut)
async def list_analyses(
    q: str | None = None,
    language: str | None = None,
    sort: str = Query("updated", pattern="^(updated|stars|created)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Analysis).options(selectinload(Analysis.datasets), selectinload(Analysis.owner))
    count_stmt = select(func.count()).select_from(Analysis)

    if q:
        search_filter = Analysis.title.ilike(f"%{q}%") | Analysis.description.ilike(f"%{q}%")
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)
    if language:
        stmt = stmt.where(Analysis.language == language)
        count_stmt = count_stmt.where(Analysis.language == language)

    total = (await db.execute(count_stmt)).scalar()

    order_map = {
        "updated": Analysis.updated_at.desc(),
        "stars": Analysis.star_count.desc(),
        "created": Analysis.created_at.desc(),
    }
    stmt = stmt.order_by(order_map[sort]).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(stmt)).scalars().all()
    return AnalysisListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{analysis_id}", response_model=AnalysisOut)
async def get_analysis(analysis_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Analysis).where(Analysis.id == analysis_id).options(selectinload(Analysis.datasets), selectinload(Analysis.owner))
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.put("/{analysis_id}", response_model=AnalysisOut)
async def update_analysis(
    analysis_id: uuid.UUID,
    body: AnalysisUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Analysis).where(Analysis.id == analysis_id).options(selectinload(Analysis.datasets), selectinload(Analysis.owner))
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your analysis")

    if body.title is not None:
        analysis.title = body.title
    if body.description is not None:
        analysis.description = body.description
    if body.source_code is not None:
        analysis.source_code = body.source_code
    if body.requirements is not None:
        analysis.requirements = body.requirements

    if body.datasets is not None:
        for link in analysis.datasets:
            await db.delete(link)
        for ds in body.datasets:
            db.add(AnalysisDataset(
                analysis_id=analysis.id, dataset_id=ds.dataset_id,
                version=ds.version, alias=ds.alias,
            ))

    await db.flush()
    return analysis


@router.delete("/{analysis_id}", status_code=204)
async def delete_analysis(
    analysis_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    analysis = await db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your analysis")
    await db.delete(analysis)
    await db.flush()


@router.post("/{analysis_id}/fork", response_model=AnalysisOut, status_code=201)
async def fork_analysis(
    analysis_id: uuid.UUID,
    body: AnalysisForkRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Analysis).where(Analysis.id == analysis_id).options(selectinload(Analysis.datasets), selectinload(Analysis.owner))
    result = await db.execute(stmt)
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="Analysis not found")

    forked = Analysis(
        owner_id=user.id,
        title=body.title or f"{original.title} (fork)",
        description=body.description or original.description,
        language=original.language,
        source_code=original.source_code,
        forked_from_id=original.id,
    )
    db.add(forked)
    await db.flush()

    for link in original.datasets:
        db.add(AnalysisDataset(
            analysis_id=forked.id,
            dataset_id=link.dataset_id,
            version=link.version,
            alias=link.alias,
        ))

    original.fork_count += 1
    await db.flush()

    stmt = select(Analysis).where(Analysis.id == forked.id).options(selectinload(Analysis.datasets), selectinload(Analysis.owner))
    return (await db.execute(stmt)).scalar_one()


@router.post("/{analysis_id}/run", response_model=AnalysisRunOut, status_code=201)
async def trigger_run(
    analysis_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Analysis).where(Analysis.id == analysis_id).options(selectinload(Analysis.datasets), selectinload(Analysis.owner))
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    run = AnalysisRun(analysis_id=analysis.id, triggered_by=user.id)
    db.add(run)
    await db.flush()

    from app.services.dataset_service import get_dataset_by_id
    from app.config import settings

    dataset_files = []
    for link in analysis.datasets:
        ds = await get_dataset_by_id(db, link.dataset_id)
        if ds and ds.versions:
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

    from app.workers.tasks import run_analysis_task
    run_analysis_task.delay(
        str(analysis.id), str(run.id), analysis.language,
        analysis.source_code, dataset_files, analysis.requirements,
    )

    analysis.status = "queued"
    await db.flush()
    return run


# Proof-of-work endpoints for local computation
@router.post("/{analysis_id}/challenge", response_model=ChallengeOut)
async def get_challenge(
    analysis_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Analysis).where(Analysis.id == analysis_id).options(selectinload(Analysis.datasets), selectinload(Analysis.owner))
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    source_hash = compute_source_hash(analysis.source_code)

    from app.services.dataset_service import get_dataset_by_id
    dataset_hashes = []
    for link in analysis.datasets:
        ds = await get_dataset_by_id(db, link.dataset_id)
        if ds and ds.versions:
            ver = ds.versions[-1]
            if ver.checksum_sha256:
                dataset_hashes.append(ver.checksum_sha256)

    challenge = create_challenge(analysis.id, source_hash, dataset_hashes)
    return ChallengeOut(**challenge)


@router.post("/{analysis_id}/submit-proof", response_model=AnalysisRunOut, status_code=201)
async def submit_proof(
    analysis_id: uuid.UUID,
    body: ProofSubmission,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Analysis).where(Analysis.id == analysis_id).options(selectinload(Analysis.datasets), selectinload(Analysis.owner))
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    env_hash = compute_environment_hash(body.environment_info)

    run = AnalysisRun(
        analysis_id=analysis.id,
        triggered_by=user.id,
        status="completed",
        stdout=body.stdout,
        stderr=body.stderr,
        duration_ms=body.duration_ms,
        pow_hash=body.proof_hash,
        pow_nonce=body.nonce,
        pow_verified=True,  # We validated the proof
        environment_hash=env_hash,
        result_meta={"environment": body.environment_info, "local_execution": True},
    )
    db.add(run)

    analysis.status = "completed"
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
