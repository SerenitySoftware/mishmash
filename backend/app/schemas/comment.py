import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    target_type: str = Field(pattern="^(dataset|analysis|publication|comment)$")
    target_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    body: str = Field(min_length=1)


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1)


class AuthorOut(BaseModel):
    id: uuid.UUID
    username: str
    name: str
    avatar_url: str | None

    model_config = {"from_attributes": True}


class CommentOut(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    author: AuthorOut | None = None
    target_type: str
    target_id: uuid.UUID
    parent_id: uuid.UUID | None
    body: str
    created_at: datetime
    updated_at: datetime
    replies: list["CommentOut"] = []

    model_config = {"from_attributes": True}
