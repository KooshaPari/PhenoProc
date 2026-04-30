"""SQLAlchemy model definitions for generic entity storage."""

from __future__ import annotations

from datetime import datetime
from typing import Any

_sqlalchemy_base: dict[str, Any] | None = None


def _get_sqlalchemy_base() -> dict[str, Any]:
    """Lazy import and create SQLAlchemy Base."""
    global _sqlalchemy_base
    if _sqlalchemy_base is None:
        try:
            from sqlalchemy import Column, DateTime, Index, String, Text
            from sqlalchemy.orm import declarative_base

            Base = declarative_base()

            class GenericEntity(Base):
                """Generic SQLAlchemy model for storing arbitrary entities.

                This model uses JSON for flexible schema support.
                """

                __tablename__ = "generic_entities"

                id = Column(String(255), primary_key=True)
                entity_type = Column(String(100), nullable=False, index=True)
                data = Column(Text, nullable=False)
                created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
                updated_at = Column(
                    DateTime,
                    default=datetime.utcnow,
                    onupdate=datetime.utcnow,
                    nullable=False,
                )

                __table_args__ = (
                    Index("idx_entity_type_created", "entity_type", "created_at"),
                )

                def __repr__(self) -> str:
                    return f"<GenericEntity(id={self.id}, type={self.entity_type})>"

            _sqlalchemy_base = {"Base": Base, "GenericEntity": GenericEntity}
        except ImportError:
            raise ImportError(
                "SQLAlchemy is required for SQLAlchemyBackend. "
                "Install it with: pip install 'sqlalchemy>=2.0.0' 'aiosqlite>=0.19.0'",
            )

    return _sqlalchemy_base
