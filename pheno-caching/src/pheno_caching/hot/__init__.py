"""
Hot Cache - In-Memory TTL-Based Caching

High-performance in-memory cache with TTL-based expiration for
frequently accessed data that tolerates brief staleness.

Performance: 10x improvement for repeated queries within TTL window.

Usage:
    >>> from pheno.caching.hot import QueryCache
    >>>
    >>> # Create cache with 30 second TTL
    >>> cache = QueryCache(ttl=30, max_size=1000)
    >>>
    >>> # Generate key and cache result
    >>> key = cache.generate_key("select", {"table": "users", "id": 123})
    >>> cache.set(key, {"name": "John", "email": "john@example.com"})
    >>>
    >>> # Retrieve from cache
    >>> result = cache.get(key)
    >>>
    >>> # Invalidate on writes
    >>> cache.invalidate_by_table("users")

Components:
- QueryCache: Core in-memory cache with TTL and LRU eviction
- CachedQueryMixin: Mixin for database adapters
"""

from .query_cache import CachedQueryMixin, QueryCache

__all__ = [
    "CachedQueryMixin",
    "QueryCache",
]
