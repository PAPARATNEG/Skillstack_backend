from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class SkillConnectionBase(BaseModel):
    from_skill_id: UUID
    to_skill_id: UUID
    label: Optional[str] = None

class SkillConnectionCreate(SkillConnectionBase):
    pass

class SkillConnectionOut(SkillConnectionBase):
    id: UUID
    created_at: datetime
    from_skill_name: Optional[str] = None
    to_skill_name: Optional[str] = None