//! Timestamp serialization adapters
//!
//! Provides adapters for serializing chrono DateTime and Duration
//! as seconds, milliseconds, or ISO 8601 strings.

use chrono::{DateTime, Duration, TimeZone, Utc};
use serde::{de::Visitor, Deserializer, Serializer};

/// Serialize DateTime as Unix timestamp (seconds)
pub struct TimestampSeconds;

impl TimestampSeconds {
    pub fn serialize<S>(dt: &DateTime<Utc>, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_i64(dt.timestamp())
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<DateTime<Utc>, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct TimestampVisitor;

        impl<'de> Visitor<'de> for TimestampVisitor {
            type Value = DateTime<Utc>;

            fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
                formatter.write_str("a unix timestamp in seconds")
            }

            fn visit_i64<E>(self, v: i64) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                Utc.timestamp_opt(v, 0)
                    .single()
                    .ok_or_else(|| E::custom("invalid timestamp"))
            }

            fn visit_u64<E>(self, v: u64) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                Utc.timestamp_opt(v as i64, 0)
                    .single()
                    .ok_or_else(|| E::custom("invalid timestamp"))
            }
        }

        deserializer.deserialize_i64(TimestampVisitor)
    }
}

/// Serialize DateTime as Unix timestamp (milliseconds)
pub struct TimestampMillis;

impl TimestampMillis {
    pub fn serialize<S>(dt: &DateTime<Utc>, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_i64(dt.timestamp_millis())
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<DateTime<Utc>, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct TimestampVisitor;

        impl<'de> Visitor<'de> for TimestampVisitor {
            type Value = DateTime<Utc>;

            fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
                formatter.write_str("a unix timestamp in milliseconds")
            }

            fn visit_i64<E>(self, v: i64) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                Utc.timestamp_millis_opt(v)
                    .single()
                    .ok_or_else(|| E::custom("invalid timestamp"))
            }

            fn visit_u64<E>(self, v: u64) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                Utc.timestamp_millis_opt(v as i64)
                    .single()
                    .ok_or_else(|| E::custom("invalid timestamp"))
            }
        }

        deserializer.deserialize_i64(TimestampVisitor)
    }
}

/// Serialize Duration as seconds (f64 for sub-second precision)
pub struct DurationSeconds;

impl DurationSeconds {
    pub fn serialize<S>(duration: &Duration, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let seconds =
            duration.num_seconds() as f64 + (duration.subsec_nanos() as f64 / 1_000_000_000.0);
        serializer.serialize_f64(seconds)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<Duration, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct DurationVisitor;

        impl<'de> Visitor<'de> for DurationVisitor {
            type Value = Duration;

            fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
                formatter.write_str("duration in seconds")
            }

            fn visit_f64<E>(self, v: f64) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                let secs = v as i64;
                let nanos = ((v - secs as f64) * 1_000_000_000.0) as i32;
                Ok(Duration::seconds(secs) + Duration::nanoseconds(nanos as i64))
            }

            fn visit_i64<E>(self, v: i64) -> Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                Ok(Duration::seconds(v))
            }
        }

        deserializer.deserialize_any(DurationVisitor)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::{Deserialize, Serialize};

    #[derive(Serialize, Deserialize, Debug, PartialEq)]
    struct Event {
        name: String,
        #[serde(with = "TimestampSeconds")]
        timestamp: DateTime<Utc>,
    }

    #[test]
    fn test_timestamp_seconds_roundtrip() {
        let event = Event {
            name: "test".to_string(),
            timestamp: Utc::now(),
        };
        let json = serde_json::to_string(&event).unwrap();
        let decoded: Event = serde_json::from_str(&json).unwrap();
        // Allow small time difference due to truncation
        assert_eq!(event.timestamp.timestamp(), decoded.timestamp.timestamp());
    }
}
