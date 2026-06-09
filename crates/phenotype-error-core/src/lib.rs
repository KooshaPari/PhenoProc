//! Error core types for Phenotype

use thiserror::Error;

/// Core error type for Phenotype
#[derive(Error, Debug, Clone)]
pub enum PhenotypeError {
    /// Configuration error
    #[error("Configuration error: {0}")]
    Config(String),
    /// IO error
    #[error("IO error: {0}")]
    Io(String),
    /// Validation error
    #[error("Validation error: {0}")]
    Validation(String),
    /// Unknown error
    #[error("Unknown error: {0}")]
    Unknown(String),
}

/// API error type
#[derive(Error, Debug, Clone)]
pub enum ApiError {
    #[error("Not found: {resource} (id: {id})")]
    NotFound { resource: String, id: String },
    #[error("Validation error: {0}")]
    Validation(String),
    #[error("API error: {0}")]
    Other(String),
}

impl ApiError {
    /// HTTP status code for this error
    pub fn status_code(&self) -> u16 {
        match self {
            ApiError::NotFound { .. } => 404,
            ApiError::Validation(_) => 422,
            ApiError::Other(_) => 500,
        }
    }
}

/// Config error type
#[derive(Error, Debug, Clone)]
#[error("Config error: {0}")]
pub struct ConfigError(pub String);

/// Domain error type
#[derive(Error, Debug, Clone)]
pub enum DomainError {
    #[error("validation failed: {0}")]
    Validation(String),
    #[error("Domain error: {0}")]
    Other(String),
}

/// Error envelope type
#[derive(Debug, Clone)]
pub struct ErrorEnvelope {
    pub message: String,
    pub code: u32,
}

/// Repository error type
#[derive(Error, Debug, Clone)]
#[error("Repository error: {0}")]
pub struct RepositoryError(pub String);

/// Storage error type
#[derive(Error, Debug, Clone)]
#[error("Storage error: {0}")]
pub struct StorageError(pub String);

/// Result type alias
pub type Result<T> = std::result::Result<T, PhenotypeError>;
