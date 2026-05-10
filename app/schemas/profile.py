from pydantic import BaseModel
from datetime import date
from typing import Dict, List


class ProfileStats(BaseModel):
    total_skills: int
    in_progress: int
    completed: int
    active_goals: int
    completed_goals: int
    by_category: Dict[str, int]


class ProgressPoint(BaseModel):
    date: date
    average_level: float
    skills_added: int


class ActivityPoint(BaseModel):
    date: date
    count: int
