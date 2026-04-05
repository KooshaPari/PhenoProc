//! Base64 encoding wrapper for byte arrays

use base64::{engine::general_purpose::STANDARD, Engine};
use serde::{de::Visitor, Deserializer, Serializer};

/// Adapter for base64-encoded byte arrays
pub struct Base64;

impl Base64 {
    /// Serialize bytes as base64 string
    pub fn serialize<S>(value: &[u8], serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&STANDARD.encode(value))
    }

    /// Deserialize base64 string to bytes
    pub fn deserialize<'de, D>(deserializer: D) -> Result<Vec<u8>, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct Base64Visitor;

        impl<'de> Visitor<'de> for Base64Visitor {
            type Value = Vec<u8>;

            fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
                formatter.write_str("a base64-encoded string")
            }

            fn visit_str<E>(self, v: &str) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                STANDARD.decode(v).map_err(|e| E::custom(e))
            }
        }

        deserializer.deserialize_str(Base64Visitor)
    }
}

/// Serialize Vec<u8> as base64
pub fn serialize<S>(value: &[u8], serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    Base64::serialize(value, serializer)
}

/// Deserialize base64 string to Vec<u8>
pub fn deserialize<'de, D>(deserializer: D) -> Result<Vec<u8>, D::Error>
where
    D: Deserializer<'de>,
{
    Base64::deserialize(deserializer)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::{Deserialize, Serialize};

    #[derive(Serialize, Deserialize, Debug, PartialEq)]
    struct TestData {
        #[serde(with = "crate::base64_wrapper")]
        data: Vec<u8>,
    }

    #[test]
    fn test_base64_roundtrip() {
        let data = TestData {
            data: vec![1, 2, 3, 4, 255],
        };
        let json = serde_json::to_string(&data).unwrap();
        let decoded: TestData = serde_json::from_str(&json).unwrap();
        assert_eq!(data.data, decoded.data);
    }
}
