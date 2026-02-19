from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.skill import Skill
from app.schemas.ai import AIPathRequest, AIPathResponse, AIRecommendRequest, AIRecommendation
from app.api.deps import get_current_user
from app.core.ai_client import generate_path, recommend_skills  # заглушки
import logging

router = APIRouter(prefix="/api/ai", tags=["AI"])

@router.post("/generate-path", response_model=AIPathResponse)
async def generate_path_endpoint(
    request: AIPathRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Валидация: убедимся, что навык существует (опционально)
    # Можно вызвать LLM сервис
    try:
        response = await generate_path(request)
        return response
    except Exception as e:
        logging.error(f"AI generate-path failed: {e}")
        # Fallback: возвращаем заглушку с ручным созданием пути
        return {
            "skill": request.current_skill,
            "steps": [
                {"level": request.current_level+1, "description": "Продолжайте изучение (LLM недоступен)"},
                {"level": request.target_level, "description": "Достигните целевого уровня"}
            ]
        }

@router.post("/recommend-skills", response_model=list[AIRecommendation])
async def recommend_skills_endpoint(
    request: AIRecommendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Получаем список навыков пользователя (если переданы ID, иначе все)
    query = db.query(Skill).filter(Skill.user_id == current_user.id)
    if request.skill_ids:
        query = query.filter(Skill.id.in_(request.skill_ids))
    user_skills = query.all()
    
    # Вызываем AI или эвристики
    try:
        recommendations = await recommend_skills(user_skills)
        return recommendations
    except Exception as e:
        logging.error(f"AI recommend-skills failed: {e}")
        # Fallback: пустой список
        return []