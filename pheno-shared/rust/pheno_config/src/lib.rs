//! Pheno shared library crate

pub mod config {
    //! Configuration module

    use std::collections::HashMap;
    use std::sync::RwLock;

    /// Configuration container
    #[derive(Debug, Default)]
    pub struct Config {
        data: RwLock<HashMap<String, String>>,
    }

    impl Config {
        /// Create new config
        pub fn new() -> Self {
            Self::default()
        }

        /// Get a string value
        pub fn get_string(&self, key: &str) -> Option<String> {
            self.data.read().unwrap().get(key).cloned()
        }

        /// Set a string value
        pub fn set_string(&self, key: impl Into<String>, value: impl Into<String>) {
            self.data.write().unwrap().insert(key.into(), value.into());
        }

        /// Check if key exists
        pub fn contains(&self, key: &str) -> bool {
            self.data.read().unwrap().contains_key(key)
        }
    }
}

pub mod cache {
    //! Caching module

    use std::collections::HashMap;
    use std::sync::RwLock;

    /// Simple in-memory cache
    #[derive(Debug, Default)]
    pub struct Cache<K, V> {
        data: RwLock<HashMap<K, V>>,
    }

    impl<K: std::hash::Hash + Eq + Clone, V: Clone> Cache<K, V> {
        /// Create new cache
        pub fn new() -> Self {
            Self::default()
        }

        /// Get value
        pub fn get(&self, key: &K) -> Option<V> {
            self.data.read().unwrap().get(key).cloned()
        }

        /// Set value
        pub fn set(&self, key: K, value: V) {
            self.data.write().unwrap().insert(key, value);
        }

        /// Remove value
        pub fn remove(&self, key: &K) -> Option<V> {
            self.data.write().unwrap().remove(key)
        }

        /// Clear cache
        pub fn clear(&self) {
            self.data.write().unwrap().clear();
        }
    }
}

pub mod error {
    //! Error handling

    use thiserror::Error;

    #[derive(Error, Debug)]
    pub enum Error {
        #[error("Configuration error: {0}")]
        Config(String),

        #[error("Cache error: {0}")]
        Cache(String),

        #[error("HTTP error: {0}")]
        Http(String),

        #[error("IO error: {0}")]
        Io(#[from] std::io::Error),
    }

    pub type Result<T> = std::result::Result<T, Error>;
}

pub mod http {
    //! HTTP client module

    use anyhow::Result;

    /// HTTP client wrapper
    #[derive(Debug, Default)]
    pub struct HttpClient {
        base_url: Option<String>,
    }

    impl HttpClient {
        /// Create new HTTP client
        pub fn new() -> Self {
            Self::default()
        }

        /// Set base URL
        pub fn with_base_url(mut self, url: impl Into<String>) -> Self {
            self.base_url = Some(url.into());
            self
        }

        /// GET request
        pub async fn get(&self, url: &str) -> Result<String> {
            let client = reqwest::Client::new();
            let full_url = if let Some(base) = &self.base_url {
                format!("{}/{}", base, url)
            } else {
                url.to_string()
            };

            let resp = client.get(&full_url).send().await?;
            let text = resp.text().await?;
            Ok(text)
        }

        /// POST request
        pub async fn post(&self, url: &str, body: impl serde::Serialize) -> Result<String> {
            let client = reqwest::Client::new();
            let full_url = if let Some(base) = &self.base_url {
                format!("{}/{}", base, url)
            } else {
                url.to_string()
            };

            let resp = client.post(&full_url).json(&body).send().await?;
            let text = resp.text().await?;
            Ok(text)
        }
    }
}
