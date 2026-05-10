from pydantic import BaseModel, Field
from typing import List, Optional


class AIGenerateRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)


class AISkillItem(BaseModel):
    name: str
    initial_level: int = Field(..., ge=1, le=3)
    target_level: Optional[int] = Field(None, ge=1, le=8)  # теперь необязательное
    description: Optional[str] = None


class AIConnection(BaseModel):
    from_skill: str
    to_skill: str
    label: Optional[str] = Field(None, max_length=300)


class AIGenerateResponse(BaseModel):
    category: str
    skills: List[AISkillItem] = []
    connections: List[AIConnection] = []


class AIImportRequest(BaseModel):
    category: str
    skills: List[AISkillItem] = []
    connections: List[AIConnection] = []
