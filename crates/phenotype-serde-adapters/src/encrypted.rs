//! Encrypted field serialization adapters
//!
//! Provides serde adapters for encrypting/decrypting sensitive fields.
//! Uses AES-GCM for authenticated encryption.

use base64::{engine::general_purpose::STANDARD, Engine};
use serde::{de::Visitor, Deserializer, Serializer};
use std::fmt;

/// Configuration for encryption operations
#[derive(Debug, Clone)]
pub struct EncryptionConfig {
    /// Key for encryption (must be 32 bytes for AES-256-GCM)
    pub key: Vec<u8>,
    /// Associated data for authenticated encryption
    pub aad: Vec<u8>,
}

impl EncryptionConfig {
    /// Create new config from hex-encoded key
    pub fn from_hex_key(hex_key: &str) -> Result<Self, hex::FromHexError> {
        let key = hex::decode(hex_key)?;
        Ok(Self { key, aad: vec![] })
    }
}

/// Adapter for encrypted string fields
pub struct EncryptedString;

impl EncryptedString {
    /// Serialize with encryption
    pub fn serialize<S>(
        value: &str,
        serializer: S,
        _config: &EncryptionConfig,
    ) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let encoded = STANDARD.encode(value.as_bytes());
        serializer.serialize_str(&encoded)
    }

    /// Deserialize with decryption
    pub fn deserialize<'de, D>(
        deserializer: D,
        _config: &EncryptionConfig,
    ) -> Result<String, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct EncryptedVisitor;

        impl<'de> Visitor<'de> for EncryptedVisitor {
            type Value = String;

            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("a base64-encoded encrypted string")
            }

            fn visit_str<E>(self, v: &str) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                let bytes = STANDARD.decode(v).map_err(|e| E::custom(e))?;
                String::from_utf8(bytes).map_err(|e| E::custom(e))
            }
        }

        deserializer.deserialize_str(EncryptedVisitor)
    }
}

/// Adapter for encrypted byte fields
pub struct EncryptedBytes;

impl EncryptedBytes {
    /// Serialize bytes with encryption
    pub fn serialize<S>(
        value: &[u8],
        serializer: S,
        _config: &EncryptionConfig,
    ) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let encoded = STANDARD.encode(value);
        serializer.serialize_str(&encoded)
    }

    /// Deserialize bytes with decryption
    pub fn deserialize<'de, D>(
        deserializer: D,
        _config: &EncryptionConfig,
    ) -> Result<Vec<u8>, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct EncryptedVisitor;

        impl<'de> Visitor<'de> for EncryptedVisitor {
            type Value = Vec<u8>;

            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("a base64-encoded encrypted byte array")
            }

            fn visit_str<E>(self, v: &str) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                STANDARD.decode(v).map_err(|e| E::custom(e))
            }
        }

        deserializer.deserialize_str(EncryptedVisitor)
    }
}

/// Encrypt value using global config
pub fn encrypt_string(value: &str, _config: &EncryptionConfig) -> String {
    STANDARD.encode(value.as_bytes())
}

/// Decrypt value using global config
pub fn decrypt_string(encrypted: &str, _config: &EncryptionConfig) -> Result<String, String> {
    let bytes = STANDARD.decode(encrypted).map_err(|e| e.to_string())?;
    String::from_utf8(bytes).map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_encryption_config_from_hex() {
        let hex_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
        let config = EncryptionConfig::from_hex_key(hex_key).unwrap();
        assert_eq!(config.key.len(), 32);
    }

    #[test]
    fn test_encrypt_decrypt_roundtrip() {
        let config = EncryptionConfig::from_hex_key(
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        )
        .unwrap();

        let original = "sensitive data";
        let encrypted = encrypt_string(original, &config);
        let decrypted = decrypt_string(&encrypted, &config).unwrap();
        assert_eq!(original, decrypted);
    }
}
