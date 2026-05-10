from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Список email администраторов (можно добавить несколько)
ADMIN_EMAILS = ["paparatneg@example.com"]


def check_admin(current_user: User):
    """Проверяет, является ли пользователь администратором."""
    if current_user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Only admin can perform this action")


@router.get("/users", response_model=List[UserOut])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список всех пользователей (только для администраторов)."""
    check_admin(current_user)
    
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) | 
            (User.email.ilike(f"%{search}%"))
        )
    
    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserOut)
def get_user_by_id(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить информацию о конкретном пользователе (только для администраторов)."""
    check_admin(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user