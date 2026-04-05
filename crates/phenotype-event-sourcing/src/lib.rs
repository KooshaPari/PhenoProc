//! # Phenotype Event Sourcing
//!
//! Event sourcing framework with aggregate roots, event stores, and projections.
//!
//! ## Features
//!
//! - Event store trait
//! - Aggregate roots
//! - Event streaming
//! - Snapshots for performance
//! - Projections for read models

use async_trait::async_trait;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use thiserror::Error;
use uuid::Uuid;

/// Event sourcing error types
#[derive(Error, Debug)]
pub enum EventSourcingError {
    #[error("Concurrency conflict: expected version {expected}, found {actual}")]
    ConcurrencyConflict { expected: i64, actual: i64 },
    #[error("Aggregate not found: {0}")]
    AggregateNotFound(String),
    #[error("Event store error: {0}")]
    StoreError(String),
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
    #[error("Invalid event sequence")]
    InvalidSequence,
}

/// Domain event trait
pub trait DomainEvent: Serialize + for<'de> Deserialize<'de> + Send + Sync + 'static {
    /// Event type identifier
    fn event_type(&self) -> &'static str;

    /// Get aggregate ID
    fn aggregate_id(&self) -> &str;

    /// Get event timestamp
    fn occurred_at(&self) -> DateTime<Utc>;
}

/// Event envelope for storage
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventEnvelope<E> {
    pub id: Uuid,
    pub aggregate_id: String,
    pub sequence: i64,
    pub event: E,
    pub metadata: HashMap<String, String>,
    pub occurred_at: DateTime<Utc>,
    pub correlation_id: Option<String>,
}

impl<E: DomainEvent> EventEnvelope<E> {
    /// Create new event envelope
    pub fn new(
        aggregate_id: impl Into<String>,
        sequence: i64,
        event: E,
        metadata: HashMap<String, String>,
    ) -> Self {
        Self {
            id: Uuid::new_v4(),
            aggregate_id: aggregate_id.into(),
            sequence,
            event,
            metadata,
            occurred_at: Utc::now(),
            correlation_id: None,
        }
    }

    /// Add correlation ID
    pub fn with_correlation(mut self, id: impl Into<String>) -> Self {
        self.correlation_id = Some(id.into());
        self
    }
}

/// Event store trait
#[async_trait]
pub trait EventStore<E: DomainEvent>: Send + Sync {
    /// Error type
    type Error: std::error::Error + Send + Sync;

    /// Append events to an aggregate
    async fn append(
        &self,
        aggregate_id: &str,
        expected_version: i64,
        events: Vec<E>,
    ) -> Result<Vec<EventEnvelope<E>>, Self::Error>;

    /// Read events for an aggregate
    async fn read(&self, aggregate_id: &str) -> Result<Vec<EventEnvelope<E>>, Self::Error>;

    /// Read events from a specific sequence
    async fn read_from(
        &self,
        aggregate_id: &str,
        from_sequence: i64,
    ) -> Result<Vec<EventEnvelope<E>>, Self::Error>;

    /// Get current version for aggregate
    async fn current_version(&self, aggregate_id: &str) -> Result<i64, Self::Error>;

    /// Stream all events
    async fn stream_all(
        &self,
        from_position: i64,
        batch_size: usize,
    ) -> Result<Vec<EventEnvelope<E>>, Self::Error>;
}

/// Aggregate root trait
#[async_trait]
pub trait Aggregate: Send + Sync + Default {
    /// Aggregate ID type
    type Id: Into<String> + Clone + Send + Sync;

    /// Event type
    type Event: DomainEvent + Clone;

    /// Error type
    type Error: std::error::Error + Send + Sync;

    /// Get aggregate ID
    fn id(&self) -> &Self::Id;

    /// Get current version
    fn version(&self) -> i64;

    /// Apply event to mutate state
    fn apply(&mut self, event: &Self::Event);

    /// Apply event envelope (with sequence tracking)
    fn apply_envelope(&mut self, envelope: &EventEnvelope<Self::Event>) {
        self.apply(&envelope.event);
    }

