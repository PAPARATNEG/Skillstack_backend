from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.goal import Goal
from app.models.skill_group import SkillGroup
from app.models.skill import Skill
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalUpdate, GoalOut
from app.api.deps import get_current_user
from uuid import UUID
from datetime import date
from typing import Optional

router = APIRouter(prefix="/api/goals", tags=["Goals"])

def calculate_goal_progress(goal: Goal):
    skills = goal.skill_group.skills
    if not skills:
        return {"current_level": 0, "progress_percentage": 0}
    avg_level = sum(s.level for s in skills) / len(skills)
    progress = (avg_level / goal.target_level) * 100
    progress = min(100, max(0, progress))
    return {
        "current_level": round(avg_level, 1),
        "progress_percentage": round(progress)
    }

@router.get("/", response_model=list[GoalOut])
def get_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    completed: Optional[bool] = Query(None),
    group_id: Optional[UUID] = Query(None)
):
    query = db.query(Goal).filter(Goal.user_id == current_user.id)
    if completed is not None:
        query = query.filter(Goal.is_completed == completed)
    if group_id:
        query = query.filter(Goal.skill_group_id == group_id)
    
    goals = query.options(joinedload(Goal.skill_group).joinedload(SkillGroup.skills)).all()
    result = []
    for g in goals:
        progress = calculate_goal_progress(g)
        g_dict = g.__dict__
        g_dict.update(progress)
        result.append(GoalOut.model_validate(g_dict))
    return result

@router.post("/", response_model=GoalOut, status_code=201)
def create_goal(
    data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Проверка группы
    group = db.query(SkillGroup).filter(
        SkillGroup.id == data.skill_group_id,
        SkillGroup.user_id == current_user.id
    ).first()
    if not group:
        raise HTTPException(404, "Skill group not found")
    
    # Проверка на активную цель
    active = db.query(Goal).filter(
        Goal.skill_group_id == data.skill_group_id,
        Goal.is_completed == False
    ).first()
    if active:
        raise HTTPException(400, "This skill group already has an active goal")
    
    goal = Goal(
        **data.model_dump(),
        user_id=current_user.id
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    # Подгружаем группу с навыками для прогресса
    goal.skill_group = group
    group.skills = db.query(Skill).filter(Skill.skill_group_id == group.id).all()
    progress = calculate_goal_progress(goal)
    return GoalOut.model_validate({**goal.__dict__, **progress})

@router.get("/{goal_id}", response_model=GoalOut)
def get_goal(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).options(joinedload(Goal.skill_group).joinedload(SkillGroup.skills)).first()
    if not goal:
        raise HTTPException(404, "Goal not found")
    progress = calculate_goal_progress(goal)
    return GoalOut.model_validate({**goal.__dict__, **progress})

@router.put("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: UUID,
    data: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).options(joinedload(Goal.skill_group)).first()
    if not goal:
        raise HTTPException(404, "Goal not found")
    
    # Если пытаемся сделать цель активной, но уже есть другая активная
    if data.is_completed == False and goal.is_completed:
        # Проверяем, нет ли другой активной цели для этой группы
        active = db.query(Goal).filter(
            Goal.skill_group_id == goal.skill_group_id,
            Goal.is_completed == False,
            Goal.id != goal_id
        ).first()
        if active:
            raise HTTPException(400, "Another active goal exists for this group")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(goal, key, value)
    db.commit()
    db.refresh(goal)
    # Подгружаем навыки для прогресса
    goal.skill_group.skills = db.query(Skill).filter(Skill.skill_group_id == goal.skill_group_id).all()
    progress = calculate_goal_progress(goal)
    return GoalOut.model_validate({**goal.__dict__, **progress})

@router.delete("/{goal_id}", status_code=204)
def delete_goal(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(404, "Goal not found")
    db.delete(goal)
    db.commit()
    return None

@router.patch("/{goal_id}/complete", response_model=GoalOut)
def complete_goal(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).options(joinedload(Goal.skill_group)).first()
    if not goal:
        raise HTTPException(404, "Goal not found")
    if goal.is_completed:
        raise HTTPException(400, "Goal already completed")
    
    goal.is_completed = True
    goal.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(goal)
    goal.skill_group.skills = db.query(Skill).filter(Skill.skill_group_id == goal.skill_group_id).all()
    progress = calculate_goal_progress(goal)
    return GoalOut.model_validate({**goal.__dict__, **progress})