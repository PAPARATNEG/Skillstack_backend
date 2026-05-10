import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.github_integration import GitHubIntegration
from app.schemas.github import (
    GitHubAuthUrl,
    GitHubRepository,
    GitHubSuggestedSkill,
    GitHubSyncResponse,
    GitHubStatus,
)
from app.api.deps import get_current_user
from app.core.config import settings
import httpx
from typing import List

router = APIRouter(prefix="/api/github", tags=["GitHub"])


@router.get("/auth-url", response_model=GitHubAuthUrl)
def get_github_auth_url():
    # Формируем URL для OAuth
    url = f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&scope=repo"
    return {"url": url}


@router.post("/callback")
async def github_callback(
    code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Обмениваем код на токен
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(400, "Failed to get access token")

    # Получаем информацию о пользователе GitHub
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"},
        )
        github_user = user_resp.json()
        github_username = github_user["login"]

    # Сохраняем в БД (токен не храним, только username)
    integration = (
        db.query(GitHubIntegration)
        .filter(GitHubIntegration.user_id == current_user.id)
        .first()
    )
    if integration:
        integration.github_username = github_username
        integration.last_sync = None
    else:
        integration = GitHubIntegration(
            user_id=current_user.id, github_username=github_username
        )
        db.add(integration)
    db.commit()

    # Можно сохранить токен в сессии (например, в request.session) для последующих запросов
    request.session["github_token"] = access_token

    return {"message": "GitHub integration successful"}


@router.get("/repositories", response_model=List[GitHubRepository])
async def get_github_repositories(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверяем наличие токена в сессии
    token = request.session.get("github_token")
    if not token:
        # Пробуем получить токен заново? Или требуем пройти OAuth сначала
        raise HTTPException(401, "GitHub not authenticated")

    async with httpx.AsyncClient() as client:
        repos_resp = await client.get(
            "https://api.github.com/user/repos",
            headers={"Authorization": f"token {token}"},
            params={"per_page": 100, "sort": "updated"},
        )
        repos = repos_resp.json()

    result = []
    for repo in repos:
        # Для каждого репозитория получаем языки
        lang_resp = await client.get(
            repo["languages_url"], headers={"Authorization": f"token {token}"}
        )
        languages = lang_resp.json()

        # Попытка получить зависимости (упрощённо)
        deps = {}
        # Можно попытаться найти package.json, requirements.txt и т.д.
        # Для простоты пока оставим пустым

        result.append(
            {
                "name": repo["name"],
                "full_name": repo["full_name"],
                "html_url": repo["html_url"],
                "languages": languages,
                "dependencies": deps,
            }
        )
    return result


@router.post("/sync", response_model=GitHubSyncResponse)
async def sync_github(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Получаем репозитории (как выше)
    repos = await get_github_repositories(request, db, current_user)
    # Анализируем и формируем предложения
    suggested = []
    for repo in repos:
        for lang, bytes_count in repo["languages"].items():
            # Простейшая эвристика: язык -> категория
            category = map_language_to_category(lang)
            suggested.append(
                {
                    "name": lang,
                    "category": category,
                    "source_repo": repo["full_name"],
                    "confidence": 0.8,  # фиксированная
                }
            )
        # Здесь можно анализировать зависимости, но для MVP достаточно языков

    # Обновляем время последней синхронизации
    integration = (
        db.query(GitHubIntegration)
        .filter(GitHubIntegration.user_id == current_user.id)
        .first()
    )
    if integration:
        integration.last_sync = datetime.utcnow()
        db.commit()

    # Убираем дубликаты (по имени навыка)
    unique = {s["name"]: s for s in suggested}.values()
    return {"suggested_skills": list(unique)}


@router.get("/status", response_model=GitHubStatus)
def get_github_status(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    integration = (
        db.query(GitHubIntegration)
        .filter(GitHubIntegration.user_id == current_user.id)
        .first()
    )
    if integration:
        return {
            "is_connected": True,
            "github_username": integration.github_username,
            "last_sync": integration.last_sync,
        }
    return {"is_connected": False, "github_username": None, "last_sync": None}


def map_language_to_category(lang: str) -> str:
    # Простейшее отображение
    frontend = ["JavaScript", "TypeScript", "HTML", "CSS", "React", "Vue", "Angular"]
    backend = ["Python", "Java", "Go", "Ruby", "PHP", "C#", "Node"]
    if lang in frontend:
        return "Frontend"
    elif lang in backend:
        return "Backend"
    else:
        return "Other"
