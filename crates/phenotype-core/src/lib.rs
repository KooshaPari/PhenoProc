//! Phenotype Core - Core types and utilities
//!
//! Provides fundamental types used across the phenotype ecosystem.

#![cfg_attr(docsrs, feature(doc_auto_cfg))]

use std::collections::HashMap;

use chrono::{DateTime, Utc};
use phenotype_contracts::{Contract, Event};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Entity ID wrapper with type safety
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct EntityId<T> {
    id: Uuid,
    _phantom: std::marker::PhantomData<T>,
}

impl<T> EntityId<T> {
    pub fn new() -> Self {
        Self {
            id: Uuid::new_v4(),
            _phantom: std::marker::PhantomData,
        }
    }

    pub fn parse(s: &str) -> Option<Self> {
        Uuid::parse_str(s).ok().map(|id| Self {
            id,
            _phantom: std::marker::PhantomData,
        })
    }

    pub fn as_uuid(&self) -> Uuid {
        self.id
    }

    pub fn to_string(&self) -> String {
        self.id.to_string()
    }
}

impl<T> Default for EntityId<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T> std::fmt::Display for EntityId<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.id)
    }
}

/// Domain event base implementation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DomainEvent {
    pub id: Uuid,
    pub event_type: String,
    pub aggregate_id: String,
    pub aggregate_type: String,
    pub sequence: u64,
    pub payload: serde_json::Value,
    pub metadata: HashMap<String, String>,
    pub timestamp: DateTime<Utc>,
}

impl DomainEvent {
    pub fn new(
        event_type: impl Into<String>,
        aggregate_id: impl Into<String>,
        aggregate_type: impl Into<String>,
    ) -> Self {
        Self {
            id: Uuid::new_v4(),
            event_type: event_type.into(),
            aggregate_id: aggregate_id.into(),
            aggregate_type: aggregate_type.into(),
            sequence: 0,
            payload: serde_json::Value::Null,
            metadata: HashMap::new(),
            timestamp: Utc::now(),
        }
    }

    pub fn with_payload<T: Serialize>(mut self, payload: T) -> Result<Self, serde_json::Error> {
        self.payload = serde_json::to_value(payload)?;
        Ok(self)
    }

    pub fn with_metadata(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.metadata.insert(key.into(), value.into());
        self
    }
}

impl Contract for DomainEvent {
    fn contract_type(&self) -> &'static str {
        "domain_event"
    }

    fn timestamp(&self) -> DateTime<Utc> {
        self.timestamp
    }

    fn correlation_id(&self) -> Uuid {
        self.id
    }

    fn as_any(&self) -> &dyn std::any::Any {
        self
    }
}

impl Event for DomainEvent {
    fn aggregate_id(&self) -> &str {
        &self.aggregate_id
    }

    fn sequence(&self) -> u64 {
        self.sequence
    }
}

/// Pagination parameters
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Pagination {
    pub page: u32,
    pub per_page: u32,
}

impl Default for Pagination {
    fn default() -> Self {
        Self {
            page: 1,
            per_page: 20,
        }
    }
}

impl Pagination {
    pub fn offset(&self) -> usize {
        ((self.page - 1) * self.per_page) as usize
    }

    pub fn limit(&self) -> usize {
        self.per_page as usize
    }
}

/// Paginated result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Paginated<T> {
    pub items: Vec<T>,
    pub total: u64,
    pub page: u32,
    pub per_page: u32,
    pub total_pages: u32,
}

impl<T> Paginated<T> {
    pub fn new(items: Vec<T>, total: u64, pagination: Pagination) -> Self {
        let total_pages =
            ((total + pagination.per_page as u64 - 1) / pagination.per_page as u64) as u32;
        Self {
            items,
            total,
            page: pagination.page,
            per_page: pagination.per_page,
            total_pages,
        }
    }
}

/// Sort direction
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SortDirection {
    Asc,
    Desc,
}

impl Default for SortDirection {
    fn default() -> Self {
        SortDirection::Asc
    }
}

/// Sort specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Sort {
    pub field: String,
    pub direction: SortDirection,
}

/// Filter operator
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "op")]
pub enum FilterOp {
    Eq {
        field: String,
        value: serde_json::Value,
    },
    Ne {
        field: String,
        value: serde_json::Value,
    },
    Gt {
        field: String,
        value: serde_json::Value,
    },
    Gte {
        field: String,
        value: serde_json::Value,
    },
    Lt {
        field: String,
        value: serde_json::Value,
    },
    Lte {
        field: String,
        value: serde_json::Value,
    },
    In {
        field: String,
        values: Vec<serde_json::Value>,
    },
    Like {
        field: String,
        pattern: String,
    },
    IsNull {
        field: String,
    },
    IsNotNull {
        field: String,
    },
}

/// Query parameters
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct QueryParams {
    pub pagination: Pagination,
    pub sort: Vec<Sort>,
    pub filters: Vec<FilterOp>,
    pub search: Option<String>,
}

/// Versioned entity
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Versioned<T> {
    pub data: T,
    pub version: u64,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl<T> Versioned<T> {
    pub fn new(data: T) -> Self {
        let now = Utc::now();
        Self {
            data,
            version: 1,
            created_at: now,
            updated_at: now,
        }
    }

    pub fn increment_version(&mut self) {
        self.version += 1;
        self.updated_at = Utc::now();
    }
}

/// Money type for financial calculations
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Money {
    pub amount: i64, // Amount in smallest currency unit (cents)
    pub currency: String,
}

impl Money {
    pub fn new(amount: i64, currency: impl Into<String>) -> Self {
        Self {
            amount,
            currency: currency.into(),
        }
    }

    pub fn from_major(major: f64, currency: impl Into<String>) -> Self {
        Self {
            amount: (major * 100.0) as i64,
            currency: currency.into(),
        }
    }

    pub fn to_major(&self) -> f64 {
        self.amount as f64 / 100.0
    }
}

impl std::fmt::Display for Money {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{} {}", self.to_major(), self.currency)
    }
}
