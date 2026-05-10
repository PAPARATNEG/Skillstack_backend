from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class SkillGroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: UUID


class SkillGroupCreate(SkillGroupBase):
    pass


class SkillGroupUpdate(SkillGroupBase):
    pass


class SkillGroupOut(SkillGroupBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    progress: Optional[float] = None  # вычисляемое
    skills_count: Optional[int] = None
    average_level: Optional[float] = None
