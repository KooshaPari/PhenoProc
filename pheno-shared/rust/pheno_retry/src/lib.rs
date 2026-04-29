//! pheno_retry - Part of Phenotype shared library ecosystem

pub mod config {
    //! Configuration module
}

pub mod cache {
    //! Caching module
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
    }
}
