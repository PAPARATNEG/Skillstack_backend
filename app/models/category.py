from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .base import UUIDMixin, TimestampMixin
import uuid


class Category(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="categories")
    skill_groups = relationship("SkillGroup", back_populates="category")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="unique_category_per_user"),
        CheckConstraint(
            "NOT (is_system = TRUE AND user_id IS NOT NULL)",
            name="system_category_no_user",
        ),
    )
