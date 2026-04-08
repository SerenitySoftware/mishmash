import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.dataset_service import get_dataset_by_id
from app.services.storage import download_file
from app.services.validation import validate_dataset
from app.config import settings

router = APIRouter(prefix="/api/datasets", tags=["validation"])


@router.get("/{dataset_id}/validate")
async def validate(dataset_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Run data quality validation on the latest version of a dataset."""
    dataset = await get_dataset_by_id(db, dataset_id)
    if not dataset or not dataset.versions:
        raise HTTPException(status_code=404, detail="Dataset not found or no versions")

    latest = dataset.versions[-1]

    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=f".{dataset.format}", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        download_file(settings.s3_datasets_bucket, latest.storage_key, tmp_path)
        with open(tmp_path, "rb") as f:
            data = f.read()
        report = validate_dataset(data, dataset.format)
        return report
    finally:
        os.unlink(tmp_path)


@router.get("/{dataset_id}/stats")
async def dataset_stats(dataset_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get statistical summary for a dataset."""
    dataset = await get_dataset_by_id(db, dataset_id)
    if not dataset or not dataset.versions:
        raise HTTPException(status_code=404, detail="Dataset not found or no versions")

    latest = dataset.versions[-1]

    import tempfile
    import os
    import pandas as pd
    import json

    with tempfile.NamedTemporaryFile(suffix=f".{dataset.format}", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        download_file(settings.s3_datasets_bucket, latest.storage_key, tmp_path)

        if dataset.format == "csv":
            df = pd.read_csv(tmp_path)
        elif dataset.format == "json":
            df = pd.read_json(tmp_path, lines=True)
        elif dataset.format == "parquet":
            df = pd.read_parquet(tmp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")

        stats = {
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "memory_usage_bytes": int(df.memory_usage(deep=True).sum()),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "null_counts": {col: int(df[col].isnull().sum()) for col in df.columns},
            "numeric_summary": {},
            "categorical_summary": {},
            "correlations": None,
        }

        # Numeric summary
        numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
        for col in numeric_cols:
            desc = df[col].describe()
            stats["numeric_summary"][col] = {
                k: float(v) if not pd.isna(v) else None
                for k, v in desc.items()
            }

        # Categorical summary (top values)
        cat_cols = df.select_dtypes(include=["object"]).columns
        for col in cat_cols:
            top = df[col].value_counts().head(10)
            stats["categorical_summary"][col] = {
                "top_values": {str(k): int(v) for k, v in top.items()},
                "unique_count": int(df[col].nunique()),
            }

        # Correlation matrix for numeric columns
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr()
            stats["correlations"] = {
                "columns": list(corr.columns),
                "values": [[float(v) if not pd.isna(v) else None for v in row] for row in corr.values],
            }

        return stats
    finally:
        os.unlink(tmp_path)
