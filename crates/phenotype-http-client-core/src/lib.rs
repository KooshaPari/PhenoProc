//! # Phenotype HTTP Client Core
//!
//! Core HTTP client traits and utilities.
//!
//! ## Features
//!
//! - HTTP client trait
//! - Request/response builders
//! - Middleware support
//! - Retry and circuit breaker integration

use async_trait::async_trait;
use std::collections::HashMap;
use std::time::Duration;
use thiserror::Error;

/// HTTP client error
#[derive(Error, Debug)]
pub enum HttpClientError {
    #[error("Request failed: {0}")]
    RequestFailed(String),
    #[error("Response error: status {status}")]
    ResponseError { status: u16, body: String },
    #[error("Timeout after {0:?}")]
    Timeout(Duration),
    #[error("Connection error: {0}")]
    ConnectionError(String),
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
}

/// HTTP method
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HttpMethod {
    GET,
    POST,
    PUT,
    PATCH,
    DELETE,
    HEAD,
    OPTIONS,
}

impl HttpMethod {
    /// As string
    pub fn as_str(&self) -> &'static str {
        match self {
            HttpMethod::GET => "GET",
            HttpMethod::POST => "POST",
            HttpMethod::PUT => "PUT",
            HttpMethod::PATCH => "PATCH",
            HttpMethod::DELETE => "DELETE",
            HttpMethod::HEAD => "HEAD",
            HttpMethod::OPTIONS => "OPTIONS",
        }
    }
}

/// HTTP request
#[derive(Debug, Clone)]
pub struct HttpRequest {
    pub method: HttpMethod,
    pub url: String,
    pub headers: HashMap<String, String>,
    pub body: Option<Vec<u8>>,
    pub timeout: Option<Duration>,
}

impl HttpRequest {
    /// Create new request
    pub fn new(method: HttpMethod, url: impl Into<String>) -> Self {
        Self {
            method,
            url: url.into(),
            headers: HashMap::new(),
            body: None,
            timeout: None,
        }
    }

    /// Create GET request
    pub fn get(url: impl Into<String>) -> Self {
        Self::new(HttpMethod::GET, url)
    }

    /// Create POST request
    pub fn post(url: impl Into<String>) -> Self {
        Self::new(HttpMethod::POST, url)
    }

    /// Create PUT request
    pub fn put(url: impl Into<String>) -> Self {
        Self::new(HttpMethod::PUT, url)
    }

    /// Create DELETE request
    pub fn delete(url: impl Into<String>) -> Self {
        Self::new(HttpMethod::DELETE, url)
    }

    /// Set header
    pub fn with_header(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.headers.insert(key.into(), value.into());
        self
    }

    /// Set JSON body
    pub fn with_json_body<T: serde::Serialize>(
        mut self,
        body: &T,
    ) -> Result<Self, serde_json::Error> {
        let json = serde_json::to_vec(body)?;
        self.body = Some(json);
        self.headers
            .insert("Content-Type".to_string(), "application/json".to_string());
        Ok(self)
    }

    /// Set raw body
    pub fn with_body(mut self, body: Vec<u8>) -> Self {
        self.body = Some(body);
        self
    }

    /// Set timeout
    pub fn with_timeout(mut self, timeout: Duration) -> Self {
        self.timeout = Some(timeout);
        self
    }
}

/// HTTP response
#[derive(Debug, Clone)]
pub struct HttpResponse {
    pub status: u16,
    pub headers: HashMap<String, String>,
    pub body: Vec<u8>,
}

impl HttpResponse {
    /// Check if success (2xx)
    pub fn is_success(&self) -> bool {
        (200..300).contains(&self.status)
    }

    /// Get body as string
    pub fn body_string(&self) -> Result<String, std::string::FromUtf8Error> {
        String::from_utf8(self.body.clone())
    }

    /// Parse body as JSON
    pub fn json<T: for<'de> serde::Deserialize<'de>>(&self) -> Result<T, HttpClientError> {
        Ok(serde_json::from_slice(&self.body)?)
    }
}

/// HTTP client trait
#[async_trait]
pub trait HttpClient: Send + Sync {
    /// Execute request
    async fn execute(&self, request: HttpRequest) -> Result<HttpResponse, HttpClientError>;

    /// GET request
    async fn get(&self, url: impl Into<String> + Send) -> Result<HttpResponse, HttpClientError> {
        self.execute(HttpRequest::get(url)).await
    }

    /// POST request with JSON body
    async fn post_json<T: serde::Serialize + Send + Sync>(
        &self,
        url: impl Into<String> + Send,
        body: &T,
    ) -> Result<HttpResponse, HttpClientError> {
        let request = HttpRequest::post(url).with_json_body(body)?;
        self.execute(request).await
    }
}

