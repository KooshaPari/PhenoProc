//! Caching layer for project registry
//!
//! Provides in-memory caching of project metadata with TTL support.

use crate::ProjectMetadata;
use dashmap::DashMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tracing::{debug, info};

/// Cached entry with TTL
#[derive(Debug, Clone)]
struct CachedEntry {
    project: ProjectMetadata,
    inserted_at: Instant,
    ttl: Duration,
}

impl CachedEntry {
    /// Check if the entry has expired
    fn is_expired(&self) -> bool {
        self.inserted_at.elapsed() > self.ttl
    }
}

/// Cache for project metadata
#[derive(Debug)]
pub struct ProjectCache {
    cache: DashMap<PathBuf, CachedEntry>,
    default_ttl: Duration,
}

impl Default for ProjectCache {
    fn default() -> Self {
        Self::new(Duration::from_secs(300)) // 5 minutes default TTL
    }
}

impl ProjectCache {
    /// Create a new cache with the specified default TTL
    ///
    /// # Example
    ///
    /// ```rust
    /// use phenotype_project_registry::cache::ProjectCache;
    /// use std::time::Duration;
    ///
    /// let cache = ProjectCache::new(Duration::from_secs(60));
    /// ```
    pub fn new(default_ttl: Duration) -> Self {
        Self {
            cache: DashMap::new(),
            default_ttl,
        }
    }

    /// Get a project from the cache
    ///
    /// Returns `Some(ProjectMetadata)` if found and not expired,
    /// `None` otherwise.
    pub fn get(&self, path: &Path) -> Option<ProjectMetadata> {
        let key = path.to_path_buf();

        if let Some(entry) = self.cache.get(&key) {
            if entry.is_expired() {
                debug!("Cache entry expired for: {}", path.display());
                drop(entry); // Release the ref before removing
                self.cache.remove(&key);
                return None;
            }
            debug!("Cache hit for: {}", path.display());
            return Some(entry.project.clone());
        }

        debug!("Cache miss for: {}", path.display());
        None
    }

    /// Insert a project into the cache
    pub fn insert(&self, path: &Path, project: ProjectMetadata) {
        let entry = CachedEntry {
            project,
            inserted_at: Instant::now(),
            ttl: self.default_ttl,
        };
        self.cache.insert(path.to_path_buf(), entry);
        debug!("Cached project at: {}", path.display());
    }

    /// Insert a project with a custom TTL
    pub fn insert_with_ttl(&self, path: &Path, project: ProjectMetadata, ttl: Duration) {
        let entry = CachedEntry {
            project,
            inserted_at: Instant::now(),
            ttl,
        };
        self.cache.insert(path.to_path_buf(), entry);
        debug!("Cached project at: {} with TTL {:?}", path.display(), ttl);
    }

    /// Remove a project from the cache
    pub fn invalidate(&self, path: &Path) {
        self.cache.remove(&path.to_path_buf());
        debug!("Invalidated cache for: {}", path.display());
    }

    /// Clear all cached entries
    pub fn clear(&self) {
        self.cache.clear();
        info!("Cache cleared");
    }

    /// Get cache statistics
    pub fn stats(&self) -> CacheStats {
        let total = self.cache.len();
        let expired = self.cache.iter().filter(|e| e.value().is_expired()).count();

        CacheStats {
            total_entries: total,
            expired_entries: expired,
            valid_entries: total - expired,
        }
    }

    /// Remove all expired entries
    pub fn cleanup(&self) {
        let before = self.cache.len();
        self.cache.retain(|_, entry| !entry.is_expired());
        let after = self.cache.len();
        let removed = before - after;
        if removed > 0 {
            info!("Cleaned up {} expired cache entries", removed);
        }
    }

    /// Start background cleanup task
    ///
    /// Spawns a task that periodically cleans up expired entries.
    /// Returns a `JoinHandle` that can be used to stop the task.
    pub fn start_cleanup_task(self: &Arc<Self>, interval: Duration) -> tokio::task::JoinHandle<()> {
        let cache = Arc::clone(self);

        tokio::spawn(async move {
            let mut ticker = tokio::time::interval(interval);
            loop {
                ticker.tick().await;
                cache.cleanup();
            }
        })
    }
}

/// Cache statistics
#[derive(Debug, Clone, Copy, Default)]
pub struct CacheStats {
    /// Total number of entries in the cache
    pub total_entries: usize,
    /// Number of expired entries
    pub expired_entries: usize,
    /// Number of valid entries
    pub valid_entries: usize,
}

/// Cached project registry
///
/// Wraps a standard registry with caching capabilities.
#[derive(Debug)]
pub struct CachedRegistry {
    inner: crate::ProjectRegistry,
    cache: Arc<ProjectCache>,
}

impl CachedRegistry {
    /// Create a new cached registry
    pub fn new(cache_ttl: Duration) -> Self {
        Self {
            inner: crate::ProjectRegistry::new(),
            cache: Arc::new(ProjectCache::new(cache_ttl)),
        }
    }

    /// Register a project
    pub fn register(&mut self, project: ProjectMetadata) {
        // Also cache it
        self.cache.insert(&project.path, project.clone());
        self.inner.register(project);
    }

    /// Get a project by name (from cache if available)
    pub fn get(&self, name: &str) -> Option<&ProjectMetadata> {
        self.inner.get(name)
    }

    /// Get all registered projects
    pub fn all(&self) -> Vec<&ProjectMetadata> {
        self.inner.all()
    }

    /// Get cache statistics
    pub fn cache_stats(&self) -> CacheStats {
        self.cache.stats()
    }

    /// Invalidate a specific cache entry
    pub fn invalidate_cache(&self, path: &Path) {
        self.cache.invalidate(path);
    }

    /// Clear the cache
    pub fn clear_cache(&self) {
        self.cache.clear();
    }

    /// Get access to the underlying cache
    pub fn cache(&self) -> &Arc<ProjectCache> {
        &self.cache
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;

    #[test]
    fn test_cache_insert_and_get() {
        let cache = ProjectCache::new(Duration::from_secs(60));
        let project = ProjectMetadata::new("test", "/tmp/test");

        cache.insert(Path::new("/tmp/test"), project.clone());

        let retrieved = cache.get(Path::new("/tmp/test"));
        assert!(retrieved.is_some());
        assert_eq!(retrieved.unwrap().name, "test");
    }

    #[test]
    fn test_cache_expiration() {
        let cache = ProjectCache::new(Duration::from_millis(10));
        let project = ProjectMetadata::new("test", "/tmp/test");

        cache.insert(Path::new("/tmp/test"), project);

        // Wait for expiration
        std::thread::sleep(Duration::from_millis(20));

        let retrieved = cache.get(Path::new("/tmp/test"));
        assert!(retrieved.is_none());
    }

    #[test]
    fn test_cache_stats() {
        let cache = ProjectCache::new(Duration::from_secs(60));
        let project = ProjectMetadata::new("test", "/tmp/test");

        cache.insert(Path::new("/tmp/test"), project);

        let stats = cache.stats();
        assert_eq!(stats.total_entries, 1);
        assert_eq!(stats.valid_entries, 1);
    }
}
