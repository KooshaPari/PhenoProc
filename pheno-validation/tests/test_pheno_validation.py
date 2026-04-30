"""Tests for pheno_validation package."""

import pytest
from dataclasses import dataclass

from pheno_validation import (
    Validate,
    ValidationError,
    ValidationErrors,
    Validator,
    Rule,
    rule,
    validate_all,
    ValidatedDataclass,
)


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error_str(self) -> None:
        """Test string representation of ValidationError."""
        error = ValidationError("email", "Invalid email format")
        assert str(error) == "Validation error on field 'email': Invalid email format"

    def test_validation_error_equality(self) -> None:
        """Test ValidationError equality."""
        error1 = ValidationError("email", "Invalid email format")
        error2 = ValidationError("email", "Invalid email format")
        error3 = ValidationError("name", "Invalid email format")
        assert error1 == error2
        assert error1 != error3


class TestValidationErrors:
    """Tests for ValidationErrors collection."""

    def test_empty_errors(self) -> None:
        """Test empty ValidationErrors."""
        errors = ValidationErrors()
        assert errors.is_empty()
        assert len(errors) == 0
        assert not errors

    def test_add_error(self) -> None:
        """Test adding errors."""
        errors = ValidationErrors()
        errors.add(ValidationError("email", "Invalid"))
        assert not errors.is_empty()
        assert len(errors) == 1
        assert bool(errors)

    def test_iteration(self) -> None:
        """Test iterating over errors."""
        errors = ValidationErrors()
        errors.add(ValidationError("email", "Invalid"))
        errors.add(ValidationError("name", "Required"))
        error_list = list(errors)
        assert len(error_list) == 2
        assert error_list[0].field == "email"
        assert error_list[1].field == "name"

    def test_for_field(self) -> None:
        """Test filtering errors by field."""
        errors = ValidationErrors()
        errors.add(ValidationError("email", "Invalid"))
        errors.add(ValidationError("email", "Too long"))
        errors.add(ValidationError("name", "Required"))
        email_errors = errors.for_field("email")
        assert len(email_errors) == 2
        name_errors = errors.for_field("name")
        assert len(name_errors) == 1


class TestValidator:
    """Tests for Validator class."""

    def test_valid_email(self) -> None:
        """Test valid email passes validation."""
        Validator.email("test@example.com")
        Validator.email("user.name+tag@domain.co.uk")

    def test_invalid_email(self) -> None:
        """Test invalid email raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.email("invalid")
        assert exc_info.value.field == "email"
        assert "Invalid email format" in exc_info.value.message

    def test_email_non_string(self) -> None:
        """Test non-string email raises ValidationError."""
        with pytest.raises(ValidationError):
            Validator.email(123)

    def test_valid_url(self) -> None:
        """Test valid URL passes validation."""
        Validator.url("https://example.com")
        Validator.url("http://localhost:8080")

    def test_invalid_url(self) -> None:
        """Test invalid URL raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.url("not-a-url")
        assert exc_info.value.field == "url"

    def test_valid_uuid(self) -> None:
        """Test valid UUID passes validation."""
        Validator.uuid("550e8400-e29b-41d4-a716-446655440000")

    def test_invalid_uuid(self) -> None:
        """Test invalid UUID raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.uuid("not-a-uuid")
        assert exc_info.value.field == "uuid"

    def test_not_empty_valid(self) -> None:
        """Test non-empty string passes."""
        Validator.not_empty("hello", "field")

    def test_not_empty_invalid(self) -> None:
        """Test empty/whitespace string fails."""
        with pytest.raises(ValidationError):
            Validator.not_empty("", "field")
        with pytest.raises(ValidationError):
            Validator.not_empty("   ", "field")

    def test_min_length_valid(self) -> None:
        """Test string meets minimum length."""
        Validator.min_length("hello", 3, "field")
        Validator.min_length("hi", 2, "field")

    def test_min_length_invalid(self) -> None:
        """Test string below minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.min_length("hi", 5, "field")
        assert "at least 5 characters" in exc_info.value.message

    def test_max_length_valid(self) -> None:
        """Test string within maximum length."""
        Validator.max_length("hello", 10, "field")

    def test_max_length_invalid(self) -> None:
        """Test string exceeds maximum length."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.max_length("hello world", 5, "field")
        assert "at most 5 characters" in exc_info.value.message

    def test_range_valid(self) -> None:
        """Test number within range."""
        Validator.range(50, 0, 100, "field")
        Validator.range(0, 0, 100, "field")
        Validator.range(100, 0, 100, "field")

    def test_range_too_low(self) -> None:
        """Test number below range."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.range(-5, 0, 100, "field")
        assert "at least 0" in exc_info.value.message

    def test_range_too_high(self) -> None:
        """Test number above range."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.range(150, 0, 100, "field")
        assert "at most 100" in exc_info.value.message

    def test_one_of_valid(self) -> None:
        """Test value in allowed choices."""
        Validator.one_of("red", ["red", "green", "blue"], "color")
        Validator.one_of(1, [1, 2, 3], "number")

    def test_one_of_invalid(self) -> None:
        """Test value not in allowed choices."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.one_of("yellow", ["red", "green", "blue"], "color")
        assert "Must be one of" in exc_info.value.message

    def test_regex_valid(self) -> None:
        """Test string matches pattern."""
        Validator.regex("hello123", r"^[a-z]+[0-9]+$", "field")

    def test_regex_invalid(self) -> None:
        """Test string doesn't match pattern."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.regex("123hello", r"^[a-z]+[0-9]+$", "field")
        assert "Does not match pattern" in exc_info.value.message

    def test_starts_with_valid(self) -> None:
        """Test string starts with prefix."""
        Validator.starts_with("hello", "he", "field")

    def test_starts_with_invalid(self) -> None:
        """Test string doesn't start with prefix."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.starts_with("hello", "lo", "field")
        assert 'Must start with "lo"' in exc_info.value.message

    def test_ends_with_valid(self) -> None:
        """Test string ends with suffix."""
        Validator.ends_with("hello", "lo", "field")

    def test_ends_with_invalid(self) -> None:
        """Test string doesn't end with suffix."""
        with pytest.raises(ValidationError) as exc_info:
            Validator.ends_with("hello", "he", "field")
        assert 'Must end with "he"' in exc_info.value.message


