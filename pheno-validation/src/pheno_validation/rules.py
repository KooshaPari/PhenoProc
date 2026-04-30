"""Composable validation rules."""

from __future__ import annotations

from typing import Callable, TypeVar

from pheno_validation.errors import ValidationError

T = TypeVar("T")


class Rule:
    """A composable validation rule.

    Rules can be combined using AND (`and_`) and OR (`or_`) operations
    to create complex validation logic from simple primitives.

    Example:
        @rule
        def strong_password(password: str) -> None:
            if len(password) < 8:
                raise ValidationError("password", "Must be at least 8 characters")

        combined = Rule(strong_password).and_(
            Rule(lambda p: Validator.regex(p, r"[A-Z]", "password"))
        )
    """

    def __init__(self, validator: Callable[[T], None]) -> None:
        """Initialize a Rule with a validator function.

        Args:
            validator: A callable that raises ValidationError on failure
        """
        self._validator = validator

    def __call__(self, value: T) -> None:
        """Execute the rule's validation.

        Args:
            value: The value to validate

        Raises:
            ValidationError: If validation fails
        """
        self._validator(value)

    def and_(self, other: Rule[T]) -> Rule[T]:
        """Combine with another rule using AND logic.

        Both rules must pass for the combined rule to pass.

        Args:
            other: Another rule to combine with

        Returns:
            A new Rule that requires both rules to pass
        """

        def combined(value: T) -> None:
            self(value)
            other(value)

        return Rule(combined)

    def or_(self, other: Rule[T]) -> Rule[T]:
        """Combine with another rule using OR logic.

        At least one rule must pass for the combined rule to pass.

        Args:
            other: Another rule to combine with

        Returns:
            A new Rule that passes if either rule passes
        """

        def combined(value: T) -> None:
            try:
                self(value)
                return
            except ValidationError:
                pass
            try:
                other(value)
            except ValidationError as e:
                raise e

        return Rule(combined)


def rule(validator: Callable[[T], None]) -> Rule[T]:
    """Create a Rule from a validator function.

    This is a convenience decorator/factory for creating Rules
    from simple validator functions.

    Args:
        validator: A callable that raises ValidationError on failure

    Returns:
        A Rule wrapping the validator

    Example:
        @rule
        def non_empty_string(value: str) -> None:
            if not value or not value.strip():
                raise ValidationError("value", "Cannot be empty")
    """
    return Rule(validator)
