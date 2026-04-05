//! # Phenotype Infrastructure
//!
//! Infrastructure traits and abstractions for ports/adapters pattern.
//!
//! ## Features
//!
//! - Repository trait for data access
//! - Cache trait for caching abstractions  
//! - Event bus trait for pub/sub
//! - Storage trait for file/object storage
//!
//! ## Example
//!
//! ```ignore
//! use phenotype_infrastructure::{Repository, Cache};
//! use async_trait::async_trait;
//!
//! struct User {
//!     id: String,
//!     name: String,
//! }
//!
//! struct MyUserRepo;
//!
//! #[async_trait]
//! impl Repository<User> for MyUserRepo {
//!     type Error = std::io::Error;
//!     
//!     async fn find_by_id(&self, id: &str) -> Result<Option<User>, Self::Error> {
//!         // Implementation
//!         Ok(None)
//!     }
//!     
//!     async fn find_all(&self) -> Result<Vec<User>, Self::Error> {
//!         Ok(vec![])
//!     }
//!     
//!     async fn save(&self, _entity: &User) -> Result<(), Self::Error> {
//!         Ok(())
//!     }
//!     
//!     async fn delete(&self, _id: &str) -> Result<(), Self::Error> {
//!         Ok(())
//!     }
//! }
//! ```

use async_trait::async_trait;
use std::error::Error;

/// Core repository trait for data access
#[async_trait]
pub trait Repository<T>: Send + Sync {
    /// Error type for operations
    type Error: Error + Send + Sync;

    /// Find entity by ID
    async fn find_by_id(&self, id: &str) -> Result<Option<T>, Self::Error>;

    /// Find all entities
    async fn find_all(&self) -> Result<Vec<T>, Self::Error>;

    /// Save entity
    async fn save(&self, entity: &T) -> Result<(), Self::Error>;

    /// Delete entity by ID
    async fn delete(&self, id: &str) -> Result<(), Self::Error>;
}

/// Cache trait for key-value storage
#[async_trait]
pub trait Cache: Send + Sync {
    /// Error type for operations
    type Error: Error + Send + Sync;

    /// Get value by key
    async fn get(&self, key: &str) -> Result<Option<Vec<u8>>, Self::Error>;

    /// Set value with optional TTL
    async fn set(
        &self,
        key: &str,
        value: &[u8],
        ttl: Option<std::time::Duration>,
    ) -> Result<(), Self::Error>;

    /// Delete key
    async fn delete(&self, key: &str) -> Result<(), Self::Error>;

    /// Check if key exists
    async fn exists(&self, key: &str) -> Result<bool, Self::Error>;

    /// Clear all cached data
    async fn clear(&self) -> Result<(), Self::Error>;
}

/// Event bus trait for pub/sub messaging
#[async_trait]
pub trait EventBus: Send + Sync {
    /// Error type for operations
    type Error: Error + Send + Sync;

    /// Publish event to a topic
    async fn publish(&self, topic: &str, event: &[u8]) -> Result<(), Self::Error>;

    /// Subscribe to a topic
    async fn subscribe(
        &self,
        topic: &str,
        handler: Box<dyn Fn(Vec<u8>) + Send + Sync>,
    ) -> Result<(), Self::Error>;
}

/// Storage trait for file/object storage
#[async_trait]
pub trait Storage: Send + Sync {
    /// Error type for operations
    type Error: Error + Send + Sync;

    /// Upload object
    async fn upload(&self, key: &str, data: &[u8]) -> Result<(), Self::Error>;

    /// Download object
    async fn download(&self, key: &str) -> Result<Option<Vec<u8>>, Self::Error>;

    /// Delete object
    async fn delete(&self, key: &str) -> Result<(), Self::Error>;

    /// List objects with prefix
    async fn list(&self, prefix: &str) -> Result<Vec<String>, Self::Error>;

    /// Check if object exists
    async fn exists(&self, key: &str) -> Result<bool, Self::Error>;

    /// Get object URL
    async fn get_url(&self, key: &str, expiry: std::time::Duration) -> Result<String, Self::Error>;
}

