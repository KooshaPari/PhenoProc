//! Phenotype Retry Library
//!
//! Type-safe, async-first retry framework with multiple backoff strategies
//! for the Phenotype ecosystem.

use std::fmt;
use std::future::Future;
use std::time::Duration;

use async_trait::async_trait;
use thiserror::Error;
use tokio::time::{sleep, Instant};

/// Errors during retry operations
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum RetryError<E> {
    #[error("Max retry attempts ({attempts}) exceeded")]
    Exceeded { attempts: u32, last_error: E },
    #[error("Retry cancelled")]
    Cancelled,
}

/// Backoff strategies
#[derive(Clone)]
pub enum BackoffStrategy {
    Fixed {
        delay: Duration,
    },
    Linear {
        base: Duration,
    },
    Exponential {
        base: Duration,
        max: Duration,
    },
    Custom {
        func: std::sync::Arc<dyn Fn(u32) -> Duration + Send + Sync>,
    },
}

impl BackoffStrategy {
    pub fn fixed(delay: Duration) -> Self {
        Self::Fixed { delay }
    }

    pub fn linear(base: Duration) -> Self {
        Self::Linear { base }
    }

    pub fn exponential(base: Duration, max: Duration) -> Self {
        Self::Exponential { base, max }
    }

    pub fn custom<F: Fn(u32) -> Duration + Send + Sync + 'static>(func: F) -> Self {
        Self::Custom {
            func: std::sync::Arc::new(func),
        }
    }

    pub fn calculate_delay(&self, attempt: u32) -> Duration {
        match self {
            Self::Fixed { delay } => *delay,
            Self::Linear { base } => *base * attempt,
            Self::Exponential { base, max } => {
                let exp = attempt.saturating_sub(1) as u32;
                (*base * 2_u32.saturating_pow(exp)).min(*max)
            }
            Self::Custom { func } => func(attempt),
        }
    }
}

impl fmt::Debug for BackoffStrategy {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Fixed { delay } => f.debug_struct("Fixed").field("delay", delay).finish(),
            Self::Linear { base } => f.debug_struct("Linear").field("base", base).finish(),
            Self::Exponential { base, max } => f
                .debug_struct("Exponential")
                .field("base", base)
                .field("max", max)
                .finish(),
            Self::Custom { .. } => f.debug_struct("Custom").finish_non_exhaustive(),
        }
    }
}

/// Retry context
#[derive(Debug, Clone)]
pub struct RetryContext {
    pub attempt: u32,
    pub max_attempts: u32,
    pub elapsed: Duration,
    pub last_error: Option<String>,
}

impl RetryContext {
    pub fn is_first_attempt(&self) -> bool {
        self.attempt == 1
    }

    pub fn is_last_attempt(&self) -> bool {
        self.attempt >= self.max_attempts
    }
}

/// Retry predicate type
/// Retry policy
#[derive(Clone)]
pub struct RetryPolicy {
    pub max_attempts: u32,
    pub backoff: BackoffStrategy,
}

impl RetryPolicy {
    pub fn new(max_attempts: u32, backoff: BackoffStrategy) -> Self {
        Self {
            max_attempts: max_attempts.max(1),
            backoff,
        }
    }

    pub fn default_exponential(max_attempts: u32) -> Self {
        Self::new(
            max_attempts,
            BackoffStrategy::exponential(Duration::from_millis(100), Duration::from_secs(5)),
        )
    }

    fn is_retryable<E: std::error::Error>(&self, _error: &E) -> bool {
        true
    }
}
impl fmt::Debug for RetryPolicy {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("RetryPolicy")
            .field("max_attempts", &self.max_attempts)
            .field("backoff", &self.backoff)
            .finish()
    }
}

impl Default for RetryPolicy {
    fn default() -> Self {
        Self::default_exponential(3)
    }
}

/// Retry trait
#[async_trait]
pub trait Retryable<T, E> {
    async fn retry(&self, policy: &RetryPolicy) -> Result<T, RetryError<E>>
    where
        E: std::error::Error + Send + Sync + 'static;
}

