//! Phenotype Test Infra - Test infrastructure and utilities
//!
//! Provides test servers, database setup, and integration test helpers.

#![cfg_attr(docsrs, feature(doc_auto_cfg))]

use std::net::SocketAddr;

use tempfile::TempDir;
use tokio::net::TcpListener;
use tracing::info;

/// Test server for integration tests
pub struct TestServer {
    pub addr: SocketAddr,
    pub base_url: String,
    _temp_dir: TempDir,
}

impl TestServer {
    pub async fn new() -> std::io::Result<Self> {
        let temp_dir = TempDir::new()?;
        let listener = TcpListener::bind("127.0.0.1:0").await?;
        let addr = listener.local_addr()?;
        let base_url = format!("http://{}", addr);

        info!("Test server started at {}", base_url);

        Ok(Self {
            addr,
            base_url,
            _temp_dir: temp_dir,
        })
    }

    pub fn url(&self, path: &str) -> String {
        format!("{}{}", self.base_url, path)
    }
}

/// Test database wrapper
pub struct TestDatabase {
    pub connection_string: String,
    _temp_dir: TempDir,
}

impl TestDatabase {
    pub fn new() -> std::io::Result<Self> {
        let temp_dir = TempDir::new()?;
        let db_path = temp_dir.path().join("test.db");
        let connection_string = format!("sqlite:{}", db_path.display());

        Ok(Self {
            connection_string,
            _temp_dir: temp_dir,
        })
    }

    pub async fn setup(&self) -> Result<(), Box<dyn std::error::Error>> {
        // Initialize schema
        info!("Setting up test database at {}", self.connection_string);
        Ok(())
    }

    pub async fn teardown(&self) -> Result<(), Box<dyn std::error::Error>> {
        info!("Tearing down test database");
        Ok(())
    }
}

/// Test context holding all test resources
pub struct TestContext {
    pub server: Option<TestServer>,
    pub database: Option<TestDatabase>,
    pub temp_dir: TempDir,
}

impl TestContext {
    pub fn new() -> std::io::Result<Self> {
        Ok(Self {
            server: None,
            database: None,
            temp_dir: TempDir::new()?,
        })
    }

    pub async fn with_server(mut self) -> std::io::Result<Self> {
        self.server = Some(TestServer::new().await?);
        Ok(self)
    }

    pub fn with_database(mut self) -> std::io::Result<Self> {
        self.database = Some(TestDatabase::new()?);
        Ok(self)
    }
}

/// Port allocator for tests
pub struct PortAllocator {
    base_port: u16,
    current: u16,
}

impl PortAllocator {
    pub fn new(base_port: u16) -> Self {
        Self {
            base_port,
            current: base_port,
        }
    }

    pub fn next(&mut self) -> u16 {
        let port = self.current;
        self.current += 1;
        port
    }

    pub fn reset(&mut self) {
        self.current = self.base_port;
    }
}

/// Test environment setup
pub fn setup_test_env() {
    // Initialize tracing for tests
    let _ = tracing_subscriber::fmt()
        .with_env_filter("debug")
        .try_init();
}

/// Assert that a future completes within a timeout
pub async fn assert_timeout<F, Fut>(f: F, timeout_ms: u64)
where
    F: FnOnce() -> Fut,
    Fut: std::future::Future,
{
    let timeout = tokio::time::Duration::from_millis(timeout_ms);
    let result = tokio::time::timeout(timeout, f()).await;
    assert!(result.is_ok(), "Operation timed out after {}ms", timeout_ms);
}

/// Retry an async operation with exponential backoff
pub async fn retry_async<F, Fut, T, E>(mut f: F, max_attempts: u32) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: std::future::Future<Output = Result<T, E>>,
{
    let mut attempts = 0;
    loop {
        match f().await {
            Ok(result) => return Ok(result),
            Err(e) if attempts < max_attempts => {
                attempts += 1;
                let delay = std::time::Duration::from_millis(100 * 2_u64.pow(attempts));
                tokio::time::sleep(delay).await;
            }
            Err(e) => return Err(e),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_port_allocator() {
        let mut allocator = PortAllocator::new(10000);
        assert_eq!(allocator.next(), 10000);
        assert_eq!(allocator.next(), 10001);
        allocator.reset();
        assert_eq!(allocator.next(), 10000);
    }
}
