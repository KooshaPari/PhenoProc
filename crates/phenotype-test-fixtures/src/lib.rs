//! Test fixtures and builders for phenotype testing.
//!
//! Provides factory functions and builders for creating test data,
//! mock objects, and common test scenarios.

#![doc = r#"
# Phenotype Test Fixtures

Reusable test fixtures for Phenotype workspace crates.

## Usage

```rust
use phenotype_test_fixtures::TestData;

let data = TestData::new("test", 42i32);
```
"#]

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Common test data containers.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestData<T> {
    pub id: Uuid,
    pub name: String,
    pub value: T,
    pub created_at: DateTime<Utc>,
    pub metadata: HashMap<String, String>,
}

impl<T: Default> TestData<T> {
    pub fn new(name: impl Into<String>, value: T) -> Self {
        Self {
            id: Uuid::new_v4(),
            name: name.into(),
            value,
            created_at: Utc::now(),
            metadata: HashMap::new(),
        }
    }

    pub fn with_metadata(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.metadata.insert(key.into(), value.into());
        self
    }
}

/// Test scenario definition.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestScenario {
    pub name: String,
    pub description: String,
    pub setup: Vec<TestStep>,
    pub execution: Vec<TestStep>,
    pub teardown: Vec<TestStep>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestStep {
    pub name: String,
    pub action: String,
    pub expected_result: String,
}

/// Test environment configuration.
#[derive(Debug)]
pub struct TestEnv {
    pub temp_dir: tempfile::TempDir,
    pub env_vars: HashMap<String, String>,
}

impl TestEnv {
    pub fn new() -> std::io::Result<Self> {
        Ok(Self {
            temp_dir: tempfile::tempdir()?,
            env_vars: HashMap::new(),
        })
    }

    pub fn path(&self) -> &std::path::Path {
        self.temp_dir.path()
    }

    pub fn set_env(&mut self, key: impl Into<String>, value: impl Into<String>) {
        self.env_vars.insert(key.into(), value.into());
    }
}

/// Assertion helpers for tests.
pub mod assertions {
    use std::fmt::Debug;

    /// Assert that a result is Ok and return the value.
    pub fn assert_ok<T, E: Debug>(result: Result<T, E>) -> T {
        match result {
            Ok(v) => v,
            Err(e) => panic!("Expected Ok, got Err: {:?}", e),
        }
    }

    /// Assert that a result is Err.
    pub fn assert_err<T: Debug, E>(result: Result<T, E>) -> E {
        match result {
            Ok(v) => panic!("Expected Err, got Ok: {:?}", v),
            Err(e) => e,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_data_creation() {
        let data = TestData::new("test", 42i32);
        assert_eq!(data.name, "test");
        assert_eq!(data.value, 42);
        assert!(data.metadata.is_empty());
    }

    #[test]
    fn test_env_creation() {
        let env = TestEnv::new().unwrap();
        assert!(env.path().exists());
    }
}