/// Retry an operation
pub async fn retry<F, Fut, T, E>(mut operation: F, policy: &RetryPolicy) -> Result<T, RetryError<E>>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, E>>,
    E: std::error::Error + Send + Sync + 'static,
{
    let _start = Instant::now();
    let mut last_error: Option<E> = None;

    for attempt in 1..=policy.max_attempts {
        match operation().await {
            Ok(value) => return Ok(value),
            Err(error) => {
                if !policy.is_retryable(&error) {
                    return Err(RetryError::Exceeded {
                        attempts: attempt,
                        last_error: error,
                    });
                }

                last_error = Some(error);

                if attempt >= policy.max_attempts {
                    return Err(RetryError::Exceeded {
                        attempts: attempt,
                        last_error: last_error.unwrap(),
                    });
                }

                sleep(policy.backoff.calculate_delay(attempt)).await;
            }
        }
    }

    Err(RetryError::Exceeded {
        attempts: policy.max_attempts,
        last_error: last_error.unwrap(),
    })
}

/// Retry with context
pub async fn retry_with_context<F, Fut, T, E>(
    mut operation: F,
    policy: &RetryPolicy,
) -> Result<T, RetryError<E>>
where
    F: FnMut(RetryContext) -> Fut,
    Fut: Future<Output = Result<T, E>>,
    E: std::error::Error + Send + Sync + 'static,
{
    let start = Instant::now();
    let mut last_error: Option<E> = None;

    for attempt in 1..=policy.max_attempts {
        let context = RetryContext {
            attempt,
            max_attempts: policy.max_attempts,
            elapsed: start.elapsed(),
            last_error: last_error.as_ref().map(|e| e.to_string()),
        };

        match operation(context).await {
            Ok(value) => return Ok(value),
            Err(error) => {
                last_error = Some(error);
                if attempt >= policy.max_attempts {
                    return Err(RetryError::Exceeded {
                        attempts: attempt,
                        last_error: last_error.unwrap(),
                    });
                }
                sleep(policy.backoff.calculate_delay(attempt)).await;
            }
        }
    }

    Err(RetryError::Exceeded {
        attempts: policy.max_attempts,
        last_error: last_error.unwrap(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicU32, Ordering};
    use std::sync::Arc;

    #[tokio::test]
    async fn test_exponential_backoff_success_on_third_attempt() {
        let counter = Arc::new(AtomicU32::new(0));
        let counter_clone = counter.clone();

        let policy = RetryPolicy::new(
            5,
            BackoffStrategy::exponential(Duration::from_millis(10), Duration::from_secs(1)),
        );

        let start = Instant::now();

        let result = retry(
            || {
                let count = counter_clone.clone();
                async move {
                    let current = count.fetch_add(1, Ordering::SeqCst);
                    if current < 2 {
                        Err::<String, std::io::Error>(std::io::Error::new(
                            std::io::ErrorKind::Other,
                            "fail",
                        ))
                    } else {
                        Ok("success".to_string())
                    }
                }
            },
            &policy,
        )
        .await;

        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "success");
        assert_eq!(counter.load(Ordering::SeqCst), 3);
        assert!(start.elapsed() >= Duration::from_millis(30));
    }

    #[tokio::test]
    async fn test_max_attempts_exceeded() {
        let counter = Arc::new(AtomicU32::new(0));
        let counter_clone = counter.clone();

        let policy = RetryPolicy::new(3, BackoffStrategy::fixed(Duration::from_millis(1)));

        let result: Result<String, RetryError<std::io::Error>> = retry(
            || {
                let count = counter_clone.clone();
                async move {
                    count.fetch_add(1, Ordering::SeqCst);
                    Err::<String, std::io::Error>(std::io::Error::new(
                        std::io::ErrorKind::Other,
                        "always fails",
                    ))
                }
            },
            &policy,
        )
        .await;

        assert!(result.is_err());
        match result {
            Err(RetryError::Exceeded {
                attempts,
                last_error,
            }) => {
                assert_eq!(attempts, 3);
                assert_eq!(last_error.kind(), std::io::ErrorKind::Other);
            }
            _ => panic!("Expected Exceeded error"),
        }
        assert_eq!(counter.load(Ordering::SeqCst), 3);
    }

    #[test]
    fn test_fixed_backoff() {
        let strategy = BackoffStrategy::fixed(Duration::from_millis(100));
        assert_eq!(strategy.calculate_delay(1), Duration::from_millis(100));
        assert_eq!(strategy.calculate_delay(5), Duration::from_millis(100));
    }

    #[test]
    fn test_linear_backoff() {
        let strategy = BackoffStrategy::linear(Duration::from_millis(50));
        assert_eq!(strategy.calculate_delay(1), Duration::from_millis(50));
        assert_eq!(strategy.calculate_delay(2), Duration::from_millis(100));
        assert_eq!(strategy.calculate_delay(3), Duration::from_millis(150));
    }

    #[test]
    fn test_exponential_backoff() {
        let strategy =
            BackoffStrategy::exponential(Duration::from_millis(100), Duration::from_millis(500));
        assert_eq!(strategy.calculate_delay(1), Duration::from_millis(100));
        assert_eq!(strategy.calculate_delay(2), Duration::from_millis(200));
        assert_eq!(strategy.calculate_delay(3), Duration::from_millis(400));
        assert_eq!(strategy.calculate_delay(4), Duration::from_millis(500));
        assert_eq!(strategy.calculate_delay(5), Duration::from_millis(500));
    }

    #[test]
    fn test_custom_backoff() {
        let strategy =
            BackoffStrategy::custom(|attempt| Duration::from_millis(attempt as u64 * 10));
        assert_eq!(strategy.calculate_delay(1), Duration::from_millis(10));
        assert_eq!(strategy.calculate_delay(5), Duration::from_millis(50));
    }

    #[test]
    fn test_retry_policy_default() {
        let policy: RetryPolicy = Default::default();
        assert_eq!(policy.max_attempts, 3);
    }

    #[test]
    fn test_retry_context() {
        let ctx = RetryContext {
            attempt: 1,
            max_attempts: 3,
            elapsed: Duration::from_millis(100),
            last_error: None,
        };
        assert!(ctx.is_first_attempt());
        assert!(!ctx.is_last_attempt());

        let ctx_last = RetryContext {
            attempt: 3,
            max_attempts: 3,
            elapsed: Duration::from_millis(300),
            last_error: Some("error".to_string()),
        };
        assert!(!ctx_last.is_first_attempt());
        assert!(ctx_last.is_last_attempt());
    }

    #[tokio::test]
    async fn test_retry_with_context() {
        let policy = RetryPolicy::new(2, BackoffStrategy::fixed(Duration::from_millis(1)));
        let mut attempts = Vec::new();

        let result: Result<String, RetryError<std::io::Error>> = retry_with_context(
            |ctx| {
                attempts.push(ctx.attempt);
                async move {
                    Err::<String, std::io::Error>(std::io::Error::new(
                        std::io::ErrorKind::Other,
                        "fail",
                    ))
                }
            },
            &policy,
        )
        .await;

        assert!(result.is_err());
        assert_eq!(attempts, vec![1, 2]);
    }

    #[tokio::test]
    async fn test_retry_succeeds_first_attempt() {
        let policy = RetryPolicy::new(3, BackoffStrategy::fixed(Duration::from_millis(10)));
        let counter = Arc::new(AtomicU32::new(0));
        let counter_clone = counter.clone();

        let result = retry(
            || {
                let count = counter_clone.clone();
                async move {
                    count.fetch_add(1, Ordering::SeqCst);
                    Ok::<String, std::io::Error>("immediate success".to_string())
                }
            },
            &policy,
        )
        .await;

        assert!(result.is_ok());
        assert_eq!(counter.load(Ordering::SeqCst), 1);
    }

    #[test]
    fn test_retry_error_display() {
        let error: RetryError<String> = RetryError::Exceeded {
            attempts: 3,
            last_error: "test".to_string(),
        };
        let msg = format!("{}", error);
        assert!(msg.contains("Max retry attempts (3) exceeded"));
    }
}
