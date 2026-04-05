//! Generic in-memory store implementations for testing and development
//!
//! This crate provides thread-safe, async-compatible in-memory stores
//! that can be used for testing, development, or as caches.

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use thiserror::Error;
use tokio::sync::RwLock;

/// Result type for store operations
pub type StoreResult<T> = Result<T, StoreError>;

/// Store error types
#[derive(Debug, Error)]
pub enum StoreError {
    #[error("Key not found: {0}")]
    NotFound(String),

    #[error("Key already exists: {0}")]
    AlreadyExists(String),

    #[error("Serialization error: {0}")]
    Serialization(String),

    #[error("Internal error: {0}")]
    Internal(String),
}

/// Store trait for key-value operations
#[async_trait]
pub trait Store<K, V>: Send + Sync
where
    K: Serialize + Deserialize<'static> + Send + Sync,
    V: Serialize + Deserialize<'static> + Send + Sync,
{
    /// Get a value by key
    async fn get(&self, key: &K) -> StoreResult<Option<V>>;

    /// Set a value (insert or update)
    async fn set(&self, key: K, value: V) -> StoreResult<()>;

    /// Delete a value by key
    async fn delete(&self, key: &K) -> StoreResult<()>;

    /// Check if key exists
    async fn exists(&self, key: &K) -> StoreResult<bool>;

    /// List all keys
    async fn keys(&self) -> StoreResult<Vec<K>>;

    /// Get all key-value pairs
    async fn entries(&self) -> StoreResult<Vec<(K, V)>>;

    /// Clear all entries
    async fn clear(&self) -> StoreResult<()>;

    /// Get count of entries
    async fn len(&self) -> StoreResult<usize>;

    /// Check if empty
    async fn is_empty(&self) -> StoreResult<bool>;
}

/// In-memory store implementation using RwLock<HashMap>
pub struct InMemoryStore<K, V> {
    data: Arc<RwLock<HashMap<K, V>>>,
}

impl<K, V> InMemoryStore<K, V>
where
    K: Serialize + Deserialize<'static> + Eq + std::hash::Hash + Clone,
    V: Serialize + Deserialize<'static> + Clone,
{
    pub fn new() -> Self {
        Self {
            data: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Create with initial capacity
    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            data: Arc::new(RwLock::new(HashMap::with_capacity(capacity))),
        }
    }
}

