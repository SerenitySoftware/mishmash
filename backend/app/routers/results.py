"""Result file listing and download for analysis runs."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analysis import AnalysisRun
from app.services.storage import create_presigned_download_url
from app.config import settings

router = APIRouter(prefix="/api/analyses", tags=["results"])


class ResultFile(BaseModel):
    filename: str
    storage_key: str
    download_url: str
    content_type: str


MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".gif": "image/gif",
    ".csv": "text/csv",
    ".json": "application/json",
    ".txt": "text/plain",
    ".html": "text/html",
    ".pdf": "application/pdf",
    ".parquet": "application/octet-stream",
}


def detect_mime(filename: str) -> str:
    import os
    _, ext = os.path.splitext(filename.lower())
    return MIME_MAP.get(ext, "application/octet-stream")


@router.get("/{analysis_id}/runs/{run_id}/results", response_model=list[ResultFile])
async def list_result_files(
    analysis_id: uuid.UUID,
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List output files from an analysis run with presigned download URLs."""
    stmt = select(AnalysisRun).where(
        AnalysisRun.id == run_id, AnalysisRun.analysis_id == analysis_id
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if not run.result_key:
        return []

    # result_key is comma-separated S3 keys
    keys = [k.strip() for k in run.result_key.split(",") if k.strip()]
    files = []
    for key in keys:
        filename = key.split("/")[-1]
        download_url = create_presigned_download_url(settings.s3_results_bucket, key)
        files.append(ResultFile(
            filename=filename,
            storage_key=key,
            download_url=download_url,
            content_type=detect_mime(filename),
        ))

    return files
