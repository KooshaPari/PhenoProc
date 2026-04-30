"""Placeholder backends for MongoDB and Redis (not yet implemented)."""

from __future__ import annotations

from typing import Any

from .base import RepositoryBackend


class MongoDBBackend(RepositoryBackend):
    """MongoDB implementation of RepositoryBackend.

    TODO: Implement MongoDB support with Motor (async MongoDB driver).
    """

    def __init__(self, connection_string: str, database: str, collection: str):
        """Initialize MongoDB backend.

        Args:
            connection_string: MongoDB connection string
            database: Database name
            collection: Collection name
        """
        raise NotImplementedError("MongoDB backend not yet implemented")

    async def create(self, entity_id: str, data: dict[str, Any]) -> None:
        raise NotImplementedError("MongoDB backend not yet implemented")

    async def read(self, entity_id: str) -> dict[str, Any] | None:
        raise NotImplementedError("MongoDB backend not yet implemented")

    async def update(self, entity_id: str, data: dict[str, Any]) -> None:
        raise NotImplementedError("MongoDB backend not yet implemented")

    async def delete(self, entity_id: str) -> None:
        raise NotImplementedError("MongoDB backend not yet implemented")

    async def query(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError("MongoDB backend not yet implemented")

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        raise NotImplementedError("MongoDB backend not yet implemented")

    async def exists(self, entity_id: str) -> bool:
        raise NotImplementedError("MongoDB backend not yet implemented")

    async def close(self) -> None:
        raise NotImplementedError("MongoDB backend not yet implemented")


class RedisBackend(RepositoryBackend):
    """Redis implementation of RepositoryBackend.

    TODO: Implement Redis support with aioredis.
    """

    def __init__(self, redis_url: str, key_prefix: str = "repo"):
        """Initialize Redis backend.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for Redis keys
        """
        raise NotImplementedError("Redis backend not yet implemented")

    async def create(self, entity_id: str, data: dict[str, Any]) -> None:
        raise NotImplementedError("Redis backend not yet implemented")

    async def read(self, entity_id: str) -> dict[str, Any] | None:
        raise NotImplementedError("Redis backend not yet implemented")

    async def update(self, entity_id: str, data: dict[str, Any]) -> None:
        raise NotImplementedError("Redis backend not yet implemented")

    async def delete(self, entity_id: str) -> None:
        raise NotImplementedError("Redis backend not yet implemented")

    async def query(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError("Redis backend not yet implemented")

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        raise NotImplementedError("Redis backend not yet implemented")

    async def exists(self, entity_id: str) -> bool:
        raise NotImplementedError("Redis backend not yet implemented")

    async def close(self) -> None:
        raise NotImplementedError("Redis backend not yet implemented")
