"""
Pheno Caching Infrastructure - Comprehensive Multi-Layer Caching System

This package provides a complete caching infrastructure extracted from the atoms
project, offering three complementary caching strategies:

1. HOT CACHE (In-Memory TTL-Based)
   - 10x performance improvement for repeated queries
   - 30 second default TTL
   - LRU eviction with size limits
   - Automatic write invalidation
   - Thread-safe operations

2. COLD CACHE (Persistent Disk-Based)
   - Survives process restarts
   - Ideal for expensive computations (embeddings)
   - JSON-based storage
   - Configurable cache directory (~/.cache/pheno/)
   - Automatic cleanup

3. DRY-RUN SYSTEM (Non-Destructive Operations)
   - Safe testing without side effects
   - Preview mode for CLIs
   - Development/staging safety
   - Decorator-based control

Quick Start
-----------

Hot Cache (In-Memory):
    >>> from pheno.caching import QueryCache
    >>>
    >>> # Create cache with 30 second TTL
    >>> cache = QueryCache(ttl=30, max_size=1000)
    >>>
    >>> # Cache a query result
    >>> key = cache.generate_key("select", {"table": "users", "id": 123})
    >>> cache.set(key, {"name": "John", "email": "john@example.com"})
    >>>
    >>> # Retrieve from cache (10x faster!)
    >>> result = cache.get(key)
    >>> if result is None:
    ...     result = await db.query(...)
    ...     cache.set(key, result)

Cold Cache (Persistent):
    >>> from pheno.caching import EmbeddingCache
    >>>
    >>> # Create embedding cache (survives restarts)
    >>> cache = EmbeddingCache(ttl=86400)  # 24 hour TTL
    >>>
    >>> # Cache expensive embedding
    >>> cache.set_embedding(
    ...     "doc_123",
    ...     embedding=[0.1, 0.2, ...],
    ...     model="text-embedding-3-small",
    ...     dimensions=768
    ... )
    >>>
    >>> # Retrieve cached embedding (instant!)
    >>> result = cache.get_embedding("doc_123")
    >>> if result is None:
    ...     embedding = await generate_embedding(text)  # Expensive!
    ...     cache.set_embedding("doc_123", embedding, model, dims)

Dry-Run System:
    >>> from pheno.caching import set_dry_run, dry_run_aware
    >>>
    >>> # Enable dry-run mode
    >>> set_dry_run(True)
    >>>
    >>> # Decorate functions
    >>> @dry_run_aware(operation_name="delete_user", return_value={"deleted": False})
    >>> async def delete_user(user_id: str):
    ...     # In dry-run mode, this logs but doesn't execute
    ...     await db.delete("users", {"id": user_id})
    ...     return {"deleted": True}
    >>>
    >>> # Safe preview
    >>> result = await delete_user("123")  # Logs: [DRY RUN] Would execute...

Architecture
------------

Hot Cache Architecture:
    - Thread-safe OrderedDict for LRU behavior
    - MD5 key generation from operation + parameters
    - Automatic TTL-based expiration
    - Configurable size limits with automatic eviction
    - Statistics tracking (hits, misses, evictions)

Cold Cache Architecture:
    - JSON-based file storage
    - Namespace isolation (embeddings, test_data, etc.)
    - File-based locking for concurrent access
    - Automatic size management (max_size_mb)
    - Index file for metadata and fast lookups

Dry-Run Architecture:
    - Global state management with thread safety
    - Decorator-based interception
    - Async/sync function support
    - Context manager for scoped control
    - Instance-level dry-run via mixin

Integration Patterns
--------------------

Database Adapter Integration:
    >>> from pheno.caching import CachedQueryMixin
    >>>
    >>> class DatabaseAdapter(CachedQueryMixin):
    ...     def __init__(self):
    ...         self._init_cache(ttl=30, max_size=1000)
    ...
    ...     async def select(self, table: str, filters: dict):
    ...         key = self._query_cache.generate_key("select", {
    ...             "table": table, "filters": filters
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

Service with Dry-Run Support:
    >>> from pheno.caching import DryRunMixin, dry_run_method
    >>>
    >>> class BackfillService(DryRunMixin):
    ...     def __init__(self, dry_run: bool = False):
    ...         self._init_dry_run(dry_run)
    ...
    ...     @dry_run_method(return_value={"processed": 0, "skipped": 100})
    ...     async def backfill_embeddings(self, limit: int = 100):
    ...         # This will be skipped if dry_run=True
    ...         results = await self._process_embeddings(limit)
    ...         return results

Multi-Layer Caching Strategy:
    >>> from pheno.caching import QueryCache, EmbeddingCache
    >>>
    >>> # Hot cache for frequent queries (30s TTL)
    >>> query_cache = QueryCache(ttl=30)
    >>>
    >>> # Cold cache for embeddings (24h TTL)
    >>> embedding_cache = EmbeddingCache(ttl=86400)
    >>>
    >>> async def get_embedding(entity_id: str):
    ...     # Layer 1: Hot cache (instant)
    ...     key = query_cache.generate_key("embedding", {"id": entity_id})
    ...     result = query_cache.get(key)
    ...     if result is not None:
    ...         return result
    ...
    ...     # Layer 2: Cold cache (fast)
    ...     result = embedding_cache.get_embedding(entity_id)
    ...     if result is not None:
    ...         # Promote to hot cache
    ...         query_cache.set(key, result)
    ...         return result
    ...
    ...     # Layer 3: Generate (expensive)
    ...     embedding = await generate_embedding(entity_id)
    ...
    ...     # Cache in both layers
    ...     embedding_cache.set_embedding(entity_id, embedding, "model", 768)
    ...     query_cache.set(key, embedding)
    ...     return embedding

Performance Characteristics
---------------------------

Hot Cache Performance:
    - Cache Hit: ~0.001ms (in-memory lookup)
    - Cache Miss: Query time + ~0.01ms (hash generation + storage)
    - Speedup: 10x for repeated queries within TTL window
    - Memory: ~1KB per entry * max_size (default 1MB for 1000 entries)

Cold Cache Performance:
    - Cache Hit: ~1-5ms (disk read + JSON parse)
    - Cache Miss: Computation time + ~2-10ms (JSON write + disk sync)
    - Speedup: Eliminates expensive recomputation across restarts
    - Disk: Configurable max_size_mb (default 1000MB)

Dry-Run Performance:
    - Overhead: ~0.001ms per decorated function call
    - Impact: Negligible (simple boolean check)

Best Practices
--------------

1. Hot Cache Usage:
   - Use for: Frequently accessed data with acceptable staleness
   - TTL: 30-60 seconds for most queries
   - Size: 1000-10000 entries depending on memory
   - Invalidation: Always invalidate on writes to same table

2. Cold Cache Usage:
   - Use for: Expensive computations that rarely change
   - TTL: Hours to days (24h for embeddings)
   - Cleanup: Run periodic cleanup_expired() in background
   - Namespace: Use separate namespaces for different data types

3. Dry-Run Usage:
   - Use for: Any destructive operation (DELETE, UPDATE, INSERT)
   - Testing: Always test with dry_run=True first
   - CLI: Provide --dry-run flag for user safety
   - Logging: Log all dry-run operations for audit trail

4. Multi-Layer Strategy:
   - Hot cache: Recent/frequent data (seconds)
   - Cold cache: Expensive computations (hours/days)
   - Database: Source of truth (always)
   - Invalidation: Cascade from hot -> cold -> database

Thread Safety
-------------

All caching components are thread-safe:
- Hot cache: Uses threading.RLock for all operations
- Cold cache: File-based locking for concurrent access
- Dry-run: Global state protected by module-level locks

Async/await Support
-------------------

All decorators support both sync and async functions:
    >>> @dry_run_aware()
    >>> async def async_function():
    ...     pass
    >>>
    >>> @dry_run_aware()
    >>> def sync_function():
    ...     pass

Monitoring and Debugging
------------------------

Get cache statistics:
    >>> stats = cache.get_stats()
    >>> print(f"Hit rate: {stats['hit_rate']:.2%}")
    >>> print(f"Size: {stats['size']}/{stats['max_size']}")
    >>> print(f"Evictions: {stats['evictions']}")

Check dry-run state:
    >>> from pheno.caching import is_dry_run
    >>> if is_dry_run():
    ...     print("Running in dry-run mode")

Maintenance operations:
    >>> # Clean up expired entries
    >>> removed = cache.cleanup_expired()
    >>> print(f"Removed {removed} expired entries")
    >>>
    >>> # Clear entire cache
    >>> cache.clear()

Extracted From
--------------

- atoms/tools/query.py: Hot cache patterns for query optimization
- atoms/infrastructure/supabase_db.py: Database caching integration
- atoms/tests/framework/cache.py: Cold cache for test data
- atoms/scripts/backfill_embeddings.py: Dry-run system patterns

License
-------

Part of the Pheno SDK.
"""

# Cold Cache Exports
from .cold import DiskCache, EmbeddingCache, TestDataCache

# Dry-Run Exports
from .dry import (
    DryRunContext,
    DryRunMixin,
    dry_run_aware,
    dry_run_method,
    dry_run_skip,
    is_dry_run,
    set_dry_run,
)

# Hot Cache Exports
from .hot import CachedQueryMixin, QueryCache

__all__ = [
    "CachedQueryMixin",
    # Cold Cache
    "DiskCache",
    "DryRunContext",
    "DryRunMixin",
    "EmbeddingCache",
    # Hot Cache
    "QueryCache",
    "TestDataCache",
    "dry_run_aware",
    "dry_run_method",
    "dry_run_skip",
    "is_dry_run",
    # Dry-Run System
    "set_dry_run",
]

__version__ = "1.0.0"
