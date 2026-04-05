//! # Phenotype Serde Adapters
//!
//! Serialization adapters for common patterns:
//! - Encrypted field serialization
//! - MessagePack serialization
//! - Lenient JSON parsing
//! - Base64/hex encoding wrappers
//!
//! ## Example
//!
//! ```rust
//! use phenotype_serde_adapters::EncryptedString;
//! use serde::{Serialize, Deserialize};
//!
//! #[derive(Serialize, Deserialize)]
//! struct User {
//!     name: String,
//!     #[serde(with = "EncryptedString")]
//!     ssn: String,
//! }
//! ```

use serde::{Deserialize, Deserializer, Serialize, Serializer};
use std::marker::PhantomData;

pub mod base64_wrapper;
pub mod encrypted;
pub mod hex_wrapper;
pub mod lenient;
pub mod messagepack;
pub mod timestamp;

pub use base64_wrapper::Base64;
pub use encrypted::{EncryptedBytes, EncryptedString, EncryptionConfig};
pub use hex_wrapper::Hex;
pub use lenient::{lenient_bool, lenient_number, LenientJson};
pub use messagepack::{from_messagepack, to_messagepack, MessagePack};
pub use timestamp::{DurationSeconds, TimestampMillis, TimestampSeconds};

/// Trait for serializable content hash
pub trait ContentHash {
    /// Compute content hash for this value
    fn content_hash(&self) -> String;
}

/// Generic adapter for custom serialization
pub struct SerializeAdapter<T, F, G>
where
    F: Fn(&T) -> Result<serde_json::Value, serde_json::Error>,
    G: Fn(&serde_json::Value) -> Result<T, serde_json::Error>,
{
    _phantom: PhantomData<(T, F, G)>,
}

impl<T, F, G> SerializeAdapter<T, F, G>
where
    F: Fn(&T) -> Result<serde_json::Value, serde_json::Error>,
    G: Fn(&serde_json::Value) -> Result<T, serde_json::Error>,
{
    /// Serialize with custom function
    pub fn serialize<S>(value: &T, serializer: S, f: F) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let json_value = f(value).map_err(serde::ser::Error::custom)?;
        json_value.serialize(serializer)
    }

    /// Deserialize with custom function
    pub fn deserialize<'de, D>(deserializer: D, g: G) -> Result<T, D::Error>
    where
        D: Deserializer<'de>,
    {
        let json_value = serde_json::Value::deserialize(deserializer)?;
        g(&json_value).map_err(serde::de::Error::custom)
    }
}

/// Versioned serialization adapter
pub struct Versioned<T> {
    version: u32,
    data: T,
}

impl<T> Versioned<T> {
    /// Create new versioned data
    pub fn new(version: u32, data: T) -> Self {
        Self { version, data }
    }

    /// Get version
    pub fn version(&self) -> u32 {
        self.version
    }

    /// Get data
    pub fn data(&self) -> &T {
        &self.data
    }

    /// Consume and get data
    pub fn into_data(self) -> T {
        self.data
    }
}

impl<T: Serialize> Serialize for Versioned<T> {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        use serde::ser::SerializeStruct;
        let mut state = serializer.serialize_struct("Versioned", 2)?;
        state.serialize_field("version", &self.version)?;
        state.serialize_field("data", &self.data)?;
        state.end()
    }
}

impl<'de, T: Deserialize<'de>> Deserialize<'de> for Versioned<T> {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        use serde::de::MapAccess;
        struct VersionedVisitor<T>(PhantomData<T>);

        impl<'de, T: Deserialize<'de>> serde::de::Visitor<'de> for VersionedVisitor<T> {
            type Value = Versioned<T>;

            fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
                formatter.write_str("struct Versioned with version and data fields")
            }

            fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
            where
                A: MapAccess<'de>,
            {
                let mut version = None;
                let mut data = None;

                while let Some(key) = map.next_key::<String>()? {
                    match key.as_str() {
                        "version" => {
                            if version.is_some() {
                                return Err(serde::de::Error::duplicate_field("version"));
                            }
                            version = Some(map.next_value()?);
                        }
                        "data" => {
                            if data.is_some() {
                                return Err(serde::de::Error::duplicate_field("data"));
                            }
                            data = Some(map.next_value()?);
                        }
                        _ => {
                            map.next_value::<serde::de::IgnoredAny>()?;
                        }
                    }
                }

                let version = version.ok_or_else(|| serde::de::Error::missing_field("version"))?;
                let data = data.ok_or_else(|| serde::de::Error::missing_field("data"))?;
                Ok(Versioned { version, data })
            }
        }

        deserializer.deserialize_struct(
            "Versioned",
            &["version", "data"],
            VersionedVisitor(PhantomData),
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_versioned_roundtrip() {
        let original = Versioned::new(1, "hello".to_string());
        let json = serde_json::to_string(&original).unwrap();
        let decoded: Versioned<String> = serde_json::from_str(&json).unwrap();
        assert_eq!(decoded.version, 1);
        assert_eq!(decoded.data, "hello");
    }
}
