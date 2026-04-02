from sqlalchemy import String, Text, Integer, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .base import UUIDMixin, TimestampMixin
import uuid

class Skill(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skill_groups.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="skills")
    skill_group = relationship("SkillGroup", back_populates="skills")
    outgoing_connections = relationship("SkillConnection", foreign_keys="SkillConnection.from_skill_id", back_populates="from_skill", cascade="all, delete-orphan")
    incoming_connections = relationship("SkillConnection", foreign_keys="SkillConnection.to_skill_id", back_populates="to_skill", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('level >= 0 AND level <= 10', name='skill_level_range'),
        UniqueConstraint('skill_group_id', 'name', name='unique_skill_per_group'),
    )