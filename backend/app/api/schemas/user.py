import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr

from backend.app.api.schemas.base import OrmBase


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    role: Literal["admin", "executive", "sales"]


class UserResponse(OrmBase):
    id: uuid.UUID
    email: str
    name: str
    role: str
    created_at: datetime
