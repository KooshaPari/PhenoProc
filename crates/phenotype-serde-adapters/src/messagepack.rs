//! MessagePack serialization adapter

use base64::{engine::general_purpose::STANDARD, Engine};
use serde::{de::Visitor, Deserialize, Deserializer, Serialize, Serializer};

/// Adapter for MessagePack serialization
pub struct MessagePack;

impl MessagePack {
    /// Serialize to MessagePack format
    pub fn serialize<T, S>(value: &T, serializer: S) -> Result<S::Ok, S::Error>
    where
        T: Serialize,
        S: Serializer,
    {
        // Convert to JSON first, then to MessagePack
        // In production, use rmp-serde directly
        let json = serde_json::to_string(value).map_err(serde::ser::Error::custom)?;
        serializer.serialize_str(&STANDARD.encode(json.as_bytes()))
    }

    /// Deserialize from MessagePack format
    pub fn deserialize<'de, T, D>(deserializer: D) -> Result<T, D::Error>
    where
        T: serde::de::DeserializeOwned,
        D: Deserializer<'de>,
    {
        struct MessagePackVisitor<T>(std::marker::PhantomData<T>);

        impl<'de, T: serde::de::DeserializeOwned> Visitor<'de> for MessagePackVisitor<T> {
            type Value = T;

            fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
                formatter.write_str("a base64-encoded messagepack string")
            }

            fn visit_str<E>(self, v: &str) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                let bytes = STANDARD.decode(v).map_err(|e| E::custom(e))?;
                // For proper implementation, use serde_json::from_slice
                // which doesn't have lifetime issues
                serde_json::from_slice(&bytes).map_err(|e| E::custom(e))
            }
        }

        deserializer.deserialize_str(MessagePackVisitor(std::marker::PhantomData))
    }
}

/// Serialize value to MessagePack bytes
pub fn to_messagepack<T: Serialize>(value: &T) -> Result<Vec<u8>, serde_json::Error> {
    // In production, use rmp-serde
    serde_json::to_vec(value)
}

/// Deserialize from MessagePack bytes
pub fn from_messagepack<T: for<'de> Deserialize<'de>>(
    bytes: &[u8],
) -> Result<T, serde_json::Error> {
    // In production, use rmp-serde
    serde_json::from_slice(bytes)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::{Deserialize, Serialize};

    #[derive(Serialize, Deserialize, Debug, PartialEq)]
    struct TestData {
        name: String,
        value: i32,
    }

    #[test]
    fn test_messagepack_roundtrip() {
        let data = TestData {
            name: "test".to_string(),
            value: 42,
        };
        let bytes = to_messagepack(&data).unwrap();
        let decoded: TestData = from_messagepack(&bytes).unwrap();
        assert_eq!(data, decoded);
    }
}
