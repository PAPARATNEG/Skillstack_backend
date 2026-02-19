from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, TokenResponse, UserOut
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token
)
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Проверка существования
    existing = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    if existing:
        raise HTTPException(400, "User with this email or username already exists")
    
    # Создание
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        password_hash=hash_password(user_in.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Ищем по email (form_data.username может быть email)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    
    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer"
    }

@router.post("/refresh")
def refresh(refresh_token: str, db: Session = Depends(get_db)):
    # Реализация проверки refresh токена (пока заглушка)
    # В реальности нужно хранить refresh токены в БД и проверять их валидность
    raise HTTPException(501, "Not implemented")

@router.post("/logout")
def logout():
    # Можно добавить черный список токенов, пока заглушка
    return {"message": "Logged out"}

@router.post("/reset-password")
def reset_password(email: str, db: Session = Depends(get_db)):
    # Отправка email с ссылкой сброса (пока заглушка)
    return {"message": f"Password reset link sent to {email}"}