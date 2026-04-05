//! Hex encoding wrapper for byte arrays

use serde::{de::Visitor, Deserializer, Serializer};

/// Adapter for hex-encoded byte arrays
pub struct Hex;

impl Hex {
    /// Serialize bytes as hex string
    pub fn serialize<S>(value: &[u8], serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&hex::encode(value))
    }

    /// Deserialize hex string to bytes
    pub fn deserialize<'de, D>(deserializer: D) -> Result<Vec<u8>, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct HexVisitor;

        impl<'de> Visitor<'de> for HexVisitor {
            type Value = Vec<u8>;

            fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
                formatter.write_str("a hex-encoded string")
            }

            fn visit_str<E>(self, v: &str) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                hex::decode(v).map_err(|e| E::custom(e))
            }
        }

        deserializer.deserialize_str(HexVisitor)
    }
}

/// Serialize Vec<u8> as hex
pub fn serialize<S>(value: &[u8], serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    Hex::serialize(value, serializer)
}

/// Deserialize hex string to Vec<u8>
pub fn deserialize<'de, D>(deserializer: D) -> Result<Vec<u8>, D::Error>
where
    D: Deserializer<'de>,
{
    Hex::deserialize(deserializer)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::{Deserialize, Serialize};

    #[derive(Serialize, Deserialize, Debug, PartialEq)]
    struct TestData {
        #[serde(with = "crate::hex_wrapper")]
        data: Vec<u8>,
    }

    #[test]
    fn test_hex_roundtrip() {
        let data = TestData {
            data: vec![1, 2, 3, 4, 255],
        };
        let json = serde_json::to_string(&data).unwrap();
        assert!(json.contains("01020304ff"));

        let decoded: TestData = serde_json::from_str(&json).unwrap();
        assert_eq!(data.data, decoded.data);
    }
}
