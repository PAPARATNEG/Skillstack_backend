from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .base import UUIDMixin, TimestampMixin
import uuid
import datetime

class GitHubIntegration(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "github_integrations"

    github_username: Mapped[str] = mapped_column(String(100), nullable=False)
    last_sync: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    user = relationship("User", back_populates="github_integration")