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
    requirements: str | None = None  # pip requirements.txt or R packages
    datasets: list[AnalysisDatasetIn] = []


class AnalysisUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    source_code: str | None = None
    requirements: str | None = None
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
    pow_hash: str | None
    pow_nonce: str | None
    pow_verified: bool | None
    environment_hash: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisDatasetOut(BaseModel):
    dataset_id: uuid.UUID
    version: int | None
    alias: str | None

    model_config = {"from_attributes": True}


class OwnerOut(BaseModel):
    id: uuid.UUID
    username: str
    name: str
    avatar_url: str | None

    model_config = {"from_attributes": True}


class AnalysisOut(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    owner: OwnerOut | None = None
    title: str
    description: str | None
    language: str
    source_code: str
    requirements: str | None
    status: str
    star_count: int
    fork_count: int
    forked_from_id: uuid.UUID | None
    datasets: list[AnalysisDatasetOut]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisListOut(BaseModel):
    items: list[AnalysisOut]
    total: int
    page: int
    page_size: int


class AnalysisForkRequest(BaseModel):
    title: str | None = None
    description: str | None = None


class ChallengeOut(BaseModel):
    analysis_id: str
    source_hash: str
    dataset_hashes: list[str]
    nonce_seed: str
    difficulty: int


class ProofSubmission(BaseModel):
    proof_hash: str
    nonce: str
    output_hash: str
    environment_info: dict
    stdout: str | None = None
    stderr: str | None = None
    duration_ms: int | None = None
    result_files: list[str] = []
