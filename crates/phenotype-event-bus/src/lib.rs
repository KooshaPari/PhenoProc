//! Phenotype Event Bus - Async event publishing and subscription
//!
//! Provides an in-memory and pluggable event bus for decoupled communication.

#![cfg_attr(docsrs, feature(doc_auto_cfg))]

use std::any::{Any, TypeId};
use std::collections::HashMap;
use std::sync::Arc;

use async_trait::async_trait;
use dashmap::DashMap;
use serde::{de::DeserializeOwned, Serialize};
use tokio::sync::{broadcast, mpsc};
use tracing::debug;
use uuid::Uuid;

/// Event trait for all bus events
pub trait Event: Send + Sync + Serialize + 'static {
    fn event_type(&self) -> &'static str;
    fn event_id(&self) -> Uuid;
    fn timestamp(&self) -> chrono::DateTime<chrono::Utc>;
    fn as_any(&self) -> &dyn Any;
}

/// Event envelope for transport
#[derive(Debug, Clone)]
pub struct EventEnvelope {
    pub id: Uuid,
    pub event_type: String,
    pub payload: serde_json::Value,
    pub metadata: HashMap<String, String>,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

/// Event bus trait
#[async_trait]
pub trait EventBus: Send + Sync + 'static {
    async fn publish<E: Event + Serialize + DeserializeOwned>(
        &self,
        event: E,
    ) -> Result<(), EventBusError>;

    /// Subscribe to events of a specific type
    async fn subscribe<E: Event + DeserializeOwned>(
        &self,
    ) -> Result<mpsc::Receiver<E>, EventBusError>;

    /// Subscribe to all events
    fn subscribe_all(&self) -> Result<broadcast::Receiver<EventEnvelope>, EventBusError>;
}

/// Event bus error types
#[derive(Debug, thiserror::Error)]
pub enum EventBusError {
    #[error("Failed to publish event: {0}")]
    PublishFailed(String),

    #[error("Failed to subscribe: {0}")]
    SubscribeFailed(String),

    #[error("Event type not registered: {0}")]
    UnknownEventType(String),

    #[error("Event bus is closed")]
    BusClosed,
}

/// In-memory event bus implementation
pub struct InMemoryEventBus {
    channels: DashMap<TypeId, Box<dyn Any + Send + Sync>>,
    broadcast_tx: broadcast::Sender<EventEnvelope>,
    _broadcast_rx: Arc<broadcast::Receiver<EventEnvelope>>,
}

impl InMemoryEventBus {
    pub fn new(capacity: usize) -> Self {
        let (tx, rx) = broadcast::channel(capacity);
        Self {
            channels: DashMap::new(),
            broadcast_tx: tx,
            _broadcast_rx: Arc::new(rx),
        }
    }

    pub fn default() -> Self {
        Self::new(1000)
    }
}

impl Default for InMemoryEventBus {
    fn default() -> Self {
        Self::new(1000)
    }
}

#[async_trait]
impl EventBus for InMemoryEventBus {
    async fn publish<E: Event>(&self, event: E) -> Result<(), EventBusError> {
        let envelope = EventEnvelope {
            id: event.event_id(),
            event_type: event.event_type().to_string(),
            payload: serde_json::to_value(&event)
                .map_err(|e| EventBusError::PublishFailed(e.to_string()))?,
            metadata: HashMap::new(),
            timestamp: event.timestamp(),
        };

        // Send to broadcast channel
        let _ = self.broadcast_tx.send(envelope.clone());

        debug!("Published event: {}", envelope.event_type);
        Ok(())
    }

    async fn subscribe<E: Event>(&self) -> Result<mpsc::Receiver<E>, EventBusError> {
        let (tx, rx) = mpsc::channel(100);
        let type_id = TypeId::of::<E>();

        // Store the sender for this type
        self.channels
            .insert(type_id, Box::new(tx) as Box<dyn Any + Send + Sync>);

        Ok(rx)
    }

    fn subscribe_all(&self) -> Result<broadcast::Receiver<EventEnvelope>, EventBusError> {
        Ok(self.broadcast_tx.subscribe())
    }
}

/// Event handler trait
#[async_trait]
pub trait EventHandler<E: Event>: Send + Sync {
    async fn handle(&self, event: E) -> Result<(), EventBusError>;
}

/// Event bus builder
pub struct EventBusBuilder {
    capacity: usize,
    enable_persistence: bool,
}

impl EventBusBuilder {
    pub fn new() -> Self {
        Self {
            capacity: 1000,
            enable_persistence: false,
        }
    }

    pub fn with_capacity(mut self, capacity: usize) -> Self {
        self.capacity = capacity;
        self
    }

    pub fn with_persistence(mut self, enabled: bool) -> Self {
        self.enable_persistence = enabled;
        self
    }

    pub fn build(self) -> Arc<InMemoryEventBus> {
        Arc::new(InMemoryEventBus::new(self.capacity))
    }
}

impl Default for EventBusBuilder {
    fn default() -> Self {
        Self::new()
    }
}

/// Event stream for reactive processing
pub struct EventStream {
    receiver: broadcast::Receiver<EventEnvelope>,
}

impl EventStream {
    pub async fn next(&mut self) -> Option<EventEnvelope> {
        self.receiver.recv().await.ok()
    }

    pub fn filter<F>(self, predicate: F) -> FilteredStream<F>
    where
        F: Fn(&EventEnvelope) -> bool,
    {
        FilteredStream {
            inner: self,
            predicate,
        }
    }
}

/// Filtered event stream
pub struct FilteredStream<F> {
    inner: EventStream,
    predicate: F,
}

impl<F: Fn(&EventEnvelope) -> bool> FilteredStream<F> {
    pub async fn next(&mut self) -> Option<EventEnvelope> {
        loop {
            match self.inner.next().await {
                Some(event) if (self.predicate)(&event) => return Some(event),
                Some(_) => continue,
                None => return None,
            }
        }
    }
}
