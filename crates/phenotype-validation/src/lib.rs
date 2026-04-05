//! # Phenotype Validation
//!
//! Validation framework for domain types with support for:
//! - Custom validation rules
//! - Email/URL/UUID validation
//! - Range validation
//! - Regex patterns
//! - Nested validation
//!
//! ## Example
//!
//! ```rust
//! use phenotype_validation::{Validate, ValidationError};
//!
//! #[derive(Debug)]
//! struct User {
//!     email: String,
//!     age: u32,
//! }
//!
//! impl Validate for User {
//!     fn validate(&self) -> Result<(), ValidationError> {
//!         if !self.email.contains('@') {
//!             return Err(ValidationError::new("email", "Invalid email format"));
//!         }
//!         if self.age < 18 {
//!             return Err(ValidationError::new("age", "Must be at least 18"));
//!         }
//!         Ok(())
//!     }
//! }
//! ```

/// Validation error with field and message
#[derive(Debug, Clone, PartialEq, thiserror::Error)]
#[error("Validation error on field '{field}': {message}")]
pub struct ValidationError {
    pub field: String,
    pub message: String,
}

impl ValidationError {
    /// Create a new validation error
    pub fn new(field: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            field: field.into(),
            message: message.into(),
        }
    }
}

/// Collection of validation errors
#[derive(Debug, Clone, PartialEq, thiserror::Error)]
#[error("Validation failed with {} errors", errors.len())]
pub struct ValidationErrors {
    pub errors: Vec<ValidationError>,
}

impl ValidationErrors {
    /// Create empty validation errors
    pub fn new() -> Self {
        Self { errors: Vec::new() }
    }

    /// Add an error
    pub fn add(&mut self, error: ValidationError) {
        self.errors.push(error);
    }

    /// Check if there are any errors
    pub fn is_empty(&self) -> bool {
        self.errors.is_empty()
    }

    /// Get errors for a specific field
    pub fn for_field(&self, field: &str) -> Vec<&ValidationError> {
        self.errors.iter().filter(|e| e.field == field).collect()
    }
}

impl Default for ValidationErrors {
    fn default() -> Self {
        Self::new()
    }
}

impl IntoIterator for ValidationErrors {
    type Item = ValidationError;
    type IntoIter = std::vec::IntoIter<ValidationError>;

    fn into_iter(self) -> Self::IntoIter {
        self.errors.into_iter()
    }
}

impl<'a> IntoIterator for &'a ValidationErrors {
    type Item = &'a ValidationError;
    type IntoIter = std::slice::Iter<'a, ValidationError>;

    fn into_iter(self) -> Self::IntoIter {
        self.errors.iter()
    }
}

/// Trait for types that can be validated
pub trait Validate {
    /// Validate this value
    fn validate(&self) -> Result<(), ValidationErrors>;

    /// Check if valid
    fn is_valid(&self) -> bool {
        self.validate().is_ok()
    }
}

/// Validator for common types
pub struct Validator;

impl Validator {
    /// Validate email format
    pub fn email(email: &str) -> Result<(), ValidationError> {
        let email_regex =
            regex::Regex::new(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$").unwrap();

        if email_regex.is_match(email) {
            Ok(())
        } else {
            Err(ValidationError::new("email", "Invalid email format"))
        }
    }

    /// Validate URL format
    pub fn url(url: &str) -> Result<(), ValidationError> {
        if url.starts_with("http://") || url.starts_with("https://") {
            Ok(())
        } else {
            Err(ValidationError::new(
                "url",
                "URL must start with http:// or https://",
            ))
        }
    }

    /// Validate UUID format
    pub fn uuid(uuid: &str) -> Result<(), ValidationError> {
        let uuid_regex = regex::Regex::new(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        )
        .unwrap();

        if uuid_regex.is_match(uuid) {
            Ok(())
        } else {
            Err(ValidationError::new("uuid", "Invalid UUID format"))
        }
    }

    /// Validate non-empty string
    pub fn not_empty(value: &str, field: &str) -> Result<(), ValidationError> {
        if value.trim().is_empty() {
            Err(ValidationError::new(field, "Value cannot be empty"))
        } else {
            Ok(())
        }
    }

    /// Validate minimum length
    pub fn min_length(value: &str, min: usize, field: &str) -> Result<(), ValidationError> {
        if value.len() < min {
            Err(ValidationError::new(
                field,
                format!("Must be at least {} characters", min),
            ))
        } else {
            Ok(())
        }
    }

    /// Validate maximum length
    pub fn max_length(value: &str, max: usize, field: &str) -> Result<(), ValidationError> {
        if value.len() > max {
            Err(ValidationError::new(
                field,
                format!("Must be at most {} characters", max),
            ))
        } else {
            Ok(())
        }
    }

    /// Validate numeric range
    pub fn range<T: PartialOrd + std::fmt::Debug>(
        value: T,
        min: T,
        max: T,
        field: &str,
    ) -> Result<(), ValidationError> {
        if value < min {
            Err(ValidationError::new(
                field,
                format!("Must be at least {:?}", min),
            ))
        } else if value > max {
            Err(ValidationError::new(
                field,
                format!("Must be at most {:?}", max),
            ))
        } else {
            Ok(())
        }
    }

    /// Validate regex pattern
    pub fn regex(value: &str, pattern: &str, field: &str) -> Result<(), ValidationError> {
        let regex = regex::Regex::new(pattern)
            .map_err(|e| ValidationError::new(field, format!("Invalid regex: {}", e)))?;

        if regex.is_match(value) {
            Ok(())
        } else {
            Err(ValidationError::new(
                field,
                format!("Does not match pattern: {}", pattern),
            ))
        }
    }
}

/// Validate multiple values and collect errors
pub fn validate_all(validations: Vec<Result<(), ValidationError>>) -> Result<(), ValidationErrors> {
    let mut errors = ValidationErrors::new();

    for validation in validations {
        if let Err(e) = validation {
            errors.add(e);
        }
    }

    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_email_validation() {
        assert!(Validator::email("test@example.com").is_ok());
        assert!(Validator::email("invalid").is_err());
        assert!(Validator::email("@example.com").is_err());
    }

    #[test]
    fn test_url_validation() {
        assert!(Validator::url("https://example.com").is_ok());
        assert!(Validator::url("http://localhost:8080").is_ok());
        assert!(Validator::url("ftp://example.com").is_err());
    }

    #[test]
    fn test_uuid_validation() {
        assert!(Validator::uuid("550e8400-e29b-41d4-a716-446655440000").is_ok());
        assert!(Validator::uuid("not-a-uuid").is_err());
    }

    #[test]
    fn test_range_validation() {
        assert!(Validator::range(50, 0, 100, "value").is_ok());
        assert!(Validator::range(-1, 0, 100, "value").is_err());
        assert!(Validator::range(101, 0, 100, "value").is_err());
    }

    #[test]
    fn test_validate_all() {
        let validations = vec![
            Validator::email("test@example.com"),
            Validator::not_empty("hello", "name"),
        ];
        assert!(validate_all(validations).is_ok());

        let validations = vec![
            Validator::email("invalid"),
            Validator::not_empty("hello", "name"),
        ];
        let result = validate_all(validations);
        assert!(result.is_err());

        if let Err(errors) = result {
            assert_eq!(errors.errors.len(), 1);
        }
    }
}
