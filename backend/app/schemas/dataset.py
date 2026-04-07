import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    tags: list[str] = []
    format: str = Field(pattern="^(csv|json|parquet)$")
    license: str | None = None


class DatasetUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    tags: list[str] | None = None
    license: str | None = None


class DatasetVersionOut(BaseModel):
    id: uuid.UUID
    version: int
    file_size_bytes: int | None
    checksum_sha256: str | None
    row_count: int | None
    column_meta: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OwnerOut(BaseModel):
    id: uuid.UUID
    username: str
    name: str
    avatar_url: str | None

    model_config = {"from_attributes": True}


class DatasetOut(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    owner: OwnerOut | None = None
    name: str
    slug: str
    description: str | None
    tags: list[str]
    format: str
    current_version: int
    row_count: int | None
    column_meta: dict | None
    license: str | None
    is_public: bool
    star_count: int
    fork_count: int
    download_count: int
    forked_from_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetListOut(BaseModel):
    items: list[DatasetOut]
    total: int
    page: int
    page_size: int


class DatasetReferenceCreate(BaseModel):
    target_id: uuid.UUID
    relationship_type: str = "derived_from"
    description: str | None = None


class DatasetReferenceOut(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    target_id: uuid.UUID
    relationship_type: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PresignedUrlOut(BaseModel):
    upload_url: str
    storage_key: str
    expires_in: int


class UploadCompleteRequest(BaseModel):
    dataset_id: uuid.UUID
    storage_key: str
    file_size_bytes: int | None = None


class DatasetForkRequest(BaseModel):
    name: str | None = None
    description: str | None = None
