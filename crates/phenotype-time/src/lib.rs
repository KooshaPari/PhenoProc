//! # Phenotype Time
//!
//! Time utilities and helpers for common operations.
//!
//! ## Features
//!
//! - Clock abstraction for testability
//! - Duration formatting
//! - Rate limiting helpers
//! - Timestamp manipulation

use chrono::{DateTime, Duration, NaiveDate, TimeZone, Utc};
use std::time::SystemTime;

/// Clock trait for testable time
pub trait Clock {
    /// Get current time as UTC DateTime
    fn now(&self) -> DateTime<Utc>;

    /// Get current timestamp (seconds since epoch)
    fn now_timestamp(&self) -> i64 {
        self.now().timestamp()
    }
}

/// System clock implementation
pub struct SystemClock;

impl Clock for SystemClock {
    fn now(&self) -> DateTime<Utc> {
        Utc::now()
    }
}

/// Mock clock for testing
pub struct MockClock {
    current_time: DateTime<Utc>,
}

impl MockClock {
    /// Create a new mock clock at a specific time
    pub fn at(year: i32, month: u32, day: u32, hour: u32, minute: u32, second: u32) -> Self {
        let dt = Utc
            .with_ymd_and_hms(year, month, day, hour, minute, second)
            .single()
            .expect("Invalid date/time");
        Self { current_time: dt }
    }

    /// Create at epoch
    pub fn at_epoch() -> Self {
        Self {
            current_time: DateTime::UNIX_EPOCH.into(),
        }
    }

    /// Advance time by duration
    pub fn advance(&mut self, duration: Duration) {
        self.current_time += duration;
    }

    /// Set to specific time
    pub fn set(&mut self, time: DateTime<Utc>) {
        self.current_time = time;
    }
}

impl Clock for MockClock {
    fn now(&self) -> DateTime<Utc> {
        self.current_time
    }
}

/// Format duration in human-readable form
pub fn format_duration(duration: Duration) -> String {
    let secs = duration.num_seconds();

    if secs < 60 {
        format!("{}s", secs)
    } else if secs < 3600 {
        format!("{}m {}s", secs / 60, secs % 60)
    } else if secs < 86400 {
        format!("{}h {}m", secs / 3600, (secs % 3600) / 60)
    } else {
        format!("{}d {}h", secs / 86400, (secs % 86400) / 3600)
    }
}

/// Format duration with milliseconds
pub fn format_duration_millis(duration: std::time::Duration) -> String {
    let secs = duration.as_secs();
    let millis = duration.subsec_millis();

    if secs == 0 {
        format!("{}ms", millis)
    } else {
        format!("{}.{}s", secs, millis)
    }
}

/// Parse duration from string (e.g., "1h30m", "2d")
pub fn parse_duration(s: &str) -> Option<Duration> {
    let mut total_seconds = 0i64;
    let mut current_num = String::new();

    for c in s.chars() {
        if c.is_ascii_digit() {
            current_num.push(c);
        } else {
            let num: i64 = current_num.parse().ok()?;
            current_num.clear();

            total_seconds += match c {
                's' => num,
                'm' => num * 60,
                'h' => num * 3600,
                'd' => num * 86400,
                'w' => num * 604800,
                _ => return None,
            };
        }
    }

    if total_seconds > 0 {
        Some(Duration::seconds(total_seconds))
    } else {
        None
    }
}

/// Rate limiter using token bucket algorithm
pub struct RateLimiter {
    tokens: f64,
    max_tokens: f64,
    refill_rate: f64, // tokens per second
    last_refill: DateTime<Utc>,
}

impl RateLimiter {
    /// Create a new rate limiter
    pub fn new(max_tokens: f64, refill_rate: f64) -> Self {
        Self {
            tokens: max_tokens,
            max_tokens,
            refill_rate,
            last_refill: Utc::now(),
        }
    }

