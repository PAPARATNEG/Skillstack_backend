from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.fake_db import fake_users_db
from app.schemas.user import UserCreate, TokenResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)

# =========================
# Регистрация
# =========================
@router.post("/register")
def register(user: UserCreate):
    """
    Здесь должна быть проверка пользователя в БД
    """

    for u in fake_users_db:
        if u["email"] == user.email:
            raise HTTPException(400, "User already exists")

    fake_user = {
        "id": len(fake_users_db) + 1,  # ID должен генерировать БД
        "email": user.email,
        "password_hash": hash_password(user.password)
    }

    fake_users_db.append(fake_user)

    return {"message": "User registered successfully"}


# =========================
# Логин
# =========================
@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends()):
    """
    Здесь должна быть выборка пользователя из БД
    """

    user = next(
        (u for u in fake_users_db if u["email"] == form.username),
        None
    )

    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    return {
        "access_token": create_access_token(user["id"]),
        "refresh_token": create_refresh_token(user["id"]),
        "token_type": "bearer"
    }


# =========================
# Обновление токена
# =========================
@router.post("/refresh")
def refresh(refresh_token: str):
    """
    Здесь должна быть проверка refresh-токена в БД
    """
    # Пока просто заглушка
    return {"message": "Token refreshed (mock)"}


# =========================
# Выход
# =========================
@router.post("/logout")
def logout():

    return {"message": "Logged out"}


# =========================
# Сброс пароля
# =========================
@router.post("/reset-password")
def reset_password(email: str):
    """
    Здесь должна быть отправка email и работа с БД
    """
    return {"message": f"Password reset link sent to {email} (mock)"}