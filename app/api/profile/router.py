from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta
from collections import defaultdict

from app.database import get_db
from app.models.user import User
from app.models.skill import Skill
from app.models.goal import Goal
from app.schemas.user import UserOut, UserUpdate
from app.schemas.profile import ProfileStats, ProgressPoint, ActivityPoint
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.get("/", response_model=UserOut)
def get_profile(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Возвращает информацию о текущем пользователе"""
    return current_user


@router.put("/", response_model=UserOut)
def update_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновляет данные профиля (username, email, password)"""
    # Если передано имя пользователя, проверяем уникальность
    if user_update.username and user_update.username != current_user.username:
        existing = db.query(User).filter(User.username == user_update.username).first()
        if existing:
            raise HTTPException(400, "Username already taken")
        current_user.username = user_update.username

    if user_update.email and user_update.email != current_user.email:
        existing = db.query(User).filter(User.email == user_update.email).first()
        if existing:
            raise HTTPException(400, "Email already registered")
        current_user.email = user_update.email

    if user_update.password:
        from app.core.security import hash_password

        current_user.password_hash = hash_password(user_update.password)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/stats", response_model=ProfileStats)
def get_profile_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Возвращает статистику пользователя"""
    # Получаем все навыки пользователя
    skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
    total_skills = len(skills)
    in_progress = sum(1 for s in skills if 1 <= s.level <= 3)
    completed = sum(1 for s in skills if s.level >= 4)  # learned + expert

    # Цели
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).all()
    active_goals = sum(1 for g in goals if not g.is_completed)
    completed_goals = sum(1 for g in goals if g.is_completed)

    # Распределение по категориям (через группы навыков)
    from app.models.skill_group import SkillGroup
    from app.models.category import Category

    by_category = defaultdict(int)
    # Загружаем группы с категориями
    groups = db.query(SkillGroup).filter(SkillGroup.user_id == current_user.id).all()
    for group in groups:
        # Считаем навыки в группе
        cnt = db.query(Skill).filter(Skill.skill_group_id == group.id).count()
        if group.category:
            by_category[group.category.name] += cnt
        else:
            by_category["Без категории"] += cnt

    return {
        "total_skills": total_skills,
        "in_progress": in_progress,
        "completed": completed,
        "active_goals": active_goals,
        "completed_goals": completed_goals,
        "by_category": dict(by_category),
    }


@router.get("/progress", response_model=List[ProgressPoint])
def get_progress_chart(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает данные для графика прогресса за последние N дней.
    В реальном проекте нужно хранить историю изменений уровней навыков.
    Сейчас это заглушка, генерирующая случайные данные.
    """
    import random

    today = date.today()
    result = []
    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        result.append(
            {
                "date": d,
                "average_level": round(random.uniform(2, 7), 1),
                "skills_added": random.randint(0, 3),
            }
        )
    return result


@router.get("/activity", response_model=List[ActivityPoint])
def get_activity_heatmap(
    year: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает данные для тепловой карты активности (сколько действий в день).
    Пока заглушка.
    """
    import random
    from datetime import date, timedelta

    if year is None:
        year = date.today().year
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    delta = (end - start).days + 1
    result = []
    for i in range(delta):
        d = start + timedelta(days=i)
        result.append({"date": d, "count": random.randint(0, 10)})
    return result