    /// Try to consume tokens
    pub fn try_consume(&mut self, amount: f64) -> bool {
        self.refill();

        if self.tokens >= amount {
            self.tokens -= amount;
            true
        } else {
            false
        }
    }

    /// Refill tokens based on elapsed time
    fn refill(&mut self) {
        let now = Utc::now();
        let elapsed = (now - self.last_refill).num_milliseconds() as f64 / 1000.0;
        let tokens_to_add = elapsed * self.refill_rate;

        self.tokens = (self.tokens + tokens_to_add).min(self.max_tokens);
        self.last_refill = now;
    }

    /// Get current token count
    pub fn tokens(&self) -> f64 {
        self.tokens
    }
}

/// Convert SystemTime to DateTime<Utc>
pub fn system_time_to_datetime(st: SystemTime) -> DateTime<Utc> {
    let duration = st
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap_or_default();
    Utc.timestamp_opt(duration.as_secs() as i64, duration.subsec_nanos())
        .single()
        .unwrap_or_else(|| Utc::now())
}

/// Convert DateTime<Utc> to SystemTime
pub fn datetime_to_system_time(dt: DateTime<Utc>) -> SystemTime {
    let duration = std::time::Duration::new(dt.timestamp() as u64, dt.timestamp_subsec_nanos());
    SystemTime::UNIX_EPOCH + duration
}

/// Check if date is within range (inclusive)
pub fn is_date_in_range(date: NaiveDate, start: NaiveDate, end: NaiveDate) -> bool {
    date >= start && date <= end
}

/// Get start of day for a datetime
pub fn start_of_day(dt: DateTime<Utc>) -> DateTime<Utc> {
    dt.date_naive()
        .and_hms_opt(0, 0, 0)
        .and_then(|naive| Utc.from_local_datetime(&naive).single())
        .unwrap_or(dt)
}

/// Get end of day for a datetime
pub fn end_of_day(dt: DateTime<Utc>) -> DateTime<Utc> {
    dt.date_naive()
        .and_hms_opt(23, 59, 59)
        .and_then(|naive| Utc.from_local_datetime(&naive).single())
        .unwrap_or(dt)
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Timelike;

    #[test]
    fn test_system_clock() {
        let clock = SystemClock;
        let now = clock.now();
        assert!(now.timestamp() > 0);
    }

    #[test]
    fn test_mock_clock() {
        let mut clock = MockClock::at(2024, 1, 15, 10, 30, 0);
        assert_eq!(
            clock.now().timestamp(),
            Utc.with_ymd_and_hms(2024, 1, 15, 10, 30, 0)
                .unwrap()
                .timestamp()
        );

        clock.advance(Duration::hours(2));
        assert_eq!(clock.now().hour(), 12);
    }

    #[test]
    fn test_format_duration() {
        assert_eq!(format_duration(Duration::seconds(30)), "30s");
        assert_eq!(format_duration(Duration::seconds(90)), "1m 30s");
        assert_eq!(format_duration(Duration::seconds(3660)), "1h 1m");
        assert_eq!(format_duration(Duration::seconds(86400)), "1d 0h");
    }

    #[test]
    fn test_parse_duration() {
        assert_eq!(parse_duration("30s"), Some(Duration::seconds(30)));
        assert_eq!(parse_duration("5m"), Some(Duration::seconds(300)));
        assert_eq!(parse_duration("2h30m"), Some(Duration::seconds(9000)));
        assert_eq!(parse_duration("1d"), Some(Duration::seconds(86400)));
        assert_eq!(parse_duration("invalid"), None);
    }

    #[test]
    fn test_rate_limiter() {
        let mut limiter = RateLimiter::new(10.0, 1.0);

        // Should be able to consume up to max
        assert!(limiter.try_consume(5.0));
        assert!(limiter.try_consume(5.0));
        assert!(!limiter.try_consume(1.0)); // Empty

        // After refill, should be able to consume again
        std::thread::sleep(std::time::Duration::from_millis(100));
        assert!(limiter.try_consume(0.1));
    }
}
