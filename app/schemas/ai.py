from pydantic import BaseModel, Field
from typing import List, Literal

class AIPathRequest(BaseModel):
    current_skill: str
    current_level: int = Field(..., ge=1, le=10)
    target_level: int = Field(..., ge=1, le=10)
    category: str
    language: str = "Russian"

class AIStep(BaseModel):
    level: int = Field(..., ge=1, le=10)
    description: str

class AIPathResponse(BaseModel):
    skill: str
    steps: List[AIStep]

class AIRecommendRequest(BaseModel):
    skill_ids: List[str] = []  # если пусто, рекомендует на основе всех навыков

class AIRecommendation(BaseModel):
    skill_name: str
    reason: str
    category: str