/// Middleware trait for request/response processing
#[async_trait]
pub trait HttpMiddleware: Send + Sync {
    /// Process request before sending
    async fn process_request(&self, request: HttpRequest) -> HttpRequest;

    /// Process response after receiving
    async fn process_response(&self, response: HttpResponse) -> HttpResponse;
}

/// Middleware chain
pub struct MiddlewareChain {
    middlewares: Vec<Box<dyn HttpMiddleware>>,
}

impl MiddlewareChain {
    /// Create new chain
    pub fn new() -> Self {
        Self {
            middlewares: Vec::new(),
        }
    }

    /// Add middleware
    pub fn add(&mut self, middleware: Box<dyn HttpMiddleware>) {
        self.middlewares.push(middleware);
    }

    /// Process request through chain
    pub async fn process_request(&self, mut request: HttpRequest) -> HttpRequest {
        for middleware in &self.middlewares {
            request = middleware.process_request(request).await;
        }
        request
    }

    /// Process response through chain (reverse order)
    pub async fn process_response(&self, mut response: HttpResponse) -> HttpResponse {
        for middleware in self.middlewares.iter().rev() {
            response = middleware.process_response(response).await;
        }
        response
    }
}

impl Default for MiddlewareChain {
    fn default() -> Self {
        Self::new()
    }
}

/// Authentication middleware
pub struct AuthMiddleware {
    token: String,
}

impl AuthMiddleware {
    /// Create new auth middleware
    pub fn new(token: impl Into<String>) -> Self {
        Self {
            token: token.into(),
        }
    }
}

#[async_trait]
impl HttpMiddleware for AuthMiddleware {
    async fn process_request(&self, mut request: HttpRequest) -> HttpRequest {
        request.headers.insert(
            "Authorization".to_string(),
            format!("Bearer {}", self.token),
        );
        request
    }

    async fn process_response(&self, response: HttpResponse) -> HttpResponse {
        response
    }
}

/// Logging middleware
pub struct LoggingMiddleware;

#[async_trait]
impl HttpMiddleware for LoggingMiddleware {
    async fn process_request(&self, request: HttpRequest) -> HttpRequest {
        println!("[HTTP] {} {}", request.method.as_str(), request.url);
        request
    }

    async fn process_response(&self, response: HttpResponse) -> HttpResponse {
        println!("[HTTP] Response: {}", response.status);
        response
    }
}

/// Request builder
pub struct RequestBuilder {
    request: HttpRequest,
}

impl RequestBuilder {
    /// Create new builder
    pub fn new(method: HttpMethod, url: impl Into<String>) -> Self {
        Self {
            request: HttpRequest::new(method, url),
        }
    }

    /// Set header
    pub fn header(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.request.headers.insert(key.into(), value.into());
        self
    }

    /// Set JSON body
    pub fn json<T: serde::Serialize>(mut self, body: &T) -> Result<Self, serde_json::Error> {
        let json = serde_json::to_vec(body)?;
        self.request.body = Some(json);
        self.request
            .headers
            .insert("Content-Type".to_string(), "application/json".to_string());
        Ok(self)
    }

    /// Set timeout
    pub fn timeout(mut self, timeout: Duration) -> Self {
        self.request.timeout = Some(timeout);
        self
    }

    /// Build request
    pub fn build(self) -> HttpRequest {
        self.request
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_http_request_builder() {
        let request =
            HttpRequest::get("https://example.com/api").with_header("Accept", "application/json");

        assert_eq!(request.method, HttpMethod::GET);
        assert_eq!(request.url, "https://example.com/api");
        assert_eq!(
            request.headers.get("Accept"),
            Some(&"application/json".to_string())
        );
    }

    #[test]
    fn test_response_success() {
        let response = HttpResponse {
            status: 200,
            headers: HashMap::new(),
            body: b"OK".to_vec(),
        };

        assert!(response.is_success());

        let response = HttpResponse {
            status: 404,
            headers: HashMap::new(),
            body: b"Not Found".to_vec(),
        };

        assert!(!response.is_success());
    }

    #[test]
    fn test_request_builder() {
        let request = RequestBuilder::new(HttpMethod::POST, "https://api.example.com/data")
            .header("Authorization", "Bearer token123")
            .build();

        assert_eq!(request.method, HttpMethod::POST);
        assert_eq!(
            request.headers.get("Authorization"),
            Some(&"Bearer token123".to_string())
        );
    }
}
