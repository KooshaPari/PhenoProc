"""Repository factory for easy instantiation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .memory import InMemoryBackend
from .placeholder import MongoDBBackend, RedisBackend
from .sqlalchemy import SQLAlchemyBackend

if TYPE_CHECKING:
    from .base import RepositoryBackend


def create_repository(
    backend_type: str,
    entity_type: str = "default",
    **kwargs: Any,
) -> RepositoryBackend:
    """Create a repository with the specified backend.

    Args:
        backend_type: Backend type ('sqlalchemy', 'memory', 'mongodb', 'redis')
        entity_type: Type identifier for entities
        **kwargs: Backend-specific configuration

    Returns:
        Configured repository backend

    Example:
        # SQLite
        repo = create_repository(
            'sqlalchemy',
            entity_type='users',
            database_url='sqlite+aiosqlite:///users.db'
        )

        # PostgreSQL
        repo = create_repository(
            'sqlalchemy',
            entity_type='products',
            database_url='postgresql+asyncpg://user:pass@localhost/mydb',
            pool_size=10
        )

        # In-memory (testing)
        repo = create_repository('memory', entity_type='test')
    """
    if backend_type == "sqlalchemy":
        return SQLAlchemyBackend(entity_type=entity_type, **kwargs)
    if backend_type == "memory":
        return InMemoryBackend(entity_type=entity_type)
    if backend_type == "mongodb":
        return MongoDBBackend(**kwargs)
    if backend_type == "redis":
        return RedisBackend(**kwargs)
    raise ValueError(f"Unknown backend type: {backend_type}")
