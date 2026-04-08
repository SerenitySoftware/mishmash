"""Citation generation for datasets."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.dataset_service import get_dataset_by_id

router = APIRouter(prefix="/api/datasets", tags=["citation"])


@router.get("/{dataset_id}/cite")
async def cite_dataset(
    dataset_id: uuid.UUID,
    version: int | None = None,
    format: str = Query("bibtex", pattern="^(bibtex|apa|ris|plain)$"),
    db: AsyncSession = Depends(get_db),
):
    """Generate a citation for a dataset in various formats."""
    dataset = await get_dataset_by_id(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    owner_name = dataset.owner.name if dataset.owner else "Unknown"
    owner_username = dataset.owner.username if dataset.owner else "unknown"

    # Use specific version or latest
    if version and dataset.versions:
        ver = next((v for v in dataset.versions if v.version == version), None)
    elif dataset.versions:
        ver = dataset.versions[-1]
    else:
        ver = None

    ver_num = ver.version if ver else dataset.current_version
    ver_date = ver.created_at if ver else dataset.created_at
    if isinstance(ver_date, str):
        ver_date = datetime.fromisoformat(ver_date)
    year = ver_date.year

    checksum = ver.checksum_sha256[:12] if ver and ver.checksum_sha256 else "n/a"
    identifier = f"mishmash:{owner_username}/{dataset.slug}@v{ver_num}"

    if format == "bibtex":
        citation = (
            f"@misc{{{dataset.slug}_v{ver_num},\n"
            f"  author = {{{owner_name}}},\n"
            f"  title = {{{{{dataset.name}}}}},\n"
            f"  year = {{{year}}},\n"
            f"  publisher = {{Mishmash}},\n"
            f"  version = {{{ver_num}}},\n"
            f"  identifier = {{{identifier}}},\n"
            f"  checksum = {{{checksum}}},\n"
            f"}}"
        )
    elif format == "apa":
        citation = (
            f"{owner_name} ({year}). {dataset.name} (Version {ver_num}) [Dataset]. "
            f"Mishmash. {identifier}"
        )
    elif format == "ris":
        citation = (
            f"TY  - DATA\n"
            f"AU  - {owner_name}\n"
            f"TI  - {dataset.name}\n"
            f"PY  - {year}\n"
            f"PB  - Mishmash\n"
            f"ET  - {ver_num}\n"
            f"DO  - {identifier}\n"
            f"ER  - "
        )
    else:  # plain
        citation = (
            f"{owner_name}. \"{dataset.name}\" (Version {ver_num}). "
            f"Mishmash, {year}. {identifier}. Checksum: {checksum}."
        )

    return {
        "citation": citation,
        "format": format,
        "identifier": identifier,
        "version": ver_num,
        "checksum": checksum,
    }
