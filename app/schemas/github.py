from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class GitHubAuthUrl(BaseModel):
    url: str

class GitHubRepository(BaseModel):
    name: str
    full_name: str
    html_url: str
    languages: dict[str, int]  # язык: байт кода
    dependencies: Optional[dict] = None  # из package.json, requirements.txt и т.п.

class GitHubSuggestedSkill(BaseModel):
    name: str
    category: str  # предполагаемая категория
    source_repo: str
    confidence: float  # 0-1

class GitHubSyncResponse(BaseModel):
    suggested_skills: List[GitHubSuggestedSkill]

class GitHubStatus(BaseModel):
    is_connected: bool
    github_username: Optional[str]
    last_sync: Optional[datetime]