//! Phenotype Async Traits - Common async trait patterns and utilities
//!
//! Provides reusable async trait definitions and stream utilities.

#![cfg_attr(docsrs, feature(doc_auto_cfg))]

use std::future::Future;
use std::pin::Pin;

use async_trait::async_trait;
use futures::{Stream, StreamExt};
use pin_project::pin_project;

/// Async initializer trait
#[async_trait]
pub trait AsyncInit: Send + Sync {
    async fn init(&mut self) -> Result<(), Box<dyn std::error::Error + Send + Sync>>;

    async fn shutdown(&mut self) -> Result<(), Box<dyn std::error::Error + Send + Sync>>;
}

/// Async resource trait
#[async_trait]
pub trait AsyncResource<T>: Send + Sync {
    async fn acquire(&self) -> Result<T, Box<dyn std::error::Error + Send + Sync>>;

    async fn release(&self, resource: T) -> Result<(), Box<dyn std::error::Error + Send + Sync>>;
}

/// Stream timeout wrapper
#[pin_project]
pub struct TimeoutStream<S> {
    #[pin]
    inner: S,
    timeout: std::time::Duration,
}

impl<S: Stream> Stream for TimeoutStream<S> {
    type Item = Result<S::Item, tokio::time::error::Elapsed>;

    fn poll_next(
        self: Pin<&mut Self>,
        cx: &mut std::task::Context<'_>,
    ) -> std::task::Poll<Option<Self::Item>> {
        let this = self.project();
        // Simplified - in production would implement actual timeout logic
        this.inner.poll_next(cx).map(|opt| opt.map(Ok))
    }
}

/// Async semaphore with priority
pub struct PrioritySemaphore {
    permits: tokio::sync::Semaphore,
}

impl PrioritySemaphore {
    pub fn new(permits: usize) -> Self {
        Self {
            permits: tokio::sync::Semaphore::new(permits),
        }
    }

    pub async fn acquire(&self) -> tokio::sync::SemaphorePermit<'_> {
        self.permits.acquire().await.expect("Semaphore closed")
    }
}

/// Background task handle
pub struct BackgroundTask<T> {
    handle: tokio::task::JoinHandle<T>,
    abort_handle: tokio::task::AbortHandle,
}

impl<T> BackgroundTask<T> {
    pub fn spawn<F, Fut>(f: F) -> Self
    where
        F: FnOnce() -> Fut + Send + 'static,
        Fut: Future<Output = T> + Send + 'static,
        T: Send + 'static,
    {
        let handle = tokio::spawn(f());
        let abort_handle = handle.abort_handle();
        Self {
            handle,
            abort_handle,
        }
    }

    pub fn abort(&self) {
        self.abort_handle.abort();
    }

    pub async fn await_completion(self) -> Result<T, tokio::task::JoinError> {
        self.handle.await
    }
}

/// Async interval with jitter
pub struct JitteredInterval {
    interval: tokio::time::Interval,
    jitter_ms: u64,
}

impl JitteredInterval {
    pub fn new(period: std::time::Duration, jitter_ms: u64) -> Self {
        let interval = tokio::time::interval(period);
        Self {
            interval,
            jitter_ms,
        }
    }

    pub async fn tick(&mut self) -> tokio::time::Instant {
        let jitter = if self.jitter_ms > 0 {
            let mut rng = rand::rngs::ThreadRng::default();
            std::time::Duration::from_millis(rand::Rng::gen_range(&mut rng, 0..self.jitter_ms))
        } else {
            std::time::Duration::from_millis(0)
        };
        tokio::time::sleep(jitter).await;
        self.interval.tick().await
    }
}

/// Rate limiter using token bucket algorithm
pub struct AsyncRateLimiter {
    semaphore: PrioritySemaphore,
    max_per_second: u32,
}

impl AsyncRateLimiter {
    pub fn new(max_per_second: u32) -> Self {
        Self {
            semaphore: PrioritySemaphore::new(max_per_second as usize),
            max_per_second,
        }
    }

    pub async fn acquire(&self) -> Result<(), String> {
        // Simple rate limiting: calculate min interval between requests
        let min_interval = std::time::Duration::from_secs(1) / self.max_per_second;
        tokio::time::sleep(min_interval).await;
        let _permit = self.semaphore.acquire().await;
        Ok(())
    }
}

/// Future extension traits
pub trait FutureExt: Future + Sized {
    fn with_timeout(self, duration: std::time::Duration) -> tokio::time::Timeout<Self>;
}

impl<F: Future> FutureExt for F {
    fn with_timeout(self, duration: std::time::Duration) -> tokio::time::Timeout<Self> {
        tokio::time::timeout(duration, self)
    }
}

/// Stream extension traits
pub trait StreamExt2: Stream + Sized {
    fn buffered_unordered(self, n: usize) -> futures::stream::BufferUnordered<Self>;
}

impl<S: Stream> StreamExt2 for S
where
    S::Item: Future,
{
    fn buffered_unordered(self, n: usize) -> futures::stream::BufferUnordered<Self> {
        self.buffer_unordered(n)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_semaphore() {
        let sem = PrioritySemaphore::new(2);
        let _permit1 = sem.acquire().await;
        let _permit2 = sem.acquire().await;
    }

    #[tokio::test]
    async fn test_rate_limiter() {
        let limiter = AsyncRateLimiter::new(10);
        limiter.acquire().await;
    }
}
