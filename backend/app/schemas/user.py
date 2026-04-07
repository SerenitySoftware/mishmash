import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    username: str = Field(min_length=3, max_length=100, pattern="^[a-zA-Z0-9_-]+$")
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    name: str
    bio: str | None
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileOut(BaseModel):
    id: uuid.UUID
    username: str
    name: str
    bio: str | None
    avatar_url: str | None
    created_at: datetime
    dataset_count: int = 0
    analysis_count: int = 0
    publication_count: int = 0

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    bio: str | None = None
    avatar_url: str | None = None
