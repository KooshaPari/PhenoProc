//! Phenotype Errors - Domain-specific error types
//!
//! Provides concrete error implementations for phenotype services.

#![cfg_attr(docsrs, feature(doc_auto_cfg))]

use phenotype_error_core::{ErrorCode, PhenotypeError};
use phenotype_error_macros::PhenotypeError;
use serde::{Deserialize, Serialize};

/// API errors
#[derive(Debug, thiserror::Error, PhenotypeError)]
#[error_code = "API_ERROR"]
pub enum ApiError {
    #[error("Not found: {resource} with id {id}")]
    NotFound { resource: String, id: String },

    #[error("Validation failed: {message}")]
    ValidationFailed { message: String },

    #[error("Unauthorized: {reason}")]
    Unauthorized { reason: String },

    #[error("Forbidden: {resource}")]
    Forbidden { resource: String },

    #[error("Rate limited. Retry after {retry_after}s")]
    RateLimited { retry_after: u64 },

    #[error("Bad request: {message}")]
    BadRequest { message: String },

    #[error("Internal error: {message}")]
    InternalError { message: String },
}

/// Database errors
#[derive(Debug, thiserror::Error, PhenotypeError)]
#[error_code = "DB_ERROR"]
pub enum DatabaseError {
    #[error("Connection failed: {message}")]
    ConnectionFailed { message: String },

    #[error("Query failed: {message}")]
    QueryFailed { message: String },

    #[error("Unique constraint violation: {field}")]
    UniqueViolation { field: String },

    #[error("Foreign key violation: {constraint}")]
    ForeignKeyViolation { constraint: String },

    #[error("Record not found: {table} id {id}")]
    NotFound { table: String, id: String },

    #[error("Transaction failed: {message}")]
    TransactionFailed { message: String },
}

/// Cache errors
#[derive(Debug, thiserror::Error, PhenotypeError)]
#[error_code = "CACHE_ERROR"]
pub enum CacheError {
    #[error("Connection failed: {message}")]
    ConnectionFailed { message: String },

    #[error("Key not found: {key}")]
    KeyNotFound { key: String },

    #[error("Serialization failed: {message}")]
    SerializationFailed { message: String },

    #[error("Deserialization failed: {message}")]
    DeserializationFailed { message: String },
}

/// Authentication errors
#[derive(Debug, thiserror::Error, PhenotypeError)]
#[error_code = "AUTH_ERROR"]
pub enum AuthError {
    #[error("Invalid credentials")]
    InvalidCredentials,

    #[error("Token expired")]
    TokenExpired,

    #[error("Token invalid")]
    TokenInvalid,

    #[error("Session expired")]
    SessionExpired,

    #[error("Account locked")]
    AccountLocked,

    #[error("Account disabled")]
    AccountDisabled,

    #[error("MFA required")]
    MfaRequired,

    #[error("MFA failed")]
    MfaFailed,
}

/// Service errors
#[derive(Debug, thiserror::Error, PhenotypeError)]
#[error_code = "SERVICE_ERROR"]
pub enum ServiceError {
    #[error("Service unavailable: {service}")]
    Unavailable { service: String },

    #[error("Service timeout: {service}")]
    Timeout { service: String },

    #[error("Circuit breaker open: {service}")]
    CircuitBreakerOpen { service: String },

    #[error("Retry exhausted: {message}")]
    RetryExhausted { message: String },

    #[error("Dependency failed: {service} - {message}")]
    DependencyFailed { service: String, message: String },
}

/// Event errors
#[derive(Debug, thiserror::Error, PhenotypeError)]
#[error_code = "EVENT_ERROR"]
pub enum EventError {
    #[error("Publishing failed: {message}")]
    PublishFailed { message: String },

    #[error("Subscription failed: {message}")]
    SubscriptionFailed { message: String },

    #[error("Handler failed: {message}")]
    HandlerFailed { message: String },

    #[error("Serialization failed: {message}")]
    SerializationFailed { message: String },

    #[error("Event store failed: {message}")]
    EventStoreFailed { message: String },
}

/// File/storage errors
#[derive(Debug, thiserror::Error, PhenotypeError)]
#[error_code = "STORAGE_ERROR"]
pub enum StorageError {
    #[error("File not found: {path}")]
    FileNotFound { path: String },

    #[error("Permission denied: {path}")]
    PermissionDenied { path: String },

    #[error("Upload failed: {message}")]
    UploadFailed { message: String },

    #[error("Download failed: {message}")]
    DownloadFailed { message: String },

    #[error("Quota exceeded")]
    QuotaExceeded,

    #[error("Invalid file type: {mime_type}")]
    InvalidFileType { mime_type: String },
}

/// Validation error details
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationErrorDetail {
    pub field: String,
    pub message: String,
    pub code: String,
}

/// Error response for API
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorResponse {
    pub code: String,
    pub message: String,
    pub details: Option<serde_json::Value>,
    pub request_id: Option<String>,
}

impl ErrorResponse {
    pub fn new(code: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            code: code.into(),
            message: message.into(),
            details: None,
            request_id: None,
        }
    }

    pub fn with_details(mut self, details: impl Serialize) -> Result<Self, serde_json::Error> {
        self.details = Some(serde_json::to_value(details)?);
        Ok(self)
    }

    pub fn with_request_id(mut self, request_id: impl Into<String>) -> Self {
        self.request_id = Some(request_id.into());
        self
    }
}

/// Helper macro for creating errors
#[macro_export]
macro_rules! api_error {
    (not_found: $resource:expr, $id:expr) => {
        $crate::ApiError::NotFound {
            resource: $resource.to_string(),
            id: $id.to_string(),
        }
    };
    (validation: $message:expr) => {
        $crate::ApiError::ValidationFailed {
            message: $message.to_string(),
        }
    };
    (unauthorized: $reason:expr) => {
        $crate::ApiError::Unauthorized {
            reason: $reason.to_string(),
        }
    };
}

/// Convert errors to HTTP status codes
pub fn error_to_status_code<E: PhenotypeError>(error: &E) -> u16 {
    match error.code() {
        ErrorCode::NotFound => 404,
        ErrorCode::ValidationFailed => 400,
        ErrorCode::Unauthorized => 401,
        ErrorCode::Forbidden => 403,
        ErrorCode::Conflict => 409,
        ErrorCode::RateLimited => 429,
        ErrorCode::ServiceUnavailable => 503,
        ErrorCode::Internal => 500,
        _ => 500,
    }
}
