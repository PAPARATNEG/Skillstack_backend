from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.skill import Skill
from app.models.goal import Goal
from app.schemas.user import UserOut
from app.schemas.skill import SkillOut
from app.schemas.goal import GoalOut
from app.api.deps import get_current_user
from app.api.profile.router import get_profile_stats
from app.api.profile.router import get_progress_chart

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Собирает все данные для главной страницы"""
    # Статистика (переиспользуем из profile)
    stats = get_profile_stats(db, current_user)

    # Последние добавленные навыки (5 штук)
    recent_skills = db.query(Skill).filter(
        Skill.user_id == current_user.id
    ).order_by(Skill.created_at.desc()).limit(5).all()
    recent_skills_out = []
    for s in recent_skills:
        # Определяем статус
        if s.level == 0:
            status = "planned"
        elif 1 <= s.level <= 3:
            status = "in_progress"
        elif 4 <= s.level <= 7:
            status = "learned"
        else:
            status = "expert"
        recent_skills_out.append({
            "id": s.id,
            "name": s.name,
            "level": s.level,
            "status": status,
            "skill_group_id": s.skill_group_id,
            "created_at": s.created_at
        })

    # Активные цели (с прогрессом)
    from app.api.goals.router import calculate_goal_progress
    active_goals = db.query(Goal).filter(
        Goal.user_id == current_user.id,
        Goal.is_completed == False
    ).all()
    active_goals_out = []
    for g in active_goals:
        # Загружаем навыки группы (можно через relationship)
        skills = db.query(Skill).filter(Skill.skill_group_id == g.skill_group_id).all()
        progress = calculate_goal_progress(g, skills)  # функция из goals/router
        goal_dict = {
            "id": g.id,
            "skill_group_id": g.skill_group_id,
            "target_level": g.target_level,
            "deadline": g.deadline,
            "current_level": progress["current_level"],
            "progress_percentage": progress["progress_percentage"],
            "is_completed": g.is_completed,
            "created_at": g.created_at
        }
        active_goals_out.append(goal_dict)

    # График прогресса за последние 7 дней (для компактности)
    progress_chart = get_progress_chart(days=7, db=db, current_user=current_user)

    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        },
        "stats": stats,
        "recent_skills": recent_skills_out,
        "active_goals": active_goals_out,
        "progress_chart": progress_chart
    }