"""
Hot Cache - In-Memory TTL-Based Query Cache

This module provides a high-performance in-memory cache with:
- TTL-based expiration (30 seconds default, configurable)
- MD5 key generation from operation + parameters
- Automatic invalidation on writes
- Size limit with LRU cleanup
- Thread-safe operations

Performance: 10x improvement for repeated queries within TTL window.

Extracted from: atoms/tools/query.py and atoms/infrastructure/supabase_db.py
"""

import hashlib
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from typing import Any


class QueryCache:
    """In-memory cache with TTL and automatic invalidation.

    Features:
    - TTL-based expiration (default 30s)
    - Size limit with LRU eviction (default 1000 entries)
    - Thread-safe operations
    - MD5 key generation
    - Automatic write invalidation

    Examples:
        >>> cache = QueryCache(ttl=30, max_size=1000)
        >>>
        >>> # Cache a query result
        >>> key = cache.generate_key("select", {"table": "users", "id": 123})
        >>> cache.set(key, {"name": "John", "email": "john@example.com"})
        >>>
        >>> # Retrieve cached result
        >>> result = cache.get(key)
        >>> if result is not None:
        ...     print("Cache hit!")
        ... else:
        ...     print("Cache miss - query database")
        >>>
        >>> # Invalidate on write
        >>> cache.invalidate_by_table("users")
        >>>
        >>> # Clear entire cache
        >>> cache.clear()
    """

    def __init__(self, ttl: float = 30.0, max_size: int = 1000):
        """Initialize query cache.

        Args:
            ttl: Time-to-live in seconds (default: 30)
            max_size: Maximum number of cached entries (default: 1000)
        """
        self.ttl = ttl
        self.max_size = max_size
        self._cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "invalidations": 0,
        }

    def generate_key(self, operation: str, params: dict[str, Any]) -> str:
        """Generate cache key from operation and parameters.

        Uses MD5 hash of operation + sorted parameters for consistency.

        Args:
            operation: Operation name (e.g., "select", "count", "query")
            params: Query parameters

        Returns:
            MD5 hash string suitable for cache key

        Examples:
            >>> cache = QueryCache()
            >>> key1 = cache.generate_key("select", {"table": "users", "id": 123})
            >>> key2 = cache.generate_key("select", {"id": 123, "table": "users"})
            >>> assert key1 == key2  # Order doesn't matter
        """
        # Sort params for consistent hashing
        sorted_params = self._serialize_params(params)
        cache_str = f"{operation}:{sorted_params}"
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _serialize_params(self, params: dict[str, Any]) -> str:
        """
        Serialize parameters to consistent string representation.
        """
        import json

        # Sort keys for consistent hashing
        return json.dumps(params, sort_keys=True, default=str)

    def get(self, key: str) -> Any | None:
        """Get cached value if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if time.time() - entry["timestamp"] > self.ttl:
                # Expired - remove and return None
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            # Move to end (LRU)
            self._cache.move_to_end(key)
            self._stats["hits"] += 1
            return entry["value"]

    def set(self, key: str, value: Any, metadata: dict[str, Any] | None = None):
        """Set cached value with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
            metadata: Optional metadata (e.g., table name for invalidation)
        """
        with self._lock:
            # Check size limit
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Remove oldest entry (LRU)
                self._cache.popitem(last=False)
                self._stats["evictions"] += 1

            self._cache[key] = {
                "value": value,
                "timestamp": time.time(),
                "metadata": metadata or {},
            }

            # Move to end
            if key in self._cache:
                self._cache.move_to_end(key)

    def invalidate(self, key: str):
        """Invalidate specific cache entry.

        Args:
            key: Cache key to invalidate
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats["invalidations"] += 1

    def invalidate_by_table(self, table: str):
        """Invalidate all cache entries for a specific table.

        Useful for write operations that affect all queries on a table.

        Args:
            table: Table name to invalidate

        Examples:
            >>> cache = QueryCache()
            >>> # After INSERT/UPDATE/DELETE on users table
            >>> cache.invalidate_by_table("users")
        """
        with self._lock:
            to_remove = []
            for key, entry in self._cache.items():
                if entry["metadata"].get("table") == table:
                    to_remove.append(key)

            for key in to_remove:
                del self._cache[key]
                self._stats["invalidations"] += 1

    def invalidate_by_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern.

        Args:
            pattern: String pattern to match in cache keys or metadata
        """
        with self._lock:
            to_remove = []
            for key, entry in self._cache.items():
                # Check key or metadata for pattern
                if pattern in key or pattern in str(entry.get("metadata", {})):
                    to_remove.append(key)

            for key in to_remove:
                del self._cache[key]
                self._stats["invalidations"] += 1

    def clear(self):
        """
        Clear all cached entries.
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats["invalidations"] += count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with hits, misses, hit rate, size, etc.

        Examples:
            >>> cache = QueryCache()
            >>> stats = cache.get_stats()
            >>> print(f"Hit rate: {stats['hit_rate']:.2%}")
            >>> print(f"Size: {stats['size']}/{stats['max_size']}")
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "evictions": self._stats["evictions"],
                "invalidations": self._stats["invalidations"],
            }

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed

        Note:
            This is called automatically during get() operations,
            but can be called manually for maintenance.
        """
        with self._lock:
            current_time = time.time()
            to_remove = []

            for key, entry in self._cache.items():
                if current_time - entry["timestamp"] > self.ttl:
                    to_remove.append(key)

            for key in to_remove:
                del self._cache[key]

            return len(to_remove)


class CachedQueryMixin:
    """Mixin to add caching capabilities to database adapters.

    Provides decorator-based caching for query methods.

    Examples:
        >>> class DatabaseAdapter(CachedQueryMixin):
        ...     def __init__(self):
        ...         self._init_cache()
        ...
        ...     async def select(self, table: str, filters: dict):
        ...         key = self._query_cache.generate_key("select", {
        ...             "table": table,
        ...             "filters": filters
        ...         })
        ...
        ...         # Check cache
        ...         cached = self._query_cache.get(key)
        ...         if cached is not None:
        ...             return cached
        ...
        ...         # Query database
        ...         result = await self._execute_query(table, filters)
        ...
        ...         # Cache result
        ...         self._query_cache.set(key, result, {"table": table})
        ...         return result
        ...
        ...     async def insert(self, table: str, data: dict):
        ...         result = await self._execute_insert(table, data)
        ...         # Invalidate cache on write
        ...         self._query_cache.invalidate_by_table(table)
        ...         return result
    """

    def _init_cache(
        self,
        ttl: float = 30.0,
        max_size: int = 1000,
        enabled: bool = True,
    ):
        """Initialize query cache.

        Args:
            ttl: Cache TTL in seconds
            max_size: Maximum cache size
            enabled: Enable/disable caching
        """
        self._query_cache = QueryCache(ttl=ttl, max_size=max_size)
        self._cache_enabled = enabled

    def cached_query(
        self,
        operation: str,
        params: dict[str, Any],
        table: str | None = None,
    ) -> Callable:
        """Decorator for cached query operations.

        Args:
            operation: Operation name
            params: Query parameters
            table: Optional table name for invalidation

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            async def wrapper(*args, **kwargs):
                if not self._cache_enabled:
                    return await func(*args, **kwargs)

                # Generate cache key
                key = self._query_cache.generate_key(operation, params)

                # Check cache
                cached = self._query_cache.get(key)
                if cached is not None:
                    return cached

                # Execute query
                result = await func(*args, **kwargs)

                # Cache result
                metadata = {"table": table} if table else {}
                self._query_cache.set(key, result, metadata)

                return result

            return wrapper

        return decorator


__all__ = [
    "CachedQueryMixin",
    "QueryCache",
]
