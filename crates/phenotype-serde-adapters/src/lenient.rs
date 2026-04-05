//! Lenient JSON parsing adapter
//!
//! Allows deserializing from JSON with missing fields, extra fields,
//! and relaxed type checking (e.g., strings where numbers expected).

use serde::de::{self, Visitor};
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use std::marker::PhantomData;

/// Lenient JSON deserializer placeholder
pub struct LenientJson<T>(PhantomData<T>);

impl<T> LenientJson<T> {
    /// Deserialize with lenient parsing (placeholder)
    pub fn deserialize<'de, D>(_deserializer: D) -> Result<T, D::Error>
    where
        T: for<'a> Deserialize<'a>,
        D: Deserializer<'de>,
    {
        unimplemented!("LenientJson requires concrete implementation")
    }

    /// Standard serialization
    pub fn serialize<S>(value: &T, serializer: S) -> Result<S::Ok, S::Error>
    where
        T: Serialize,
        S: Serializer,
    {
        value.serialize(serializer)
    }
}

/// Deserialize number from string or number
pub fn lenient_number<'de, D, T>(deserializer: D) -> Result<T, D::Error>
where
    D: Deserializer<'de>,
    T: std::str::FromStr + serde::Deserialize<'de>,
    T::Err: std::fmt::Display,
{
    struct LenientNumberVisitor<T>(PhantomData<T>);

    impl<'de, T> Visitor<'de> for LenientNumberVisitor<T>
    where
        T: std::str::FromStr + serde::Deserialize<'de>,
        T::Err: std::fmt::Display,
    {
        type Value = T;

        fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
            formatter.write_str("a number or string representing a number")
        }

        fn visit_i64<E>(self, v: i64) -> Result<Self::Value, E>
        where
            E: de::Error,
        {
            let s = v.to_string();
            s.parse()
                .map_err(|e| E::custom(format!("cannot convert: {}", e)))
        }

        fn visit_u64<E>(self, v: u64) -> Result<Self::Value, E>
        where
            E: de::Error,
        {
            let s = v.to_string();
            s.parse()
                .map_err(|e| E::custom(format!("cannot convert: {}", e)))
        }

        fn visit_f64<E>(self, v: f64) -> Result<Self::Value, E>
        where
            E: de::Error,
        {
            let s = v.to_string();
            s.parse()
                .map_err(|e| E::custom(format!("cannot convert: {}", e)))
        }

        fn visit_str<E>(self, v: &str) -> Result<Self::Value, E>
        where
            E: de::Error,
        {
            v.parse()
                .map_err(|e| E::custom(format!("cannot parse '{}': {}", v, e)))
        }
    }

    deserializer.deserialize_any(LenientNumberVisitor(PhantomData))
}

/// Deserialize boolean from string or bool
pub fn lenient_bool<'de, D>(deserializer: D) -> Result<bool, D::Error>
where
    D: Deserializer<'de>,
{
    struct LenientBoolVisitor;

    impl<'de> Visitor<'de> for LenientBoolVisitor {
        type Value = bool;

        fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
            formatter.write_str("a boolean or string representing a boolean")
        }

        fn visit_bool<E>(self, v: bool) -> Result<Self::Value, E>
        where
            E: de::Error,
        {
            Ok(v)
        }

        fn visit_str<E>(self, v: &str) -> Result<Self::Value, E>
        where
            E: de::Error,
        {
            match v.to_lowercase().as_str() {
                "true" | "yes" | "1" | "on" => Ok(true),
                "false" | "no" | "0" | "off" | "" => Ok(false),
                _ => Err(E::custom(format!("cannot parse '{}' as boolean", v))),
            }
        }
    }

    deserializer.deserialize_any(LenientBoolVisitor)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::Deserialize;

    #[derive(Deserialize, Debug, PartialEq)]
    struct Config {
        #[serde(deserialize_with = "lenient_number")]
        port: u16,
        #[serde(deserialize_with = "lenient_bool", default)]
        enabled: bool,
        name: String,
    }

    #[test]
    fn test_lenient_number_from_string() {
        let json = r#"{"port": "8080", "enabled": "yes", "name": "test"}"#;
        let config: Config = serde_json::from_str(json).unwrap();
        assert_eq!(config.port, 8080);
        assert!(config.enabled);
    }

    #[test]
    fn test_lenient_bool_variations() {
        for (input, expected) in [
            ("true", true),
            ("yes", true),
            ("1", true),
            ("false", false),
            ("no", false),
            ("0", false),
            ("", false),
        ] {
            let json = format!(
                r#"{{"port": 8080, "enabled": "{}", "name": "test"}}"#,
                input
            );
            let config: Config = serde_json::from_str(&json).unwrap();
            assert_eq!(config.enabled, expected, "failed for input: {}", input);
        }
    }
}
