from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.skill import Skill
from app.models.skill_connection import SkillConnection
from app.models.user import User
from app.schemas.skill import SkillOut
from app.schemas.skill_connection import SkillConnectionCreate, SkillConnectionOut
from app.api.deps import get_current_user
from app.api.skills.router import enrich_skill  
from uuid import UUID

router = APIRouter(prefix="/api/skills-map", tags=["Skills Map"])


@router.get("/")
def get_skills_map(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Все навыки пользователя
    skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
    nodes = [enrich_skill(s) for s in skills]

    # Все связи (только те, где навыки принадлежат пользователю)
    connections = (
        db.query(SkillConnection)
        .join(Skill, SkillConnection.from_skill_id == Skill.id)
        .filter(Skill.user_id == current_user.id)
        .all()
    )
    edges = []
    for conn in connections:
        edges.append(
            {
                "id": str(conn.id),
                "from_skill_id": str(conn.from_skill_id),
                "to_skill_id": str(conn.to_skill_id),
                "label": conn.label,
                "created_at": conn.created_at.isoformat(),
            }
        )
    return {"nodes": nodes, "edges": edges}


@router.post("/connections", response_model=SkillConnectionOut, status_code=201)
def create_connection(
    data: SkillConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверяем, что оба навыка принадлежат пользователю
    skills = (
        db.query(Skill)
        .filter(
            Skill.id.in_([data.from_skill_id, data.to_skill_id]),
            Skill.user_id == current_user.id,
        )
        .all()
    )
    if len(skills) != 2:
        raise HTTPException(400, "One or both skills not found or not owned by user")

    # Проверяем уникальность связи (только в одном направлении)
    existing = (
        db.query(SkillConnection)
        .filter(
            SkillConnection.from_skill_id == data.from_skill_id,
            SkillConnection.to_skill_id == data.to_skill_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Connection already exists")

    conn = SkillConnection(**data.model_dump())
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


@router.delete("/connections/{connection_id}", status_code=204)
def delete_connection(
    connection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = (
        db.query(SkillConnection)
        .join(Skill, SkillConnection.from_skill_id == Skill.id)
        .filter(SkillConnection.id == connection_id, Skill.user_id == current_user.id)
        .first()
    )
    if not conn:
        raise HTTPException(404, "Connection not found")
    db.delete(conn)
    db.commit()
    return None


@router.get("/connections/from/{skill_id}")
def get_outgoing_connections(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверка принадлежности навыка
    skill = (
        db.query(Skill)
        .filter(Skill.id == skill_id, Skill.user_id == current_user.id)
        .first()
    )
    if not skill:
        raise HTTPException(404, "Skill not found")
    connections = (
        db.query(SkillConnection)
        .filter(SkillConnection.from_skill_id == skill_id)
        .all()
    )
    return connections


@router.get("/connections/to/{skill_id}")
def get_incoming_connections(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = (
        db.query(Skill)
        .filter(Skill.id == skill_id, Skill.user_id == current_user.id)
        .first()
    )
    if not skill:
        raise HTTPException(404, "Skill not found")
    connections = (
        db.query(SkillConnection).filter(SkillConnection.to_skill_id == skill_id).all()
    )
    return connections