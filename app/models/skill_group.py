from sqlalchemy import String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .base import UUIDMixin, TimestampMixin
import uuid

class SkillGroup(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "skill_groups"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="skill_groups")
    category = relationship("Category", back_populates="skill_groups")
    skills = relationship("Skill", back_populates="skill_group", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="skill_group", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='unique_skill_group_per_user'),
    )