    /// Load from events
    fn load(&mut self, events: &[EventEnvelope<Self::Event>]) {
        for envelope in events {
            self.apply_envelope(envelope);
        }
    }

    /// Get uncommitted changes
    fn uncommitted(&self) -> &[Self::Event];

    /// Clear uncommitted changes
    fn clear_uncommitted(&mut self);

    /// Commit changes (called after successful persistence)
    fn commit(&mut self) {
        self.clear_uncommitted();
    }
}

/// Repository for aggregates
pub struct AggregateRepository<A: Aggregate> {
    store: Box<dyn EventStore<A::Event, Error = EventSourcingError>>,
    _phantom: std::marker::PhantomData<A>,
}

impl<A: Aggregate> AggregateRepository<A> {
    /// Create new repository
    pub fn new(store: Box<dyn EventStore<A::Event, Error = EventSourcingError>>) -> Self {
        Self {
            store,
            _phantom: std::marker::PhantomData,
        }
    }

    /// Load aggregate by ID
    pub async fn load(&self, id: &A::Id) -> Result<A, EventSourcingError> {
        let id_str: String = id.clone().into();
        let events = self.store.read(&id_str).await?;

        let mut aggregate = A::default();
        aggregate.load(&events);

        Ok(aggregate)
    }

    /// Save aggregate changes
    pub async fn save(&self, aggregate: &mut A) -> Result<(), EventSourcingError> {
        let id_str: String = aggregate.id().clone().into();
        let version = aggregate.version();
        let events: Vec<A::Event> = aggregate.uncommitted().to_vec();

        if events.is_empty() {
            return Ok(());
        }

        self.store.append(&id_str, version, events).await?;

        aggregate.commit();
        Ok(())
    }
}

/// Snapshot for performance
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Snapshot<A> {
    pub aggregate_id: String,
    pub version: i64,
    pub state: A,
    pub created_at: DateTime<Utc>,
}

/// Snapshot store trait
#[async_trait]
pub trait SnapshotStore<A>: Send + Sync {
    /// Error type
    type Error: std::error::Error + Send + Sync;

    /// Save snapshot
    async fn save(&self, snapshot: &Snapshot<A>) -> Result<(), Self::Error>;

    /// Load snapshot
    async fn load(&self, aggregate_id: &str) -> Result<Option<Snapshot<A>>, Self::Error>;

    /// Delete old snapshots
    async fn delete_before(&self, aggregate_id: &str, version: i64) -> Result<(), Self::Error>;
}

/// Projection trait for read models
#[async_trait]
pub trait Projection<E: DomainEvent>: Send + Sync {
    /// Error type
    type Error: std::error::Error + Send + Sync;

    /// Project an event
    async fn project(&mut self, event: &EventEnvelope<E>) -> Result<(), Self::Error>;

    /// Reset projection (rebuild from scratch)
    async fn reset(&mut self) -> Result<(), Self::Error>;
}

/// Event bus for publishing events
#[async_trait]
pub trait EventBus<E: DomainEvent>: Send + Sync {
    /// Error type
    type Error: std::error::Error + Send + Sync;

    /// Publish event
    async fn publish(&self, event: &EventEnvelope<E>) -> Result<(), Self::Error>;

    /// Subscribe to events
    async fn subscribe<F>(&self, handler: F) -> Result<(), Self::Error>
    where
        F: Fn(&EventEnvelope<E>) + Send + Sync;
}

/// In-memory event store for testing
pub struct InMemoryEventStore<E: DomainEvent> {
    events: std::sync::Mutex<HashMap<String, Vec<EventEnvelope<E>>>>,
    all_events: std::sync::Mutex<Vec<EventEnvelope<E>>>,
}

impl<E: DomainEvent> Default for InMemoryEventStore<E> {
    fn default() -> Self {
        Self {
            events: std::sync::Mutex::new(HashMap::new()),
            all_events: std::sync::Mutex::new(Vec::new()),
        }
    }
}

impl<E: DomainEvent> InMemoryEventStore<E> {
    /// Create new in-memory store
    pub fn new() -> Self {
        Self::default()
    }
}

