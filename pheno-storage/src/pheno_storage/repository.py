"""
Generic repository system with pluggable backends.

This module provides a flexible repository pattern implementation that supports
multiple storage backends (SQLAlchemy, MongoDB, Redis) for generic data persistence.

This is a facade module that re-exports from the repositories subpackage.
For the actual implementation, see the repositories package.
"""

from .repositories import (
    ConnectionError,
    create_repository,
    EntityNotFoundError,
    InMemoryBackend,
    MongoDBBackend,
    RedisBackend,
    RepositoryBackend,
    RepositoryError,
    SQLAlchemyBackend,
    TransactionError,
)

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
