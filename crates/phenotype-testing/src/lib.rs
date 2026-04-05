//! # Phenotype Testing
//!
//! Testing utilities and helpers for async and sync tests.
//!
//! ## Features
//!
//! - Async test runtime helpers
//! - Mock store implementations
//! - Assertion helpers
//! - Test data generators
//! - Timeout utilities

use std::future::Future;
use std::time::Duration;

/// Run a future with a timeout for tests
pub async fn timeout<F, T>(future: F, duration: Duration) -> Result<T, tokio::time::error::Elapsed>
where
    F: Future<Output = T>,
{
    tokio::time::timeout(duration, future).await
}

/// Run a future with a default 5 second timeout
pub async fn timeout_default<F, T>(future: F) -> Result<T, tokio::time::error::Elapsed>
where
    F: Future<Output = T>,
{
    timeout(future, Duration::from_secs(5)).await
}

/// Block on a future in a test (for sync test contexts)
pub fn block_on<F, T>(future: F) -> T
where
    F: Future<Output = T>,
{
    tokio_test::block_on(future)
}

/// Generate a unique test ID
pub fn test_id() -> String {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    let id: u64 = rng.gen();
    format!("test-{}", id)
}

/// Generate a random port for test servers
pub fn random_port() -> u16 {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    // Ports 49152-65535 are dynamic/private
    rng.gen_range(49152..=65535)
}

/// Wait for a condition to become true with timeout
pub async fn wait_for<F, Fut>(mut condition: F, timeout: Duration) -> bool
where
    F: FnMut() -> Fut,
    Fut: Future<Output = bool>,
{
    let start = tokio::time::Instant::now();
    loop {
        if condition().await {
            return true;
        }
        if start.elapsed() > timeout {
            return false;
        }
        tokio::time::sleep(Duration::from_millis(10)).await;
    }
}

/// Retry an async operation with exponential backoff
pub async fn retry_async<F, Fut, T, E>(
    mut operation: F,
    max_attempts: u32,
    base_delay: Duration,
) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, E>>,
{
    for attempt in 0..max_attempts {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) if attempt == max_attempts - 1 => return Err(e),
            Err(_) => {
                let delay = base_delay * 2u32.pow(attempt);
                tokio::time::sleep(delay).await;
            }
        }
    }
    unreachable!()
}

/// Test assertion helpers
pub mod assertions {
    use std::future::Future;
    use std::time::Duration;
    /// Assert that a result is Ok and return the value
    pub fn assert_ok<T, E>(result: Result<T, E>) -> T
    where
        E: std::fmt::Debug,
    {
        match result {
            Ok(val) => val,
            Err(e) => panic!("Expected Ok, got Err: {:?}", e),
        }
    }

    /// Assert that a result is Err and return the error
    pub fn assert_err<T, E>(result: Result<T, E>) -> E
    where
        T: std::fmt::Debug,
    {
        match result {
            Err(e) => e,
            Ok(val) => panic!("Expected Err, got Ok: {:?}", val),
        }
    }

    /// Assert that a future completes within a duration
    pub async fn assert_completes<F, T>(future: F, duration: Duration)
    where
        F: Future<Output = T>,
    {
        match tokio::time::timeout(duration, future).await {
            Ok(_) => {}
            Err(_) => panic!("Future did not complete within {:?}", duration),
        }
    }

    /// Assert that a string contains a substring
    pub fn assert_contains(haystack: &str, needle: &str) {
        assert!(
            haystack.contains(needle),
            "Expected '{}' to contain '{}'",
            haystack,
            needle
        );
    }
}

/// Test data generators
pub mod generators {
    use rand::Rng;

    /// Generate a random string of specified length
    pub fn random_string(len: usize) -> String {
        const CHARSET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        let mut rng = rand::thread_rng();
        (0..len)
            .map(|_| {
                let idx = rng.gen_range(0..CHARSET.len());
                CHARSET[idx] as char
            })
            .collect()
    }

    /// Generate a random email address
    pub fn random_email() -> String {
        format!("{}@example.com", random_string(10))
    }

    /// Generate a random UUID-like string
    pub fn random_uuid() -> String {
        use rand::Rng;
        let mut rng = rand::thread_rng();
        let hex = |len: usize, rng: &mut rand::rngs::ThreadRng| -> String {
            (0..len)
                .map(|_| format!("{:x}", rng.gen_range(0..16)))
                .collect()
        };
        format!(
            "{}-{}-{}-{}-{}",
            hex(8, &mut rng),
            hex(4, &mut rng),
            hex(4, &mut rng),
            hex(4, &mut rng),
            hex(12, &mut rng)
        )
    }
}

/// Async test runtime setup
pub mod runtime {
    use std::sync::Once;

    static INIT: Once = Once::new();

    /// Initialize test tracing
    pub fn init_tracing() {
        INIT.call_once(|| {
            tracing_subscriber::fmt()
                .with_test_writer()
                .with_max_level(tracing::Level::DEBUG)
                .init();
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_timeout_success() {
        let result = timeout(async { 42 }, Duration::from_secs(1)).await;
        assert_eq!(result.unwrap(), 42);
    }

    #[tokio::test]
    async fn test_timeout_failure() {
        let result = timeout(
            async {
                tokio::time::sleep(Duration::from_secs(10)).await;
                42
            },
            Duration::from_millis(10),
        )
        .await;
        assert!(result.is_err());
    }

    #[test]
    fn test_random_port() {
        let port1 = random_port();
        let port2 = random_port();
        assert!(port1 >= 49152);
        assert!(port2 >= 49152);
        // Very unlikely to be the same
        assert_ne!(port1, port2);
    }

    #[test]
    fn test_generators() {
        let s = generators::random_string(10);
        assert_eq!(s.len(), 10);

        let email = generators::random_email();
        assert!(email.contains('@'));

        let uuid = generators::random_uuid();
        assert_eq!(uuid.len(), 36);
    }

    #[tokio::test]
    async fn test_retry_async() {
        let mut attempts = 0;
        let result: Result<i32, ()> = retry_async(
            || {
                attempts += 1;
                async move {
                    if attempts < 3 {
                        Err(())
                    } else {
                        Ok(42)
                    }
                }
            },
            5,
            Duration::from_millis(1),
        )
        .await;
        assert_eq!(result.unwrap(), 42);
        assert_eq!(attempts, 3);
    }
}
