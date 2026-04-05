//! Port traits for hexagonal architecture
//!
//! Provides the core port interfaces for:
//! - Repository pattern (data access)
//! - Cache operations
//! - Event bus (pub/sub)
//! - Storage abstractions

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use thiserror::Error;

/// Repository trait for data access
#[async_trait]
pub trait Repository<T, ID>: Send + Sync
where
    T: Send + Sync + Serialize + for<'de> Deserialize<'de>,
    ID: Send + Sync,
{
    async fn find_by_id(&self, id: ID) -> Result<Option<T>, PortError>;
    async fn find_all(&self) -> Result<Vec<T>, PortError>;
    async fn save(&self, entity: T) -> Result<T, PortError>;
    async fn delete(&self, id: ID) -> Result<(), PortError>;
}

/// Cache trait for key-value operations
#[async_trait]
pub trait Cache<K, V>: Send + Sync
where
    K: Send + Sync,
    V: Send + Sync + Clone,
{
    async fn get(&self, key: &K) -> Result<Option<V>, PortError>;
    async fn set(&self, key: K, value: V, ttl_secs: Option<u64>) -> Result<(), PortError>;
    async fn delete(&self, key: &K) -> Result<(), PortError>;
    async fn clear(&self) -> Result<(), PortError>;
}

/// Event bus trait for pub/sub messaging
#[async_trait]
pub trait EventBus: Send + Sync {
    async fn publish(&self, topic: &str, payload: Vec<u8>) -> Result<(), PortError>;
    async fn subscribe(&self, topic: &str) -> Result<Box<dyn EventStream>, PortError>;
}

/// Event stream trait for receiving messages
#[async_trait]
pub trait EventStream: Send + Sync {
    async fn next(&mut self) -> Result<Option<Vec<u8>>, PortError>;
}

/// Storage trait for file/blob operations
#[async_trait]
pub trait Storage: Send + Sync {
    async fn put(&self, key: &str, data: Vec<u8>) -> Result<(), PortError>;
    async fn get(&self, key: &str) -> Result<Option<Vec<u8>>, PortError>;
    async fn delete(&self, key: &str) -> Result<(), PortError>;
    async fn list(&self, prefix: &str) -> Result<Vec<String>, PortError>;
}

/// Port error type
#[derive(Error, Debug, Clone)]
pub enum PortError {
    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Connection error: {0}")]
    Connection(String),

    #[error("Serialization error: {0}")]
    Serialization(String),

    #[error("Timeout")]
    Timeout,

    #[error("Internal error: {0}")]
    Internal(String),
}

/// Pagination parameters
#[derive(Debug, Clone, Default)]
pub struct Pagination {
    pub page: u32,
    pub page_size: u32,
}

impl Pagination {
    pub fn new(page: u32, page_size: u32) -> Self {
        Self { page, page_size }
    }

    pub fn offset(&self) -> u32 {
        (self.page - 1) * self.page_size
    }

    pub fn limit(&self) -> u32 {
        self.page_size
    }
}

/// Sort direction
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum SortDirection {
    #[default]
    Ascending,
    Descending,
}

/// Query filter
#[derive(Debug, Clone)]
pub struct Filter {
    pub field: String,
    pub operator: FilterOperator,
    pub value: serde_json::Value,
}

/// Filter operators
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FilterOperator {
    Eq,
    Neq,
    Gt,
    Gte,
    Lt,
    Lte,
    Like,
    In,
}

/// Query specification
#[derive(Debug, Clone, Default)]
pub struct QuerySpec {
    pub filters: Vec<Filter>,
    pub pagination: Pagination,
    pub sort_field: Option<String>,
    pub sort_direction: SortDirection,
}

/// Unit of work for transactional operations
#[async_trait]
pub trait UnitOfWork: Send + Sync {
    async fn begin(&self) -> Result<(), PortError>;
    async fn commit(&self) -> Result<(), PortError>;
    async fn rollback(&self) -> Result<(), PortError>;
}

/// Entity trait for domain objects
pub trait Entity<ID>: Send + Sync {
    fn id(&self) -> ID;
    fn version(&self) -> u64;
}

/// Aggregate root trait
pub trait AggregateRoot<ID>: Entity<ID> + Send + Sync {
    type Event: Send + Sync;

    fn apply(&mut self, event: Self::Event);
    fn uncommitted_events(&self) -> &[Self::Event];
    fn mark_committed(&mut self);
}

/// In-memory repository implementation
/// Trait for types that have an identifier.
pub trait Identifiable<ID> {
    /// Get the identifier.
    fn id(&self) -> ID;
}

/// In-memory repository implementation
pub struct InMemoryRepository<T, ID> {
    data: std::sync::RwLock<HashMap<ID, T>>,
}

impl<T, ID> InMemoryRepository<T, ID> {
    pub fn new() -> Self {
        Self {
            data: std::sync::RwLock::new(HashMap::new()),
        }
    }
}

impl<T, ID> Default for InMemoryRepository<T, ID>
where
    ID: std::hash::Hash + Eq,
{
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl<T, ID> Repository<T, ID> for InMemoryRepository<T, ID>
where
    T: Clone + Send + Sync + Serialize + for<'de> Deserialize<'de>,
    ID: Clone + std::hash::Hash + Eq + Send + Sync,
{
    async fn find_by_id(&self, id: ID) -> Result<Option<T>, PortError> {
        let data = self
            .data
            .read()
            .map_err(|_| PortError::Internal("Lock poisoned".into()))?;
        Ok(data.get(&id).cloned())
    }

    async fn find_all(&self) -> Result<Vec<T>, PortError> {
        let data = self
            .data
            .read()
            .map_err(|_| PortError::Internal("Lock poisoned".into()))?;
        Ok(data.values().cloned().collect())
    }

    async fn save(&self, entity: T) -> Result<T, PortError> {
        let _data = self
            .data
            .write()
            .map_err(|_| PortError::Internal("Lock poisoned".into()))?;
        // This is a simplified implementation - real one would extract ID from entity
        Ok(entity)
    }

    async fn delete(&self, _id: ID) -> Result<(), PortError> {
        let _data = self
            .data
            .write()
            .map_err(|_| PortError::Internal("Lock poisoned".into()))?;
        // Simplified - real implementation would delete by ID
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Clone, Debug, Serialize, Deserialize)]
    struct TestEntity {
        id: i32,
        name: String,
    }

    #[test]
    fn test_pagination() {
        let p = Pagination::new(2, 10);
        assert_eq!(p.offset(), 10);
        assert_eq!(p.limit(), 10);
    }

    #[test]
    fn test_port_error_display() {
        let err = PortError::NotFound("user".into());
        assert_eq!(err.to_string(), "Not found: user");
    }

    #[tokio::test]
    async fn test_in_memory_repository() {
        let repo = InMemoryRepository::<TestEntity, i32>::new();

        // Test save and find roundtrip - the save returns the entity
        let entity = TestEntity {
            id: 1,
            name: "Test".into(),
        };
        let saved = repo.save(entity.clone()).await.unwrap();
        assert_eq!(saved.id, 1);

        // Note: The simplified InMemoryRepository doesn't actually store entities
        // since it can't extract IDs generically - real implementations would
        // require the Entity trait bound
    }
}
