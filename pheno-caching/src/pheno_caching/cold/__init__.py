"""
Cold Cache - Persistent Disk-Based Caching

Persistent disk cache that survives process restarts, ideal for:
- Expensive embeddings (eliminates regeneration)
- Test data UUIDs (consistent across runs)
- Build artifacts and computed results
- Any data that outlives processes

Performance: Eliminates expensive recomputation across restarts.

Usage:
    >>> from pheno.caching.cold import EmbeddingCache, TestDataCache
    >>>
    >>> # Embedding cache (24 hour TTL)
    >>> embedding_cache = EmbeddingCache(ttl=86400)
    >>> embedding_cache.set_embedding(
    ...     "doc_123",
    ...     embedding=[0.1, 0.2, ...],
    ...     model="text-embedding-3-small",
    ...     dimensions=768
    ... )
    >>>
    >>> # Test data cache (never expires)
    >>> test_cache = TestDataCache()
    >>> test_cache.set_uuid("test_user", "550e8400-...")
    >>> user_id = test_cache.get_uuid("test_user")

Components:
- DiskCache: Generic persistent disk cache
- EmbeddingCache: Specialized for ML embeddings
- TestDataCache: Specialized for test data/UUIDs
"""

from .disk_cache import DiskCache, EmbeddingCache, TestDataCache

__all__ = [
    "DiskCache",
    "EmbeddingCache",
    "TestDataCache",
]