/// Database transaction trait
#[async_trait]
pub trait Transaction: Send + Sync {
    /// Error type for operations
    type Error: Error + Send + Sync;

    /// Commit the transaction
    async fn commit(self) -> Result<(), Self::Error>;

    /// Rollback the transaction
    async fn rollback(self) -> Result<(), Self::Error>;
}

/// Unit of work pattern for transactional operations
#[async_trait]
pub trait UnitOfWork: Send + Sync {
    /// Error type for operations
    type Error: Error + Send + Sync;

    /// Transaction type
    type Transaction: Transaction;

    /// Begin a transaction
    async fn begin(&self) -> Result<Self::Transaction, Self::Error>;

    /// Execute function within a transaction
    async fn with_transaction<F, Fut, R>(&self, f: F) -> Result<R, Self::Error>
    where
        F: FnOnce(Self::Transaction) -> Fut + Send,
        Fut: std::future::Future<Output = Result<R, Self::Error>> + Send;
}

/// Search repository trait for full-text search
#[async_trait]
pub trait SearchRepository<T>: Send + Sync {
    /// Error type for operations
    type Error: Error + Send + Sync;

    /// Search with query
    async fn search(&self, query: &str) -> Result<Vec<T>, Self::Error>;

    /// Index entity
    async fn index(&self, entity: &T) -> Result<(), Self::Error>;

    /// Remove from index
    async fn remove_from_index(&self, id: &str) -> Result<(), Self::Error>;
}

/// Health check trait for infrastructure components
#[async_trait]
pub trait HealthCheck: Send + Sync {
    /// Error type for operations
    type Error: Error + Send + Sync;

    /// Check health status
    async fn check(&self) -> Result<HealthStatus, Self::Error>;
}

/// Health status enum
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HealthStatus {
    /// Component is healthy
    Healthy,
    /// Component is degraded but functioning
    Degraded,
    /// Component is unavailable
    Unavailable,
}

impl HealthStatus {
    /// Check if status is healthy
    pub fn is_healthy(&self) -> bool {
        matches!(self, HealthStatus::Healthy)
    }

    /// Check if status is degraded
    pub fn is_degraded(&self) -> bool {
        matches!(self, HealthStatus::Degraded)
    }

    /// Check if status is available (healthy or degraded)
    pub fn is_available(&self) -> bool {
        matches!(self, HealthStatus::Healthy | HealthStatus::Degraded)
    }
}

/// Circuit breaker trait for resilient operations
pub trait CircuitBreaker: Send + Sync {
    /// Check if circuit is closed (allowing requests)
    fn is_closed(&self) -> bool;

    /// Check if circuit is open (blocking requests)
    fn is_open(&self) -> bool;

    /// Record a success
    fn record_success(&mut self);

    /// Record a failure
    fn record_failure(&mut self);
}

#[cfg(test)]
mod tests {
    use super::*;

    struct MockRepo;
    struct MockEntity;

    #[async_trait]
    impl Repository<MockEntity> for MockRepo {
        type Error = std::io::Error;

        async fn find_by_id(&self, _id: &str) -> Result<Option<MockEntity>, Self::Error> {
            Ok(Some(MockEntity))
        }

        async fn find_all(&self) -> Result<Vec<MockEntity>, Self::Error> {
            Ok(vec![MockEntity])
        }

        async fn save(&self, _entity: &MockEntity) -> Result<(), Self::Error> {
            Ok(())
        }

        async fn delete(&self, _id: &str) -> Result<(), Self::Error> {
            Ok(())
        }
    }

    #[test]
    fn test_health_status() {
        assert!(HealthStatus::Healthy.is_healthy());
        assert!(!HealthStatus::Degraded.is_healthy());
        assert!(!HealthStatus::Unavailable.is_healthy());

        assert!(HealthStatus::Healthy.is_available());
        assert!(HealthStatus::Degraded.is_available());
        assert!(!HealthStatus::Unavailable.is_available());
    }
}
