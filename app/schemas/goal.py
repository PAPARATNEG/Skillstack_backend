from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional


class GoalBase(BaseModel):
    skill_group_id: UUID
    target_level: int = Field(..., ge=1, le=10)
    deadline: date
    description: Optional[str] = Field(None, max_length=500)  


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    target_level: Optional[int] = Field(None, ge=1, le=10)
    deadline: Optional[date] = None
    description: Optional[str] = Field(None, max_length=500)  
    is_completed: Optional[bool] = None


class GoalOut(GoalBase):
    id: UUID
    user_id: UUID
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    current_level: Optional[float] = None
    progress_percentage: Optional[int] = None