class TestRule:
    """Tests for composable Rule class."""

    def test_rule_creation(self) -> None:
        """Test creating a rule."""

        @rule
        def is_positive(value: int) -> None:
            if value <= 0:
                raise ValidationError("value", "Must be positive")

        rule_instance = Rule(is_positive)
        rule_instance(5)  # Should not raise

    def test_rule_and(self) -> None:
        """Test combining rules with AND."""

        @rule
        def longer_than_5(value: str) -> None:
            if len(value) <= 5:
                raise ValidationError("value", "Must be longer than 5")

        @rule
        def has_uppercase(value: str) -> None:
            if not any(c.isupper() for c in value):
                raise ValidationError("value", "Must have uppercase")

        combined = Rule(longer_than_5).and_(Rule(has_uppercase))
        combined("HelloWorld")  # Should not raise

        with pytest.raises(ValidationError):
            combined("hello")  # Fails longer_than_5

    def test_rule_or(self) -> None:
        """Test combining rules with OR."""

        @rule
        def is_short(value: str) -> None:
            if len(value) >= 5:
                raise ValidationError("value", "Must be short")

        @rule
        def has_uppercase(value: str) -> None:
            if not any(c.isupper() for c in value):
                raise ValidationError("value", "Must have uppercase")

        combined = Rule(is_short).or_(Rule(has_uppercase))
        combined("hi")  # Passes is_short
        combined("HELLO")  # Passes has_uppercase

        with pytest.raises(ValidationError):
            combined("hello")  # Fails both


class TestValidateAll:
    """Tests for validate_all function."""

    def test_validate_all_passes(self) -> None:
        """Test validate_all passes when all validations pass."""
        validate_all(
            lambda: Validator.email("test@example.com"),
            lambda: Validator.range(25, 0, 150, "age"),
        )

    def test_validate_all_collects_errors(self) -> None:
        """Test validate_all collects all errors."""
        with pytest.raises(ValidationErrors) as exc_info:
            validate_all(
                lambda: Validator.email("invalid"),
                lambda: Validator.range(200, 0, 150, "age"),
            )
        errors = exc_info.value
        assert len(errors) == 2
        fields = {e.field for e in errors}
        assert fields == {"email", "age"}


class TestValidatedDataclass:
    """Tests for ValidatedDataclass."""

    def test_valid_dataclass(self) -> None:
        """Test valid dataclass passes validation."""

        @dataclass
        class User(ValidatedDataclass):
            email: str
            age: int
            name: str

            def validate(self) -> None:
                super().validate()
                validate_all(
                    lambda: Validator.email(self.email),
                    lambda: Validator.range(self.age, 0, 150, "age"),
                    lambda: Validator.not_empty(self.name, "name"),
                )

        user = User(email="test@example.com", age=25, name="Test")
        user.validate()  # Should not raise

    def test_invalid_dataclass(self) -> None:
        """Test invalid dataclass raises ValidationErrors."""

        @dataclass
        class User(ValidatedDataclass):
            email: str
            age: int

            def validate(self) -> None:
                super().validate()
                validate_all(
                    lambda: Validator.email(self.email),
                    lambda: Validator.range(self.age, 0, 150, "age"),
                )

        user = User(email="invalid", age=200)
        with pytest.raises(ValidationErrors) as exc_info:
            user.validate()
        assert len(exc_info.value) == 2

    def test_is_valid(self) -> None:
        """Test is_valid method."""

        @dataclass
        class User(ValidatedDataclass):
            email: str

            def validate(self) -> None:
                super().validate()
                Validator.email(self.email)

        valid_user = User(email="test@example.com")
        invalid_user = User(email="invalid")

        assert valid_user.is_valid() is True
        assert invalid_user.is_valid() is False

    def test_from_dict(self) -> None:
        """Test creating instance from dict."""

        @dataclass
        class User(ValidatedDataclass):
            email: str
            age: int

            def validate(self) -> None:
                super().validate()
                validate_all(
                    lambda: Validator.email(self.email),
                    lambda: Validator.range(self.age, 0, 150, "age"),
                )

        data = {"email": "test@example.com", "age": 25}
        user = User.from_dict(data)
        assert user.email == "test@example.com"
        assert user.age == 25

        invalid_data = {"email": "invalid", "age": 25}
        with pytest.raises(ValidationErrors):
            User.from_dict(invalid_data)
