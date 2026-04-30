"""DB-Kit: Universal database abstraction with RLS and multi-tenancy."""

from .adapters.base import DatabaseAdapter
from .adapters.neon import NeonAdapter
from .adapters.postgres import PostgreSQLAdapter
from .adapters.supabase import SupabaseAdapter
from .client import Database

# Connection pooling
from .pooling import (
    AsyncConnectionPool,
    ConnectionPoolConfig,
    ConnectionPoolManager,
    ConnectionStats,
    SyncConnectionPool,
    cleanup_all_pools,
    get_pool_manager,
    get_provider_pool,
)

# Realtime
from .realtime import RealtimeAdapter, SupabaseRealtimeAdapter

# Storage
from .storage import StorageAdapter, SupabaseStorageAdapter

__version__ = "0.1.0"

__all__ = [
    # Connection pooling
    "AsyncConnectionPool",
    "ConnectionPoolConfig",
    "ConnectionPoolManager",
    "ConnectionStats",
    # Database
    "Database",
    "DatabaseAdapter",
    "NeonAdapter",
    "PostgreSQLAdapter",
    # Realtime
    "RealtimeAdapter",
    # Storage
    "StorageAdapter",
    "SupabaseAdapter",
    "SupabaseRealtimeAdapter",
    "SupabaseStorageAdapter",
    "SyncConnectionPool",
    "cleanup_all_pools",
    "get_pool_manager",
    "get_provider_pool",
]
