from sqlalchemy import Integer, Date, Boolean, ForeignKey, CheckConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .base import UUIDMixin, TimestampMixin
import uuid
import datetime

class Goal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "goals"

    target_level: Mapped[int] = mapped_column(Integer, nullable=False)
    deadline: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skill_groups.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="goals")
    skill_group = relationship("SkillGroup", back_populates="goals")

    __table_args__ = (
        CheckConstraint('target_level >= 1 AND target_level <= 10', name='goal_target_level_range'),
    )