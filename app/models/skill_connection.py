from sqlalchemy import String, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .base import UUIDMixin, TimestampMixin
import uuid

class SkillConnection(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "skill_connections"

    label: Mapped[str] = mapped_column(String(100), nullable=True)
    from_skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    to_skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)

    from_skill = relationship("Skill", foreign_keys=[from_skill_id], back_populates="outgoing_connections")
    to_skill = relationship("Skill", foreign_keys=[to_skill_id], back_populates="incoming_connections")

    __table_args__ = (
        CheckConstraint('from_skill_id != to_skill_id', name='different_skills'),
        UniqueConstraint('from_skill_id', 'to_skill_id', name='unique_directed_connection'),
    )