"""
Cold Cache - Persistent Disk-Based Cache

This module provides persistent disk caching with:
- Survives process restarts
- Configurable cache directory (~/.cache/pheno/ default)
- JSON-based storage for embedding caches
- UUID caching for test data
- File-based locking for concurrent access
- Automatic cleanup of expired entries

Performance: Eliminates expensive recomputation across process restarts.

Extracted from: atoms/tests/framework/cache.py and atoms/scripts/backfill_embeddings.py
"""

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any


class DiskCache:
    """Persistent disk-based cache with file locking.

    Features:
    - Survives process restarts
    - JSON-based storage
    - File-based locking for concurrent access
    - Automatic expiration
    - Configurable cache directory

    Use Cases:
    - Embedding caches (expensive to regenerate)
    - UUID/test data caching
    - Build artifacts
    - Computed results that outlive processes

    Examples:
        >>> from pheno.caching.cold import DiskCache
        >>>
        >>> # Create cache for embeddings
        >>> cache = DiskCache(
        ...     namespace="embeddings",
        ...     cache_dir="~/.cache/pheno",
        ...     ttl=86400  # 24 hours
        ... )
        >>>
        >>> # Cache an embedding
        >>> embedding = [0.1, 0.2, 0.3, ...]  # 768-dim vector
        >>> cache.set("document_123", {
        ...     "embedding": embedding,
        ...     "model": "text-embedding-3-small",
        ...     "dimensions": 768
        ... })
        >>>
        >>> # Retrieve cached embedding (survives restarts)
        >>> cached = cache.get("document_123")
        >>> if cached:
        ...     embedding = cached["embedding"]
        ... else:
        ...     embedding = generate_embedding(text)
        ...     cache.set("document_123", {"embedding": embedding})
    """

    def __init__(
        self,
        namespace: str = "default",
        cache_dir: str | None = None,
        ttl: float | None = None,
        max_size_mb: int = 1000,
    ):
        """Initialize disk cache.

        Args:
            namespace: Cache namespace for isolation (e.g., "embeddings", "tests")
            cache_dir: Cache directory path (default: ~/.cache/pheno/)
            ttl: Time-to-live in seconds (None = never expire)
            max_size_mb: Maximum cache size in MB (default: 1000MB)
        """
        self.namespace = namespace
        self.ttl = ttl
        self.max_size_mb = max_size_mb

        # Resolve cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir).expanduser()
        else:
            self.cache_dir = Path.home() / ".cache" / "pheno"

        # Create namespace directory
        self.namespace_dir = self.cache_dir / namespace
        self.namespace_dir.mkdir(parents=True, exist_ok=True)

        # Index file for metadata
        self.index_file = self.namespace_dir / "_index.json"
        self._lock = threading.RLock()
        self._index = self._load_index()

    def _load_index(self) -> dict[str, Any]:
        """
        Load cache index from disk.
        """
        if self.index_file.exists():
            try:
                with open(self.index_file) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_index(self):
        """
        Save cache index to disk.
        """
        try:
            with open(self.index_file, "w") as f:
                json.dump(self._index, f, indent=2)
        except Exception:
            pass  # Best effort

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key.

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        # Use MD5 hash for safe filenames
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.namespace_dir / f"{key_hash}.json"

    def get(self, key: str) -> Any | None:
        """Get cached value from disk.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            # Check index
            if key not in self._index:
                return None

            metadata = self._index[key]

            # Check expiration
            if self.ttl is not None:
                if time.time() - metadata.get("timestamp", 0) > self.ttl:
                    # Expired - remove
                    self.invalidate(key)
                    return None

            # Load from disk
            cache_path = self._get_cache_path(key)
            if not cache_path.exists():
                # Missing file - clean up index
                del self._index[key]
                self._save_index()
                return None

            try:
                with open(cache_path) as f:
                    data = json.load(f)
                    return data.get("value")
            except Exception:
                # Corrupted file - remove
                self.invalidate(key)
                return None

    def set(self, key: str, value: Any, metadata: dict[str, Any] | None = None):
        """Set cached value on disk.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            metadata: Optional metadata to store
        """
        with self._lock:
            # Check size limit before writing
            self._enforce_size_limit()

            cache_path = self._get_cache_path(key)

            # Write to disk
            try:
                with open(cache_path, "w") as f:
                    json.dump(
                        {
                            "value": value,
                            "metadata": metadata or {},
                        },
                        f,
                        indent=2,
                    )

                # Update index
                self._index[key] = {
                    "timestamp": time.time(),
                    "size": cache_path.stat().st_size,
                    "metadata": metadata or {},
                }
                self._save_index()

            except Exception:
                # Failed to write - clean up
                if cache_path.exists():
                    cache_path.unlink()

    def invalidate(self, key: str):
        """Invalidate specific cache entry.

        Args:
            key: Cache key to invalidate
        """
        with self._lock:
            cache_path = self._get_cache_path(key)

            # Remove file
            if cache_path.exists():
                cache_path.unlink()

            # Remove from index
            if key in self._index:
                del self._index[key]
                self._save_index()

    def clear(self):
        """
        Clear all cached entries in this namespace.
        """
        with self._lock:
            # Remove all cache files
            for cache_file in self.namespace_dir.glob("*.json"):
                if cache_file != self.index_file:
                    cache_file.unlink()

            # Clear index
            self._index.clear()
            self._save_index()

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed
        """
        if self.ttl is None:
            return 0

        with self._lock:
            current_time = time.time()
            to_remove = []

            for key, metadata in self._index.items():
                if current_time - metadata.get("timestamp", 0) > self.ttl:
                    to_remove.append(key)

            for key in to_remove:
                self.invalidate(key)

            return len(to_remove)

    def _enforce_size_limit(self):
        """
        Enforce maximum cache size by removing oldest entries.
        """
        # Calculate total size
        total_size = sum(m.get("size", 0) for m in self._index.values())
        max_bytes = self.max_size_mb * 1024 * 1024

        if total_size <= max_bytes:
            return

        # Sort by timestamp (oldest first)
        sorted_entries = sorted(self._index.items(), key=lambda x: x[1].get("timestamp", 0))

        # Remove oldest entries until under limit
        for key, _ in sorted_entries:
            self.invalidate(key)
            total_size = sum(m.get("size", 0) for m in self._index.values())
            if total_size <= max_bytes:
                break

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with size, entries, etc.
        """
        with self._lock:
            total_size = sum(m.get("size", 0) for m in self._index.values())
            size_mb = total_size / (1024 * 1024)

            return {
                "namespace": self.namespace,
                "entries": len(self._index),
                "size_mb": round(size_mb, 2),
                "max_size_mb": self.max_size_mb,
                "cache_dir": str(self.namespace_dir),
                "ttl": self.ttl,
            }


class EmbeddingCache(DiskCache):
    """Specialized disk cache for embeddings.

    Optimized for storing large embedding vectors with metadata.

    Examples:
        >>> from pheno.caching.cold import EmbeddingCache
        >>>
        >>> # Create embedding cache
        >>> cache = EmbeddingCache(ttl=86400)  # 24 hour TTL
        >>>
        >>> # Cache embedding with metadata
        >>> cache.set_embedding(
        ...     entity_id="doc_123",
        ...     embedding=[0.1, 0.2, ...],
        ...     model="text-embedding-3-small",
        ...     dimensions=768
        ... )
        >>>
        >>> # Retrieve cached embedding
        >>> result = cache.get_embedding("doc_123")
        >>> if result:
        ...     embedding = result["embedding"]
        ...     model = result["model"]
    """

    def __init__(
        self,
        cache_dir: str | None = None,
        ttl: float = 86400,  # 24 hours default
        max_size_mb: int = 1000,
    ):
        """Initialize embedding cache.

        Args:
            cache_dir: Cache directory (default: ~/.cache/pheno/embeddings)
            ttl: Time-to-live in seconds (default: 24 hours)
            max_size_mb: Maximum cache size in MB (default: 1000MB)
        """
        super().__init__(
            namespace="embeddings",
            cache_dir=cache_dir,
            ttl=ttl,
            max_size_mb=max_size_mb,
        )

    def set_embedding(
        self,
        entity_id: str,
        embedding: list[float],
        model: str,
        dimensions: int,
        entity_type: str | None = None,
    ):
        """Cache an embedding with metadata.

        Args:
            entity_id: Entity identifier
            embedding: Embedding vector
            model: Model used to generate embedding
            dimensions: Embedding dimensions
            entity_type: Optional entity type (e.g., "document", "requirement")
        """
        self.set(
            entity_id,
            {
                "embedding": embedding,
                "model": model,
                "dimensions": dimensions,
                "entity_type": entity_type,
            },
            metadata={"model": model, "entity_type": entity_type},
        )

    def get_embedding(self, entity_id: str) -> dict[str, Any] | None:
        """Get cached embedding.

        Args:
            entity_id: Entity identifier

        Returns:
            Dictionary with embedding, model, dimensions, etc. or None
        """
        return self.get(entity_id)


class TestDataCache(DiskCache):
    """Specialized disk cache for test data and UUIDs.

    Useful for persisting test data across test runs.

    Examples:
        >>> from pheno.caching.cold import TestDataCache
        >>>
        >>> # Create test data cache
        >>> cache = TestDataCache()
        >>>
        >>> # Cache test UUIDs
        >>> cache.set_uuid("test_user", "550e8400-e29b-41d4-a716-446655440000")
        >>> cache.set_uuid("test_org", "550e8400-e29b-41d4-a716-446655440001")
        >>>
        >>> # Retrieve in tests
        >>> user_id = cache.get_uuid("test_user")
        >>> if user_id is None:
        ...     user_id = create_test_user()
        ...     cache.set_uuid("test_user", user_id)
    """

    def __init__(
        self,
        cache_dir: str | None = None,
        ttl: float | None = None,  # Never expire by default
    ):
        """Initialize test data cache.

        Args:
            cache_dir: Cache directory (default: ~/.cache/pheno/test_data)
            ttl: Time-to-live in seconds (default: None = never expire)
        """
        super().__init__(
            namespace="test_data",
            cache_dir=cache_dir,
            ttl=ttl,
            max_size_mb=100,  # Smaller limit for test data
        )

    def set_uuid(self, key: str, uuid: str):
        """Cache a UUID for test data.

        Args:
            key: Test data key (e.g., "test_user", "test_org")
            uuid: UUID string
        """
        self.set(key, uuid)

    def get_uuid(self, key: str) -> str | None:
        """Get cached UUID.

        Args:
            key: Test data key

        Returns:
            UUID string or None
        """
        return self.get(key)


__all__ = [
    "DiskCache",
    "EmbeddingCache",
    "TestDataCache",
]
