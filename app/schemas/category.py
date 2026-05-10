from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    id: UUID
    is_system: bool
    user_id: UUID | None
    created_at: datetime
    updated_at: datetime
