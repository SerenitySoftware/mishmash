import json
import uuid
from datetime import datetime, timezone

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.analysis import AnalysisRun
from app.services.runner import run_analysis_in_container
from app.workers.celery_app import celery_app

# Sync engine for celery workers (celery is sync)
# Convert async URL to sync: postgresql+asyncpg://... -> postgresql+psycopg2://...
sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(sync_url)
SyncSession = sessionmaker(sync_engine)

# Redis for SSE pub/sub
redis_client = redis.from_url(settings.redis_url)


def publish_run_status(run_id: str, status: str, **extra):
    """Publish run status change to Redis for SSE consumers."""
    data = {"run_id": run_id, "status": status, **extra}
    redis_client.publish(f"run:{run_id}", json.dumps(data))


@celery_app.task(name="run_analysis")
def run_analysis_task(
    analysis_id: str,
    run_id: str,
    language: str,
    source_code: str,
    dataset_files: list[dict],
    requirements: str | None = None,
) -> dict:
    """Execute an analysis and update the run record."""
    with SyncSession() as db:
        run = db.get(AnalysisRun, uuid.UUID(run_id))
        if not run:
            return {"error": "Run not found"}

        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        db.commit()
        publish_run_status(run_id, "running")

        result = run_analysis_in_container(
            analysis_id=uuid.UUID(analysis_id),
            run_id=uuid.UUID(run_id),
            language=language,
            source_code=source_code,
            dataset_files=dataset_files,
            requirements=requirements,
        )

        run.status = result["status"]
        run.finished_at = datetime.now(timezone.utc)
        run.duration_ms = result["duration_ms"]
        run.stdout = result["stdout"]
        run.stderr = result["stderr"]
        run.result_key = ",".join(result["result_files"]) if result["result_files"] else None
        if result["status"] == "failed":
            run.error_message = result["stderr"][:1000]
        db.commit()

        publish_run_status(run_id, result["status"], duration_ms=result["duration_ms"])

        return {"status": result["status"], "run_id": run_id}


@celery_app.task(name="process_upload")
def process_upload_task(
    dataset_id: str,
    version_id: str,
    storage_key: str,
    format: str,
) -> dict:
    """Process an uploaded dataset: extract metadata, row count, column info, quality profile."""
    import hashlib
    import tempfile
    import os
    import pandas as pd
    from app.services.storage import download_file
    from app.services.validation import validate_dataset

    with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        download_file(settings.s3_datasets_bucket, storage_key, tmp_path)

        if format == "csv":
            df = pd.read_csv(tmp_path)
        elif format == "json":
            df = pd.read_json(tmp_path, lines=True)
        elif format == "parquet":
            df = pd.read_parquet(tmp_path)
        else:
            return {"error": f"Unsupported format: {format}"}

        row_count = len(df)
        column_meta = []
        for col in df.columns:
            col_info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "nullable": bool(df[col].isnull().any()),
                "unique_count": int(df[col].nunique()),
            }
            if df[col].dtype in ("int64", "float64"):
                col_info["min"] = float(df[col].min()) if not pd.isna(df[col].min()) else None
                col_info["max"] = float(df[col].max()) if not pd.isna(df[col].max()) else None
                col_info["mean"] = float(df[col].mean()) if not pd.isna(df[col].mean()) else None
            column_meta.append(col_info)

        file_size = os.path.getsize(tmp_path)

        # Compute checksum
        sha256 = hashlib.sha256()
        with open(tmp_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        checksum = sha256.hexdigest()

        # Compute quality profile
        with open(tmp_path, "rb") as f:
            quality_profile = validate_dataset(f.read(), format)

        with SyncSession() as db:
            from app.models.dataset import Dataset, DatasetVersion
            version = db.get(DatasetVersion, uuid.UUID(version_id))
            if version:
                version.row_count = row_count
                version.column_meta = column_meta
                version.file_size_bytes = file_size
                version.checksum_sha256 = checksum
                version.quality_profile = quality_profile

            dataset = db.get(Dataset, uuid.UUID(dataset_id))
            if dataset:
                dataset.row_count = row_count
                dataset.column_meta = column_meta

            db.commit()

        return {
            "status": "completed",
            "row_count": row_count,
            "columns": len(column_meta),
            "quality_score": quality_profile.get("quality_score", None),
        }

    finally:
        os.unlink(tmp_path)