#[async_trait]
impl<E: DomainEvent + Clone> EventStore<E> for InMemoryEventStore<E> {
    type Error = EventSourcingError;

    async fn append(
        &self,
        aggregate_id: &str,
        expected_version: i64,
        events: Vec<E>,
    ) -> Result<Vec<EventEnvelope<E>>, Self::Error> {
        let mut store = self.events.lock().unwrap();
        let existing = store.get(aggregate_id).cloned().unwrap_or_default();
        let actual_version = existing.len() as i64;

        if actual_version != expected_version {
            return Err(EventSourcingError::ConcurrencyConflict {
                expected: expected_version,
                actual: actual_version,
            });
        }

        let mut envelopes = Vec::new();
        for (i, event) in events.into_iter().enumerate() {
            let envelope = EventEnvelope::new(
                aggregate_id,
                expected_version + i as i64 + 1,
                event,
                HashMap::new(),
            );
            envelopes.push(envelope);
        }

        store
            .entry(aggregate_id.to_string())
            .or_default()
            .extend(envelopes.clone());

        self.all_events.lock().unwrap().extend(envelopes.clone());

        Ok(envelopes)
    }

    async fn read(&self, aggregate_id: &str) -> Result<Vec<EventEnvelope<E>>, Self::Error> {
        let store = self.events.lock().unwrap();
        Ok(store.get(aggregate_id).cloned().unwrap_or_default())
    }

    async fn read_from(
        &self,
        aggregate_id: &str,
        from_sequence: i64,
    ) -> Result<Vec<EventEnvelope<E>>, Self::Error> {
        let events = self.read(aggregate_id).await?;
        Ok(events
            .into_iter()
            .filter(|e| e.sequence >= from_sequence)
            .collect())
    }

    async fn current_version(&self, aggregate_id: &str) -> Result<i64, Self::Error> {
        let store = self.events.lock().unwrap();
        Ok(store.get(aggregate_id).map(|e| e.len() as i64).unwrap_or(0))
    }

    async fn stream_all(
        &self,
        from_position: i64,
        batch_size: usize,
    ) -> Result<Vec<EventEnvelope<E>>, Self::Error> {
        let all = self.all_events.lock().unwrap();
        Ok(all
            .iter()
            .skip(from_position as usize)
            .take(batch_size)
            .cloned()
            .collect())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Debug, Clone, Serialize, Deserialize)]
    enum TestEvent {
        Created { id: String, name: String },
        Updated { name: String },
    }

    impl DomainEvent for TestEvent {
        fn event_type(&self) -> &'static str {
            match self {
                TestEvent::Created { .. } => "created",
                TestEvent::Updated { .. } => "updated",
            }
        }

        fn aggregate_id(&self) -> &str {
            match self {
                TestEvent::Created { id, .. } => id,
                TestEvent::Updated { .. } => "test",
            }
        }

        fn occurred_at(&self) -> DateTime<Utc> {
            Utc::now()
        }
    }

    #[test]
    fn test_in_memory_event_store() {
        let store = InMemoryEventStore::<TestEvent>::new();

        let events = vec![
            TestEvent::Created {
                id: "agg-1".to_string(),
                name: "Test".to_string(),
            },
            TestEvent::Updated {
                name: "Updated".to_string(),
            },
        ];

        let envelopes =
            futures::executor::block_on(async { store.append("agg-1", 0, events).await.unwrap() });

        assert_eq!(envelopes.len(), 2);
        assert_eq!(envelopes[0].sequence, 1);
        assert_eq!(envelopes[1].sequence, 2);
    }

    #[test]
    fn test_concurrency_conflict() {
        let store = InMemoryEventStore::<TestEvent>::new();

        let event = TestEvent::Created {
            id: "agg-1".to_string(),
            name: "Test".to_string(),
        };

        futures::executor::block_on(async {
            store.append("agg-1", 0, vec![event.clone()]).await.unwrap();

            // Should fail with wrong version
            let result = store.append("agg-1", 0, vec![event]).await;
            assert!(matches!(
                result,
                Err(EventSourcingError::ConcurrencyConflict { .. })
            ));
        });
    }
}
