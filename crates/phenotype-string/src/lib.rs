//! Phenotype string utilities
//!
//! Common string manipulation helpers for the Phenotype ecosystem.

/// Truncate a string to a maximum length, adding ellipsis if truncated
pub fn truncate(s: &str, max_len: usize) -> String {
    if s.chars().count() <= max_len {
        s.to_string()
    } else {
        let truncated: String = s.chars().take(max_len.saturating_sub(3)).collect();
        format!("{}...", truncated)
    }
}

/// Convert a string to snake_case
pub fn to_snake_case(s: &str) -> String {
    let mut result = String::new();
    let mut prev_is_lower = false;

    for ch in s.chars() {
        if ch.is_uppercase() {
            if prev_is_lower {
                result.push('_');
            }
            result.push(ch.to_ascii_lowercase());
            prev_is_lower = false;
        } else {
            result.push(ch);
            prev_is_lower = ch.is_lowercase();
        }
    }

    result
}

/// Convert a string to camelCase
pub fn to_camel_case(s: &str) -> String {
    let mut result = String::new();
    let mut capitalize_next = false;

    for ch in s.chars() {
        if ch == '_' || ch == '-' || ch == ' ' {
            capitalize_next = true;
        } else if capitalize_next {
            result.push(ch.to_ascii_uppercase());
            capitalize_next = false;
        } else {
            result.push(ch);
        }
    }

    result
}

/// Check if a string is a valid identifier (alphanumeric + underscore, starts with letter)
pub fn is_valid_identifier(s: &str) -> bool {
    if s.is_empty() {
        return false;
    }

    let mut chars = s.chars();
    let first = chars.next().unwrap();
    if !first.is_alphabetic() && first != '_' {
        return false;
    }

    chars.all(|c| c.is_alphanumeric() || c == '_')
}

/// Indent each line of a string by the given number of spaces
pub fn indent(s: &str, spaces: usize) -> String {
    let prefix = " ".repeat(spaces);
    s.lines()
        .map(|line| format!("{}{}", prefix, line))
        .collect::<Vec<_>>()
        .join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_truncate_short_string() {
        assert_eq!(truncate("hello", 10), "hello");
    }

    #[test]
    fn test_truncate_long_string() {
        // max_len=10, we take 7 chars + "..." = 10 chars total
        assert_eq!(truncate("hello world this is long", 10), "hello w...");
    }

    #[test]
    fn test_to_snake_case() {
        assert_eq!(to_snake_case("HelloWorld"), "hello_world");
        assert_eq!(to_snake_case("Hello"), "hello");
    }

    #[test]
    fn test_to_camel_case() {
        assert_eq!(to_camel_case("hello_world"), "helloWorld");
        assert_eq!(to_camel_case("hello-world"), "helloWorld");
    }

    #[test]
    fn test_is_valid_identifier() {
        assert!(is_valid_identifier("hello"));
        assert!(is_valid_identifier("_hello"));
        assert!(is_valid_identifier("hello_world"));
        assert!(!is_valid_identifier("123"));
        assert!(!is_valid_identifier(""));
    }

    #[test]
    fn test_indent() {
        assert_eq!(indent("line1\nline2", 2), "  line1\n  line2");
    }
}
