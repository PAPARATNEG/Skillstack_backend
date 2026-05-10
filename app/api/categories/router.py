from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.api.deps import get_current_user
from uuid import UUID

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("/", response_model=list[CategoryOut])
def get_categories(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Возвращаем системные + пользовательские
    return (
        db.query(Category)
        .filter((Category.user_id == current_user.id) | (Category.is_system == True))
        .all()
    )


@router.post("/", response_model=CategoryOut, status_code=201)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверка уникальности имени для пользователя
    existing = (
        db.query(Category)
        .filter(Category.user_id == current_user.id, Category.name == data.name)
        .first()
    )
    if existing:
        raise HTTPException(400, "Category with this name already exists")

    db_cat = Category(**data.model_dump(), user_id=current_user.id)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = (
        db.query(Category)
        .filter(
            (Category.id == category_id)
            & ((Category.user_id == current_user.id) | (Category.is_system == True))
        )
        .first()
    )
    if not cat:
        raise HTTPException(404, "Category not found")
    return cat


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = (
        db.query(Category)
        .filter(
            Category.id == category_id,
            Category.user_id == current_user.id,  # системные нельзя редактировать
        )
        .first()
    )
    if not cat:
        raise HTTPException(404, "Category not found or not editable")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(cat, key, value)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == current_user.id)
        .first()
    )
    if not cat:
        raise HTTPException(404, "Category not found or not deletable")

    # Проверка, что нет связанных групп (RESTRICT в БД, но лучше проверить здесь)
    if cat.skill_groups:
        raise HTTPException(400, "Cannot delete category with existing skill groups")

    db.delete(cat)
    db.commit()
    return None
