//! Phenotype Config Core - Configuration management
//!
//! Provides typed configuration with validation and hot-reloading.

#![cfg_attr(docsrs, feature(doc_auto_cfg))]

use std::path::Path;

use phenotype_validation::{Validate, ValidationError};
use serde::de::DeserializeOwned;
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Configuration error types
#[derive(Debug, Error)]
pub enum ConfigError {
    #[error("Failed to load config: {0}")]
    LoadFailed(String),

    #[error("Failed to parse config: {0}")]
    ParseFailed(String),

    #[error("Validation failed: {0:?}")]
    ValidationFailed(Vec<ValidationError>),

    #[error("Config key not found: {0}")]
    KeyNotFound(String),

    #[error("Environment variable not found: {0}")]
    EnvVarNotFound(String),
}

/// Configuration source
#[derive(Debug, Clone)]
pub enum ConfigSource {
    File(String),
    Env(String),
    Inline(String),
    Remote(String),
}

/// Typed configuration trait
pub trait Config: DeserializeOwned + Serialize + Validate + Clone {
    fn prefix() -> &'static str;

    fn load() -> Result<Self, ConfigError> {
        // Default implementation tries to load from various sources
        Self::from_env()
    }

    fn from_env() -> Result<Self, ConfigError> {
        // In production, would use env vars with prefix
        Err(ConfigError::EnvVarNotFound("Not implemented".to_string()))
    }

    fn from_file<P: AsRef<Path>>(path: P) -> Result<Self, ConfigError> {
        let content =
            std::fs::read_to_string(path).map_err(|e| ConfigError::LoadFailed(e.to_string()))?;
        Self::from_str(&content)
    }

    fn from_str(s: &str) -> Result<Self, ConfigError> {
        serde_yaml::from_str(s).map_err(|e| ConfigError::ParseFailed(e.to_string()))
    }

    fn merge(&mut self, other: &Self) -> Result<(), ConfigError>;
}

/// Configuration manager
pub struct ConfigManager<T: Config> {
    current: T,
    sources: Vec<ConfigSource>,
    validators: Vec<Box<dyn Fn(&T) -> Result<(), ConfigError>>>,
}

impl<T: Config> ConfigManager<T> {
    pub fn new(default_config: T) -> Self {
        Self {
            current: default_config,
            sources: Vec::new(),
            validators: Vec::new(),
        }
    }

    pub fn with_source(mut self, source: ConfigSource) -> Self {
        self.sources.push(source);
        self
    }

    pub fn with_validator<F>(mut self, validator: F) -> Self
    where
        F: Fn(&T) -> Result<(), ConfigError> + 'static,
    {
        self.validators.push(Box::new(validator));
        self
    }

    pub async fn load(&mut self) -> Result<(), ConfigError> {
        for source in &self.sources {
            match source {
                ConfigSource::File(path) => {
                    let new_config = T::from_file(path)?;
                    self.current.merge(&new_config)?;
                }
                ConfigSource::Env(_prefix) => {
                    // Load from environment variables
                }
                _ => {}
            }
        }

        // Validate
        if let Err(validation_errors) = self.current.validate() {
            return Err(ConfigError::ValidationFailed(
                validation_errors.errors.into_iter().collect(),
            ));
        }

        for validator in &self.validators {
            validator(&self.current)?;
        }

        Ok(())
    }

    pub fn get(&self) -> &T {
        &self.current
    }

    pub fn get_mut(&mut self) -> &mut T {
        &mut self.current
    }
}

/// Configuration watcher for hot-reloading
pub struct ConfigWatcher<T: Config> {
    manager: ConfigManager<T>,
    watch_paths: Vec<String>,
}

impl<T: Config> ConfigWatcher<T> {
    pub fn new(manager: ConfigManager<T>) -> Self {
        Self {
            manager,
            watch_paths: Vec::new(),
        }
    }

    pub fn watch(mut self, path: impl Into<String>) -> Self {
        self.watch_paths.push(path.into());
        self
    }

    pub async fn run(&mut self) -> Result<(), ConfigError> {
        // In production, would use notify crate for file watching
        loop {
            tokio::time::sleep(std::time::Duration::from_secs(5)).await;
            if let Err(e) = self.manager.load().await {
                tracing::warn!("Config reload failed: {}", e);
            }
        }
    }
}

/// Common configuration sections
pub mod sections {
    use super::*;

    /// Database configuration
    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub struct DatabaseConfig {
        pub url: String,
        pub max_connections: u32,
        pub min_connections: u32,
        pub connect_timeout_ms: u64,
        pub idle_timeout_ms: u64,
    }

    impl Default for DatabaseConfig {
        fn default() -> Self {
            Self {
                url: "postgres://localhost:5432/phenotype".to_string(),
                max_connections: 10,
                min_connections: 1,
                connect_timeout_ms: 5000,
                idle_timeout_ms: 300000,
            }
        }
    }

    /// HTTP server configuration
    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub struct ServerConfig {
        pub host: String,
        pub port: u16,
        pub request_timeout_ms: u64,
        pub max_request_size: usize,
    }

    impl Default for ServerConfig {
        fn default() -> Self {
            Self {
                host: "0.0.0.0".to_string(),
                port: 8080,
                request_timeout_ms: 30000,
                max_request_size: 10 * 1024 * 1024, // 10MB
            }
        }
    }

    /// Logging configuration
    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub struct LoggingConfig {
        pub level: String,
        pub format: LogFormat,
        pub output: LogOutput,
    }

    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub enum LogFormat {
        Json,
        Pretty,
        Compact,
    }

    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub enum LogOutput {
        Stdout,
        Stderr,
        File(String),
    }

    impl Default for LoggingConfig {
        fn default() -> Self {
            Self {
                level: "info".to_string(),
                format: LogFormat::Pretty,
                output: LogOutput::Stdout,
            }
        }
    }
}

/// Environment variable helper
pub fn env_var(key: &str) -> Result<String, ConfigError> {
    std::env::var(key).map_err(|_| ConfigError::EnvVarNotFound(key.to_string()))
}

/// Load configuration from multiple sources
pub async fn load_config<T: Config + Default>(
    file_path: Option<&str>,
    env_prefix: Option<&str>,
) -> Result<T, ConfigError> {
    let mut manager = ConfigManager::new(T::default());

    if let Some(path) = file_path {
        manager = manager.with_source(ConfigSource::File(path.to_string()));
    }

    if let Some(prefix) = env_prefix {
        manager = manager.with_source(ConfigSource::Env(prefix.to_string()));
    }

    manager.load().await?;
    Ok(manager.get().clone())
}
