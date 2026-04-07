import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PublicationReferenceIn(BaseModel):
    ref_type: str = Field(pattern="^(dataset|analysis_run)$")
    ref_id: uuid.UUID


class PublicationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)
    references: list[PublicationReferenceIn] = []


class PublicationUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    body: str | None = None
    references: list[PublicationReferenceIn] | None = None


class PublicationReferenceOut(BaseModel):
    ref_type: str
    ref_id: uuid.UUID

    model_config = {"from_attributes": True}


class PublicationOut(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    title: str
    slug: str
    body: str
    references: list[PublicationReferenceOut]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PublicationListOut(BaseModel):
    items: list[PublicationOut]
    total: int
    page: int
    page_size: int
