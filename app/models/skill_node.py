from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .base import UUIDMixin, TimestampMixin
import uuid


class SkillNode(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "skill_nodes"

    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=0.0)
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    skill = relationship("Skill", back_populates="node")
