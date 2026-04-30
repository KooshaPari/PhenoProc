"""SQLAlchemy backend implementation."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .base import RepositoryBackend
from .exceptions import (
    ConnectionError,
    EntityNotFoundError,
    RepositoryError,
    TransactionError,
)
from .sqlalchemy_model import _get_sqlalchemy_base

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


class SQLAlchemyBackend(RepositoryBackend):
    """SQLAlchemy implementation of RepositoryBackend.

    Supports any SQL database via SQLAlchemy with connection pooling,
    transactions, and advanced querying capabilities.
    """

    def __init__(
        self,
        database_url: str,
        entity_type: str = "default",
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
    ):
        """Initialize SQLAlchemy backend.

        Args:
            database_url: SQLAlchemy database URL (e.g., 'sqlite+aiosqlite:///db.sqlite',
                         'postgresql+asyncpg://user:pass@host/db')
            entity_type: Type identifier for entities in this repository
            echo: Echo SQL statements for debugging
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections beyond pool_size
            pool_timeout: Timeout for getting connection from pool (seconds)
            pool_recycle: Recycle connections after this many seconds
        """
        _get_sqlalchemy_base()

        self.database_url = database_url
        self.entity_type = entity_type
        self._engine: Any | None = None
        self._session_factory: Any | None = None

        self._pool_config = {
            "echo": echo,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_timeout": pool_timeout,
            "pool_recycle": pool_recycle,
            "pool_pre_ping": True,
        }

        self._active_session: Any | None = None

    async def _ensure_initialized(self) -> None:
        """Ensure engine and session factory are initialized."""
        if self._engine is None:
            try:
                from sqlalchemy.ext.asyncio import (
                    AsyncSession,
                    async_sessionmaker,
                    create_async_engine,
                )

                sa_base = _get_sqlalchemy_base()
                Base = sa_base["Base"]

                self._engine = create_async_engine(
                    self.database_url,
                    **self._pool_config,
                )
                self._session_factory = async_sessionmaker(
                    self._engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                )

                async with self._engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
            except ImportError:
                raise ConnectionError(
                    "SQLAlchemy is required. Install with: "
                    "pip install 'sqlalchemy>=2.0.0' 'aiosqlite>=0.19.0'",
                )
            except Exception as e:
                raise ConnectionError(f"Failed to initialize database connection: {e}")

    @asynccontextmanager
    async def _get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager.

        If a transaction is active, uses the active session.
        Otherwise, creates a new session.
        """
        await self._ensure_initialized()

        if self._active_session is not None:
            yield self._active_session
            return

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def _crud_create(self, entity_id: str, data: dict[str, Any]) -> None:
        """Create a new entity."""
        sa_base = _get_sqlalchemy_base()
        GenericEntity = sa_base["GenericEntity"]

        async with self._get_session() as session:
            entity = GenericEntity(
                id=entity_id,
                entity_type=self.entity_type,
                data=json.dumps(data),
            )
            session.add(entity)
            await session.flush()

    async def _crud_read(self, entity_id: str) -> dict[str, Any] | None:
        """Read an entity by ID."""
        from sqlalchemy import and_, select

        sa_base = _get_sqlalchemy_base()
        GenericEntity = sa_base["GenericEntity"]

        async with self._get_session() as session:
            stmt = select(GenericEntity).where(
                and_(
                    GenericEntity.id == entity_id,
                    GenericEntity.entity_type == self.entity_type,
                ),
            )
            result = await session.execute(stmt)
            entity = result.scalar_one_or_none()

            if entity is None:
                return None

            return json.loads(entity.data)

    async def _crud_update(self, entity_id: str, data: dict[str, Any]) -> None:
        """Update an existing entity."""
        from sqlalchemy import and_, update

        sa_base = _get_sqlalchemy_base()
        GenericEntity = sa_base["GenericEntity"]

        async with self._get_session() as session:
            stmt = (
                update(GenericEntity)
                .where(
                    and_(
                        GenericEntity.id == entity_id,
                        GenericEntity.entity_type == self.entity_type,
                    ),
                )
                .values(
                    data=json.dumps(data),
                    updated_at=datetime.now(datetime.UTC),
                )
            )
            result = await session.execute(stmt)

            if result.rowcount == 0:
                raise EntityNotFoundError(f"Entity {entity_id} not found")

            await session.flush()

    async def _crud_delete(self, entity_id: str) -> None:
        """Delete an entity."""
        from sqlalchemy import and_, delete

        sa_base = _get_sqlalchemy_base()
        GenericEntity = sa_base["GenericEntity"]

        async with self._get_session() as session:
            stmt = delete(GenericEntity).where(
                and_(
                    GenericEntity.id == entity_id,
                    GenericEntity.entity_type == self.entity_type,
                ),
            )
            result = await session.execute(stmt)

            if result.rowcount == 0:
                raise EntityNotFoundError(f"Entity {entity_id} not found")

            await session.flush()

    async def _crud_query(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query entities with filtering and pagination."""
        from sqlalchemy import and_, select

        sa_base = _get_sqlalchemy_base()
        GenericEntity = sa_base["GenericEntity"]

        async with self._get_session() as session:
            stmt = select(GenericEntity).where(
                GenericEntity.entity_type == self.entity_type,
            )

            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if key in ["id", "entity_type", "created_at", "updated_at"]:
                        filter_conditions.append(getattr(GenericEntity, key) == value)

                if filter_conditions:
                    stmt = stmt.where(and_(*filter_conditions))

            if order_by:
                descending = order_by.startswith("-")
                field = order_by.lstrip("-")

                if hasattr(GenericEntity, field):
                    col = getattr(GenericEntity, field)
                    stmt = stmt.order_by(col.desc() if descending else col)
            else:
                stmt = stmt.order_by(GenericEntity.created_at.desc())

            stmt = stmt.limit(limit).offset(offset)

            result = await session.execute(stmt)
            entities = result.scalars().all()

            return [json.loads(entity.data) for entity in entities]

    async def _crud_count(self, filters: dict[str, Any] | None = None) -> int:
        """Count entities matching filters."""
        from sqlalchemy import and_, func, select

        sa_base = _get_sqlalchemy_base()
        GenericEntity = sa_base["GenericEntity"]

        async with self._get_session() as session:
            stmt = select(func.count(GenericEntity.id)).where(
                GenericEntity.entity_type == self.entity_type,
            )

            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if key in ["id", "entity_type", "created_at", "updated_at"]:
                        filter_conditions.append(getattr(GenericEntity, key) == value)

                if filter_conditions:
                    stmt = stmt.where(and_(*filter_conditions))

            result = await session.execute(stmt)
            return result.scalar_one()

    async def _crud_exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        from sqlalchemy import and_, func, select

        sa_base = _get_sqlalchemy_base()
        GenericEntity = sa_base["GenericEntity"]

        async with self._get_session() as session:
            stmt = select(func.count(GenericEntity.id)).where(
                and_(
                    GenericEntity.id == entity_id,
                    GenericEntity.entity_type == self.entity_type,
                ),
            )
            result = await session.execute(stmt)
            return result.scalar_one() > 0

    async def create(self, entity_id: str, data: dict[str, Any]) -> None:
        try:
            await self._crud_create(entity_id, data)
        except Exception as e:
            raise RepositoryError(f"Failed to create entity {entity_id}: {e}")

    async def read(self, entity_id: str) -> dict[str, Any] | None:
        try:
            return await self._crud_read(entity_id)
        except Exception as e:
            raise RepositoryError(f"Failed to read entity {entity_id}: {e}")

    async def update(self, entity_id: str, data: dict[str, Any]) -> None:
        try:
            await self._crud_update(entity_id, data)
        except EntityNotFoundError:
            raise
        except Exception as e:
            raise RepositoryError(f"Failed to update entity {entity_id}: {e}")

    async def delete(self, entity_id: str) -> None:
        try:
            await self._crud_delete(entity_id)
        except EntityNotFoundError:
            raise
        except Exception as e:
            raise RepositoryError(f"Failed to delete entity {entity_id}: {e}")

    async def query(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str | None = None,
    ) -> list[dict[str, Any]]:
        try:
            return await self._crud_query(filters, limit, offset, order_by)
        except Exception as e:
            raise RepositoryError(f"Failed to query entities: {e}")

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        try:
            return await self._crud_count(filters)
        except Exception as e:
            raise RepositoryError(f"Failed to count entities: {e}")

    async def exists(self, entity_id: str) -> bool:
        try:
            return await self._crud_exists(entity_id)
        except Exception as e:
            raise RepositoryError(f"Failed to check entity existence: {e}")

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[None, None]:
        """Start a transaction context.

        All operations within this context will be part of the same transaction
        and will be committed or rolled back together.

        Example:
            async with backend.transaction():
                await backend.create("id1", {"name": "Entity 1"})
                await backend.create("id2", {"name": "Entity 2"})
                # Both creates will be committed together
        """
        await self._ensure_initialized()

        if self._active_session is not None:
            yield
            return

        async with self._session_factory() as session:
            try:
                self._active_session = session
                async with session.begin():
                    yield
            except Exception as e:
                await session.rollback()
                raise TransactionError(f"Transaction failed: {e}")
            finally:
                self._active_session = None

    async def close(self) -> None:
        """Close backend connection and cleanup resources."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._active_session = None
