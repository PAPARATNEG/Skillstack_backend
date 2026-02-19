from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import declarative_mixin, declared_attr
import uuid

@declarative_mixin
class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

@declarative_mixin
class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)