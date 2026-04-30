"""Repository backends package.

Provides pluggable storage backends for the repository pattern.
"""

from .base import RepositoryBackend
from .exceptions import (
    ConnectionError,
    EntityNotFoundError,
    RepositoryError,
    TransactionError,
)
from .factory import create_repository
from .memory import InMemoryBackend
from .placeholder import MongoDBBackend, RedisBackend
from .sqlalchemy import SQLAlchemyBackend

__all__ = [
    "ConnectionError",
    "EntityNotFoundError",
    "InMemoryBackend",
    "MongoDBBackend",
    "RedisBackend",
    "RepositoryBackend",
    "RepositoryError",
    "SQLAlchemyBackend",
    "TransactionError",
    "create_repository",
]
