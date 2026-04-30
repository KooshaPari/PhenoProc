"""In-memory repository backend for testing and development."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone, UTC
from typing import Any

from .base import RepositoryBackend
from .exceptions import EntityNotFoundError


class InMemoryBackend(RepositoryBackend):
    """In-memory implementation of RepositoryBackend.

    Useful for testing and development. Does not persist data between restarts.
    """

    def __init__(self, entity_type: str = "default"):
        """Initialize in-memory backend.

        Args:
            entity_type: Type identifier for entities in this repository
        """
        self.entity_type = entity_type
        self._storage: dict[str, dict[str, Any]] = {}
        self._in_transaction = False
        self._transaction_storage: dict[str, dict[str, Any]] | None = None

    async def create(self, entity_id: str, data: dict[str, Any]) -> None:
        """Create a new entity."""
        storage = self._transaction_storage if self._in_transaction else self._storage
        storage[entity_id] = {
            **data,
            "_created_at": datetime.now(UTC).isoformat(),
            "_updated_at": datetime.now(UTC).isoformat(),
        }

    async def read(self, entity_id: str) -> dict[str, Any] | None:
        """Read an entity by ID."""
        storage = self._transaction_storage if self._in_transaction else self._storage
        entity = storage.get(entity_id)
        if entity is None:
            return None

        return {k: v for k, v in entity.items() if not k.startswith("_")}

    async def update(self, entity_id: str, data: dict[str, Any]) -> None:
        """Update an existing entity."""
        storage = self._transaction_storage if self._in_transaction else self._storage
        if entity_id not in storage:
            raise EntityNotFoundError(f"Entity {entity_id} not found")

        existing = storage[entity_id]
        storage[entity_id] = {
            **data,
            "_created_at": existing.get(
                "_created_at", datetime.now(UTC).isoformat(),
            ),
            "_updated_at": datetime.now(UTC).isoformat(),
        }

    async def delete(self, entity_id: str) -> None:
        """Delete an entity."""
        storage = self._transaction_storage if self._in_transaction else self._storage
        if entity_id not in storage:
            raise EntityNotFoundError(f"Entity {entity_id} not found")

        del storage[entity_id]

    async def query(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query entities with filtering and pagination."""
        storage = self._transaction_storage if self._in_transaction else self._storage
        results = []

        for entity_data in storage.values():
            if filters:
                matches = all(entity_data.get(k) == v for k, v in filters.items())
                if not matches:
                    continue

            results.append(
                {k: v for k, v in entity_data.items() if not k.startswith("_")},
            )

        if order_by:
            descending = order_by.startswith("-")
            field = order_by.lstrip("-")
            results.sort(key=lambda x: x.get(field, ""), reverse=descending)

        return results[offset : offset + limit]

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count entities matching filters."""
        storage = self._transaction_storage if self._in_transaction else self._storage
        if not filters:
            return len(storage)

        return sum(
            1
            for entity_data in storage.values()
            if all(entity_data.get(k) == v for k, v in filters.items())
        )

    async def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        storage = self._transaction_storage if self._in_transaction else self._storage
        return entity_id in storage

    @asynccontextmanager
    async def transaction(self):
        """Start a transaction context."""
        if self._in_transaction:
            yield
            return

        self._transaction_storage = self._storage.copy()
        self._in_transaction = True

        try:
            yield
            self._storage = self._transaction_storage
        except Exception:
            pass
        finally:
            self._transaction_storage = None
            self._in_transaction = False

    async def close(self) -> None:
        """Close backend connection and cleanup resources."""
        self._storage.clear()
