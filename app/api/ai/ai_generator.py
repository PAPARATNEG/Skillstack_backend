import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.category import Category
from app.models.skill_group import SkillGroup
from app.models.skill import Skill
from app.models.skill_node import SkillNode
from app.models.skill_connection import SkillConnection
from app.schemas.ai_generator import (
    AIGenerateRequest, AIGenerateResponse, AIImportRequest
)
from app.services.ollama_service import call_ollama, build_prompt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI Generator"])

@router.post("/generate", response_model=AIGenerateResponse)
async def generate_skill_group(
    req: AIGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        prompt = build_prompt(req.query)
        raw_response = await call_ollama(prompt)
        raw_response = raw_response.strip()
        # Доп. очистка от маркеров
        if raw_response.startswith("```json"):
            raw_response = raw_response[7:]
        if raw_response.startswith("```"):
            raw_response = raw_response[3:]
        if raw_response.endswith("```"):
            raw_response = raw_response[:-3]
        raw_response = raw_response.strip()
        data = json.loads(raw_response)
        # Защита от отсутствующих полей
        if "skills" not in data:
            data["skills"] = []
        if "connections" not in data:
            data["connections"] = []
        if not isinstance(data["connections"], list):
            data["connections"] = []
        if not isinstance(data["skills"], list):
            data["skills"] = []
        validated = AIGenerateResponse(**data)
        return validated
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}, raw: {raw_response}")
        raise HTTPException(status_code=502, detail="Не удалось разобрать ответ нейросети")
    except Exception as e:
        logger.exception("Unexpected error in generate_skill_group")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.post("/import", status_code=201)
async def import_skill_group(
    req: AIImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Категория
    category = db.query(Category).filter(
        (Category.user_id == current_user.id) | (Category.is_system == True),
        Category.name == req.category
    ).first()
    if not category:
        category = Category(
            name=req.category,
            user_id=current_user.id,
            is_system=False
        )
        db.add(category)
        db.flush()

    # 2. Группа навыков
    skill_group = SkillGroup(
        name=req.category,
        description=f"Сгенерировано AI: {req.category}",
        category_id=category.id,
        user_id=current_user.id
    )
    db.add(skill_group)
    db.flush()

    # 3. Навыки и узлы
    created_skills = []
    for skill_item in req.skills:
        existing = db.query(Skill).filter(
            Skill.skill_group_id == skill_group.id,
            Skill.name == skill_item.name
        ).first()
        if existing:
            continue
        skill = Skill(
            name=skill_item.name,
            description=skill_item.description,
            level=skill_item.initial_level,
            user_id=current_user.id,
            skill_group_id=skill_group.id
        )
        db.add(skill)
        db.flush()
        node = SkillNode(skill_id=skill.id)
        db.add(node)
        created_skills.append(skill)

    # 4. Связи
    if req.connections:
        name_to_id = {s.name: s.id for s in created_skills}
        for conn_data in req.connections:
            from_id = name_to_id.get(conn_data.from_skill)
            to_id = name_to_id.get(conn_data.to_skill)
            if not from_id or not to_id:
                logger.warning(f"Connection skipped: unknown skill '{conn_data.from_skill}' or '{conn_data.to_skill}'")
                continue
            existing = db.query(SkillConnection).filter(
                SkillConnection.from_skill_id == from_id,
                SkillConnection.to_skill_id == to_id
            ).first()
            if existing:
                continue
            conn = SkillConnection(
                from_skill_id=from_id,
                to_skill_id=to_id,
                label=conn_data.label
            )
            db.add(conn)

    db.commit()
    return {
        "success": True,
        "skill_group_id": str(skill_group.id),
        "category_id": str(category.id),
        "skills_created": len(created_skills),
        "connections_created": len(req.connections) if req.connections else 0
    }