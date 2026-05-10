from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.skill_group import SkillGroup
from app.models.skill import Skill
from app.models.user import User
from app.schemas.skill_group import SkillGroupCreate, SkillGroupUpdate, SkillGroupOut
from app.api.deps import get_current_user
from uuid import UUID
from typing import Optional

router = APIRouter(prefix="/api/skill-groups", tags=["Skill Groups"])


def calculate_group_stats(group: SkillGroup):
    skills = group.skills
    total = len(skills)
    if total == 0:
        return {"progress": 0, "average_level": 0, "skills_count": 0}
    total_level = sum(s.level for s in skills)
    avg = total_level / total
    progress = (total_level / (total * 10)) * 100
    return {
        "progress": round(progress, 1),
        "average_level": round(avg, 1),
        "skills_count": total,
    }


@router.get("/", response_model=list[SkillGroupOut])
def get_skill_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
):
    query = db.query(SkillGroup).filter(SkillGroup.user_id == current_user.id)
    if category_id:
        query = query.filter(SkillGroup.category_id == category_id)
    if search:
        query = query.filter(SkillGroup.name.ilike(f"%{search}%"))

    groups = query.options(joinedload(SkillGroup.skills)).all()
    result = []
    for g in groups:
        stats = calculate_group_stats(g)
        g_dict = g.__dict__
        g_dict.update(stats)
        result.append(SkillGroupOut.model_validate(g_dict))
    return result


@router.post("/", response_model=SkillGroupOut, status_code=201)
def create_skill_group(
    data: SkillGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверка существования группы с таким именем
    existing = (
        db.query(SkillGroup)
        .filter(SkillGroup.user_id == current_user.id, SkillGroup.name == data.name)
        .first()
    )
    if existing:
        raise HTTPException(400, "Skill group with this name already exists")

    # Проверка, что категория принадлежит пользователю или системная
    from app.models.category import Category

    cat = (
        db.query(Category)
        .filter(
            (Category.id == data.category_id)
            & ((Category.user_id == current_user.id) | (Category.is_system == True))
        )
        .first()
    )
    if not cat:
        raise HTTPException(400, "Invalid category")

    db_group = SkillGroup(**data.model_dump(), user_id=current_user.id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    # Загружаем skills для статистики
    db_group.skills = []
    stats = calculate_group_stats(db_group)
    return SkillGroupOut.model_validate({**db_group.__dict__, **stats})


@router.get("/{group_id}", response_model=SkillGroupOut)
def get_skill_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = (
        db.query(SkillGroup)
        .filter(SkillGroup.id == group_id, SkillGroup.user_id == current_user.id)
        .options(joinedload(SkillGroup.skills))
        .first()
    )
    if not group:
        raise HTTPException(404, "Skill group not found")
    stats = calculate_group_stats(group)
    return SkillGroupOut.model_validate({**group.__dict__, **stats})


@router.put("/{group_id}", response_model=SkillGroupOut)
def update_skill_group(
    group_id: UUID,
    data: SkillGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = (
        db.query(SkillGroup)
        .filter(SkillGroup.id == group_id, SkillGroup.user_id == current_user.id)
        .first()
    )
    if not group:
        raise HTTPException(404, "Skill group not found")

    # Если меняется категория, проверить её доступность
    if data.category_id and data.category_id != group.category_id:
        from app.models.category import Category

        cat = (
            db.query(Category)
            .filter(
                (Category.id == data.category_id)
                & ((Category.user_id == current_user.id) | (Category.is_system == True))
            )
            .first()
        )
        if not cat:
            raise HTTPException(400, "Invalid category")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(group, key, value)
    db.commit()
    db.refresh(group)
    # Загружаем skills
    group.skills = db.query(Skill).filter(Skill.skill_group_id == group.id).all()
    stats = calculate_group_stats(group)
    return SkillGroupOut.model_validate({**group.__dict__, **stats})


@router.delete("/{group_id}", status_code=204)
def delete_skill_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = (
        db.query(SkillGroup)
        .filter(SkillGroup.id == group_id, SkillGroup.user_id == current_user.id)
        .first()
    )
    if not group:
        raise HTTPException(404, "Skill group not found")

    db.delete(group)
    db.commit()
    return None


@router.get("/{group_id}/progress")
def get_group_progress(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = (
        db.query(SkillGroup)
        .filter(SkillGroup.id == group_id, SkillGroup.user_id == current_user.id)
        .options(joinedload(SkillGroup.skills))
        .first()
    )
    if not group:
        raise HTTPException(404, "Skill group not found")
    stats = calculate_group_stats(group)
    return stats
