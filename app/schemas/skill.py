from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None
    level: int = Field(0, ge=0, le=10)

class SkillCreate(SkillBase):
    pass

class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    level: Optional[int] = Field(None, ge=0, le=10)

class SkillOut(SkillBase):
    id: UUID
    user_id: UUID
    skill_group_id: UUID
    created_at: datetime
    updated_at: datetime
    status: Literal["planned", "in_progress", "learned", "expert"]
    position: Optional[dict] = None  # {x: float, y: float}