from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.skill import Skill
from app.models.skill_group import SkillGroup
from app.models.user import User
from app.schemas.skill import SkillCreate, SkillUpdate, SkillOut
from app.api.deps import get_current_user
from uuid import UUID
from typing import Optional

router = APIRouter(prefix="/api/skills", tags=["Skills"])

def get_skill_status(level: int) -> str:
    if level == 0:
        return "planned"
    elif 1 <= level <= 3:
        return "in_progress"
    elif 4 <= level <= 7:
        return "learned"
    else:
        return "expert"

def enrich_skill(skill: Skill):
    status = get_skill_status(skill.level)
    return {
        **skill.__dict__,
        "status": status,
        "position": pos
    }

@router.get("/", response_model=list[SkillOut])
def get_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    group_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None, regex="^(planned|in_progress|learned|expert)$"),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    query = db.query(Skill).filter(Skill.user_id == current_user.id)
    if group_id:
        query = query.filter(Skill.skill_group_id == group_id)
    if search:
        query = query.filter(Skill.name.ilike(f"%{search}%"))
    
    # Сначала получим все навыки, потом отфильтруем по статусу (вычисляемое поле)
    skills = query.offset(offset).limit(limit).all()
    result = []
    for s in skills:
        enriched = enrich_skill(s)
        if status and enriched["status"] != status:
            continue
        result.append(SkillOut.model_validate(enriched))
    return result

@router.get("/{skill_id}", response_model=SkillOut)
def get_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skill = db.query(Skill).filter(
        Skill.id == skill_id,
        Skill.user_id == current_user.id
    ).options(joinedload(Skill.node)).first()
    if not skill:
        raise HTTPException(404, "Skill not found")
    enriched = enrich_skill(skill)
    return SkillOut.model_validate(enriched)

@router.post("/skill-groups/{group_id}/skills/", response_model=SkillOut, status_code=201)
def create_skill(
    group_id: UUID,
    data: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Проверка группы
    group = db.query(SkillGroup).filter(
        SkillGroup.id == group_id,
        SkillGroup.user_id == current_user.id
    ).first()
    if not group:
        raise HTTPException(404, "Skill group not found")
    
    # Проверка уникальности имени в группе
    existing = db.query(Skill).filter(
        Skill.skill_group_id == group_id,
        Skill.name == data.name
    ).first()
    if existing:
        raise HTTPException(400, "Skill with this name already exists in the group")
    
    # Создаём навык (без создания SkillNode)
    skill = Skill(
        **data.model_dump(),
        user_id=current_user.id,
        skill_group_id=group_id
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    
    enriched = enrich_skill(skill)
    return SkillOut.model_validate(enriched)

@router.put("/{skill_id}", response_model=SkillOut)
def update_skill(
    skill_id: UUID,
    data: SkillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skill = db.query(Skill).filter(
        Skill.id == skill_id,
        Skill.user_id == current_user.id
    ).options(joinedload(Skill.node)).first()
    if not skill:
        raise HTTPException(404, "Skill not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(skill, key, value)
    db.commit()
    db.refresh(skill)
    enriched = enrich_skill(skill)
    return SkillOut.model_validate(enriched)

@router.patch("/{skill_id}/level", response_model=SkillOut)
def update_skill_level(
    skill_id: UUID,
    level: int = Query(..., ge=0, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skill = db.query(Skill).filter(
        Skill.id == skill_id,
        Skill.user_id == current_user.id
    ).options(joinedload(Skill.node)).first()
    if not skill:
        raise HTTPException(404, "Skill not found")
    skill.level = level
    db.commit()
    db.refresh(skill)
    enriched = enrich_skill(skill)
    return SkillOut.model_validate(enriched)

@router.delete("/{skill_id}", status_code=204)
def delete_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skill = db.query(Skill).filter(
        Skill.id == skill_id,
        Skill.user_id == current_user.id
    ).first()
    if not skill:
        raise HTTPException(404, "Skill not found")
    db.delete(skill)
    db.commit()
    return None