"""Built-in validators for common validation scenarios."""

from __future__ import annotations

import re
from numbers import Real
from typing import Sequence, TypeVar

from pheno_validation.errors import ValidationError

T = TypeVar("T")


class Validator:
    """Collection of validation methods for common types.

    Provides static methods for validating strings, numbers,
    and other common data types.
    """

    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    UUID_PATTERN = re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )

    URL_PATTERN = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    @staticmethod
    def email(email: str) -> None:
        """Validate email format.

        Args:
            email: The email string to validate

        Raises:
            ValidationError: If email format is invalid
        """
        if not isinstance(email, str) or not Validator.EMAIL_PATTERN.match(email):
            raise ValidationError("email", "Invalid email format")

    @staticmethod
    def url(url: str) -> None:
        """Validate URL format (http/https only).

        Args:
            url: The URL string to validate

        Raises:
            ValidationError: If URL format is invalid
        """
        if not isinstance(url, str) or not Validator.URL_PATTERN.match(url):
            raise ValidationError("url", "URL must be a valid http:// or https:// URL")

    @staticmethod
    def uuid(value: str) -> None:
        """Validate UUID format.

        Args:
            value: The string to validate as UUID

        Raises:
            ValidationError: If UUID format is invalid
        """
        if not isinstance(value, str) or not Validator.UUID_PATTERN.match(value):
            raise ValidationError("uuid", "Invalid UUID format")

    @staticmethod
    def not_empty(value: str, field: str) -> None:
        """Validate string is not empty or whitespace-only.

        Args:
            value: The string to validate
            field: The field name for error reporting

        Raises:
            ValidationError: If string is empty or whitespace-only
        """
        if not isinstance(value, str) or not value or not value.strip():
            raise ValidationError(field, "Value cannot be empty")

    @staticmethod
    def min_length(value: str, min_len: int, field: str) -> None:
        """Validate minimum string length.

        Args:
            value: The string to validate
            min_len: Minimum required length
            field: The field name for error reporting

        Raises:
            ValidationError: If string is shorter than minimum
        """
        if not isinstance(value, str):
            raise ValidationError(field, f"Must be a string, got {type(value).__name__}")
        if len(value) < min_len:
            raise ValidationError(field, f"Must be at least {min_len} characters")

    @staticmethod
    def max_length(value: str, max_len: int, field: str) -> None:
        """Validate maximum string length.

        Args:
            value: The string to validate
            max_len: Maximum allowed length
            field: The field name for error reporting

        Raises:
            ValidationError: If string is longer than maximum
        """
        if not isinstance(value, str):
            raise ValidationError(field, f"Must be a string, got {type(value).__name__}")
        if len(value) > max_len:
            raise ValidationError(field, f"Must be at most {max_len} characters")

    @staticmethod
    def length(value: str, length: int, field: str) -> None:
        """Validate exact string length.

        Args:
            value: The string to validate
            length: Expected exact length
            field: The field name for error reporting

        Raises:
            ValidationError: If string length doesn't match
        """
        if not isinstance(value, str):
            raise ValidationError(field, f"Must be a string, got {type(value).__name__}")
        if len(value) != length:
            raise ValidationError(field, f"Must be exactly {length} characters")

    @staticmethod
    def range(value: Real, min_val: Real, max_val: Real, field: str) -> None:
        """Validate numeric range (inclusive).

        Args:
            value: The numeric value to validate
            min_val: Minimum allowed value (inclusive)
            max_val: Maximum allowed value (inclusive)
            field: The field name for error reporting

        Raises:
            ValidationError: If value is outside range
        """
        if not isinstance(value, Real):
            raise ValidationError(field, f"Must be a number, got {type(value).__name__}")
        if value < min_val:
            raise ValidationError(field, f"Must be at least {min_val}")
        if value > max_val:
            raise ValidationError(field, f"Must be at most {max_val}")

    @staticmethod
    def min(value: Real, min_val: Real, field: str) -> None:
        """Validate minimum value.

        Args:
            value: The numeric value to validate
            min_val: Minimum allowed value (inclusive)
            field: The field name for error reporting

        Raises:
            ValidationError: If value is below minimum
        """
        if not isinstance(value, Real):
            raise ValidationError(field, f"Must be a number, got {type(value).__name__}")
        if value < min_val:
            raise ValidationError(field, f"Must be at least {min_val}")

    @staticmethod
    def max(value: Real, max_val: Real, field: str) -> None:
        """Validate maximum value.

        Args:
            value: The numeric value to validate
            max_val: Maximum allowed value (inclusive)
            field: The field name for error reporting

        Raises:
            ValidationError: If value is above maximum
        """
        if not isinstance(value, Real):
            raise ValidationError(field, f"Must be a number, got {type(value).__name__}")
        if value > max_val:
            raise ValidationError(field, f"Must be at most {max_val}")

    @staticmethod
    def regex(value: str, pattern: str, field: str) -> None:
        """Validate string matches regex pattern.

        Args:
            value: The string to validate
            pattern: Regular expression pattern
            field: The field name for error reporting

        Raises:
            ValidationError: If string doesn't match pattern
        """
        if not isinstance(value, str):
            raise ValidationError(field, f"Must be a string, got {type(value).__name__}")
        if not re.match(pattern, value):
            raise ValidationError(field, f"Does not match pattern: {pattern}")

    @staticmethod
    def one_of(value: T, choices: Sequence[T], field: str) -> None:
        """Validate value is one of allowed choices.

        Args:
            value: The value to validate
            choices: Sequence of allowed values
            field: The field name for error reporting

        Raises:
            ValidationError: If value is not in choices
        """
        if value not in choices:
            choices_str = ", ".join(map(str, choices))
            raise ValidationError(field, f"Must be one of: {choices_str}")

    @staticmethod
    def pattern(value: str, pattern: str, field: str) -> None:
        """Validate string matches regex pattern (alias for regex).

        Args:
            value: The string to validate
            pattern: Regular expression pattern
            field: The field name for error reporting

        Raises:
            ValidationError: If string doesn't match pattern
        """
        Validator.regex(value, pattern, field)

    @staticmethod
    def includes(value: str, substring: str, field: str) -> None:
        """Validate string contains substring.

        Args:
            value: The string to validate
            substring: Substring that must be present
            field: The field name for error reporting

        Raises:
            ValidationError: If substring is not found
        """
        if not isinstance(value, str):
            raise ValidationError(field, f"Must be a string, got {type(value).__name__}")
        if substring not in value:
            raise ValidationError(field, f'Must include "{substring}"')

    @staticmethod
    def excludes(value: str, substring: str, field: str) -> None:
        """Validate string does not contain substring.

        Args:
            value: The string to validate
            substring: Substring that must NOT be present
            field: The field name for error reporting

        Raises:
            ValidationError: If substring is found
        """
        if not isinstance(value, str):
            raise ValidationError(field, f"Must be a string, got {type(value).__name__}")
        if substring in value:
            raise ValidationError(field, f'Must not include "{substring}"')

    @staticmethod
    def starts_with(value: str, prefix: str, field: str) -> None:
        """Validate string starts with prefix.

        Args:
            value: The string to validate
            prefix: Required prefix
            field: The field name for error reporting

        Raises:
            ValidationError: If string doesn't start with prefix
        """
        if not isinstance(value, str):
            raise ValidationError(field, f"Must be a string, got {type(value).__name__}")
        if not value.startswith(prefix):
            raise ValidationError(field, f'Must start with "{prefix}"')

    @staticmethod
    def ends_with(value: str, suffix: str, field: str) -> None:
        """Validate string ends with suffix.

        Args:
            value: The string to validate
            suffix: Required suffix
            field: The field name for error reporting

        Raises:
            ValidationError: If string doesn't end with suffix
        """
        if not isinstance(value, str):
            raise ValidationError(field, f"Must be a string, got {type(value).__name__}")
        if not value.endswith(suffix):
            raise ValidationError(field, f'Must end with "{suffix}"')
