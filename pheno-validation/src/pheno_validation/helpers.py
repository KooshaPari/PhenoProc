"""Utility functions for validation."""

from __future__ import annotations

from typing import Callable

from pheno_validation.errors import ValidationError, ValidationErrors


def validate_all(*validations: Callable[[], None]) -> None:
    """Run all validations and collect errors.

    Unlike individual validators that raise on first error,
    this collects ALL errors before raising.

    Args:
        *validations: Callables that perform validation

    Raises:
        ValidationErrors: Aggregate of all validation errors

    Example:
        validate_all(
            lambda: Validator.email(user.email),
            lambda: Validator.range(user.age, 0, 150, "age"),
        )
    """
    errors = ValidationErrors()
    for validation in validations:
        try:
            validation()
        except ValidationError as e:
            errors.add(e)
    if not errors.is_empty():
        raise errors
