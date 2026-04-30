"""Repository backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

T = TypeVar("T")


class RepositoryBackend(ABC, Generic[T]):
    """Abstract base class for repository backends.

    All storage backends (SQLAlchemy, MongoDB, Redis) must implement this interface.
    """

    @abstractmethod
    async def create(self, entity_id: str, data: dict[str, Any]) -> None:
        """Create a new entity.

        Args:
            entity_id: Unique identifier for the entity
            data: Entity data to store

        Raises:
            RepositoryError: If create operation fails
        """

    @abstractmethod
    async def read(self, entity_id: str) -> dict[str, Any] | None:
        """Read an entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity data if found, None otherwise

        Raises:
            RepositoryError: If read operation fails
        """

    @abstractmethod
    async def update(self, entity_id: str, data: dict[str, Any]) -> None:
        """Update an existing entity.

        Args:
            entity_id: Entity identifier
            data: Updated entity data

        Raises:
            EntityNotFoundError: If entity doesn't exist
            RepositoryError: If update operation fails
        """

    @abstractmethod
    async def delete(self, entity_id: str) -> None:
        """Delete an entity.

        Args:
            entity_id: Entity identifier

        Raises:
            EntityNotFoundError: If entity doesn't exist
            RepositoryError: If delete operation fails
        """

    @abstractmethod
    async def query(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query entities with filtering and pagination.

        Args:
            filters: Filter criteria (key-value pairs)
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            order_by: Field to order by (prefix with '-' for descending)

        Returns:
            List of matching entities

        Raises:
            RepositoryError: If query operation fails
        """

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count entities matching filters.

        Args:
            filters: Filter criteria (key-value pairs)

        Returns:
            Number of matching entities

        Raises:
            RepositoryError: If count operation fails
        """

    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """Check if entity exists.

        Args:
            entity_id: Entity identifier

        Returns:
            True if entity exists, False otherwise
        """

    @abstractmethod
    async def close(self) -> None:
        """Close backend connection and cleanup resources."""
