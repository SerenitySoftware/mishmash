import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AnalysisDatasetIn(BaseModel):
    dataset_id: uuid.UUID
    version: int | None = None
    alias: str | None = None


class AnalysisCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    language: str = Field(pattern="^(python|r|sql)$")
    source_code: str = Field(min_length=1)
    datasets: list[AnalysisDatasetIn] = []


class AnalysisUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    source_code: str | None = None
    datasets: list[AnalysisDatasetIn] | None = None


class AnalysisRunOut(BaseModel):
    id: uuid.UUID
    analysis_id: uuid.UUID
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    stdout: str | None
    stderr: str | None
    result_key: str | None
    result_meta: dict | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisDatasetOut(BaseModel):
    dataset_id: uuid.UUID
    version: int | None
    alias: str | None

    model_config = {"from_attributes": True}


class AnalysisOut(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: str | None
    language: str
    source_code: str
    status: str
    datasets: list[AnalysisDatasetOut]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisListOut(BaseModel):
    items: list[AnalysisOut]
    total: int
    page: int
    page_size: int