impl<K, V> Default for InMemoryStore<K, V>
where
    K: Serialize + Deserialize<'static> + Eq + std::hash::Hash + Clone,
    V: Serialize + Deserialize<'static> + Clone,
{
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl<K, V> Store<K, V> for InMemoryStore<K, V>
where
    K: Serialize + Deserialize<'static> + Eq + std::hash::Hash + Clone + Send + Sync,
    V: Serialize + Deserialize<'static> + Clone + Send + Sync,
{
    async fn get(&self, key: &K) -> StoreResult<Option<V>> {
        let data = self.data.read().await;
        Ok(data.get(key).cloned())
    }

    async fn set(&self, key: K, value: V) -> StoreResult<()> {
        let mut data = self.data.write().await;
        data.insert(key, value);
        Ok(())
    }

    async fn delete(&self, key: &K) -> StoreResult<()> {
        let mut data = self.data.write().await;
        data.remove(key);
        Ok(())
    }

    async fn exists(&self, key: &K) -> StoreResult<bool> {
        let data = self.data.read().await;
        Ok(data.contains_key(key))
    }

    async fn keys(&self) -> StoreResult<Vec<K>> {
        let data = self.data.read().await;
        Ok(data.keys().cloned().collect())
    }

    async fn entries(&self) -> StoreResult<Vec<(K, V)>> {
        let data = self.data.read().await;
        Ok(data.iter().map(|(k, v)| (k.clone(), v.clone())).collect())
    }

    async fn clear(&self) -> StoreResult<()> {
        let mut data = self.data.write().await;
        data.clear();
        Ok(())
    }

    async fn len(&self) -> StoreResult<usize> {
        let data = self.data.read().await;
        Ok(data.len())
    }

    async fn is_empty(&self) -> StoreResult<bool> {
        let data = self.data.read().await;
        Ok(data.is_empty())
    }
}

/// In-memory store with TTL support
pub struct InMemoryStoreWithTTL<K, V> {
    data: Arc<RwLock<HashMap<K, (V, chrono::DateTime<chrono::Utc>)>>>,
    ttl_seconds: i64,
}

impl<K, V> InMemoryStoreWithTTL<K, V>
where
    K: Serialize + Deserialize<'static> + Eq + std::hash::Hash + Clone,
    V: Serialize + Deserialize<'static> + Clone,
{
    pub fn new(ttl_seconds: i64) -> Self {
        Self {
            data: Arc::new(RwLock::new(HashMap::new())),
            ttl_seconds,
        }
    }

    async fn is_expired(&self, expires_at: &chrono::DateTime<chrono::Utc>) -> bool {
        chrono::Utc::now() > *expires_at
    }
}

#[async_trait]
impl<K, V> Store<K, V> for InMemoryStoreWithTTL<K, V>
where
    K: Serialize + Deserialize<'static> + Eq + std::hash::Hash + Clone + Send + Sync,
    V: Serialize + Deserialize<'static> + Clone + Send + Sync,
{
    async fn get(&self, key: &K) -> StoreResult<Option<V>> {
        let data = self.data.read().await;

        if let Some((value, expires_at)) = data.get(key) {
            if self.is_expired(expires_at).await {
                return Ok(None);
            }
            return Ok(Some(value.clone()));
        }

        Ok(None)
    }

    async fn set(&self, key: K, value: V) -> StoreResult<()> {
        let expires_at = chrono::Utc::now() + chrono::Duration::seconds(self.ttl_seconds);
        let mut data = self.data.write().await;
        data.insert(key, (value, expires_at));
        Ok(())
    }

    async fn delete(&self, key: &K) -> StoreResult<()> {
        let mut data = self.data.write().await;
        data.remove(key);
        Ok(())
    }

    async fn exists(&self, key: &K) -> StoreResult<bool> {
        let data = self.data.read().await;

        if let Some((_, expires_at)) = data.get(key) {
            if self.is_expired(expires_at).await {
                return Ok(false);
            }
            return Ok(true);
        }

        Ok(false)
    }

    async fn keys(&self) -> StoreResult<Vec<K>> {
        let data = self.data.read().await;
        let now = chrono::Utc::now();

        let valid_keys: Vec<K> = data
            .iter()
            .filter(|(_, (_, expires_at))| now <= *expires_at)
            .map(|(k, _)| k.clone())
            .collect();

        Ok(valid_keys)
    }

    async fn entries(&self) -> StoreResult<Vec<(K, V)>> {
        let data = self.data.read().await;
        let now = chrono::Utc::now();

        let valid_entries: Vec<(K, V)> = data
            .iter()
            .filter(|(_, (_, expires_at))| now <= *expires_at)
            .map(|(k, (v, _))| (k.clone(), v.clone()))
            .collect();

        Ok(valid_entries)
    }

    async fn clear(&self) -> StoreResult<()> {
        let mut data = self.data.write().await;
        data.clear();
        Ok(())
    }

    async fn len(&self) -> StoreResult<usize> {
        // Count non-expired entries
        self.keys().await.map(|k| k.len())
    }

    async fn is_empty(&self) -> StoreResult<bool> {
        self.len().await.map(|l| l == 0)
    }
}

/// Builder for creating stores with custom configurations
pub struct StoreBuilder<K, V> {
    capacity: Option<usize>,
    ttl_seconds: Option<i64>,
    _phantom: std::marker::PhantomData<(K, V)>,
}

impl<K, V> StoreBuilder<K, V> {
    pub fn new() -> Self {
        Self {
            capacity: None,
            ttl_seconds: None,
            _phantom: std::marker::PhantomData,
        }
    }

    pub fn capacity(mut self, capacity: usize) -> Self {
        self.capacity = Some(capacity);
        self
    }

    pub fn ttl(mut self, seconds: i64) -> Self {
        self.ttl_seconds = Some(seconds);
        self
    }

    pub fn build(self) -> InMemoryStore<K, V>
    where
        K: Serialize + Deserialize<'static> + Eq + std::hash::Hash + Clone,
        V: Serialize + Deserialize<'static> + Clone,
    {
        match self.capacity {
            Some(cap) => InMemoryStore::with_capacity(cap),
            None => InMemoryStore::new(),
        }
    }

    pub fn build_with_ttl(self) -> InMemoryStoreWithTTL<K, V>
    where
        K: Serialize + Deserialize<'static> + Eq + std::hash::Hash + Clone,
        V: Serialize + Deserialize<'static> + Clone,
    {
        let ttl = self.ttl_seconds.unwrap_or(300); // Default 5 minutes
        InMemoryStoreWithTTL::new(ttl)
    }
}

impl<K, V> Default for StoreBuilder<K, V> {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_basic_operations() {
        let store = InMemoryStore::<String, String>::new();

        // Test set and get
        store
            .set("key1".to_string(), "value1".to_string())
            .await
            .unwrap();
        let result = store.get(&"key1".to_string()).await.unwrap();
        assert_eq!(result, Some("value1".to_string()));

        // Test exists
        assert!(store.exists(&"key1".to_string()).await.unwrap());
        assert!(!store.exists(&"key2".to_string()).await.unwrap());

        // Test delete
        store.delete(&"key1".to_string()).await.unwrap();
        assert!(!store.exists(&"key1".to_string()).await.unwrap());
    }

    #[tokio::test]
    async fn test_ttl_store() {
        let store = InMemoryStoreWithTTL::<String, String>::new(1); // 1 second TTL

        store
            .set("key1".to_string(), "value1".to_string())
            .await
            .unwrap();

        // Should exist immediately
        assert!(store.exists(&"key1".to_string()).await.unwrap());

        // Wait for expiration
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;

        // Should be expired now
        assert!(!store.exists(&"key1".to_string()).await.unwrap());
    }
}
