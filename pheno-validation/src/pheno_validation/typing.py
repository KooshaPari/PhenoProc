"""Type definitions and helpers."""

from __future__ import annotations

from typing import Callable, TypeVar

from pheno_validation.errors import ValidationError

T = TypeVar("T")

FieldValidator = Callable[[], None]
"""A callable that performs field-level validation.

Example:
    validator: FieldValidator = lambda: Validator.email(user.email)
"""

ObjectValidator = Callable[[T], None]
"""A callable that validates an entire object.

Example:
    validator: ObjectValidator = lambda obj: validate_all(
        lambda: Validator.email(obj.email),
        lambda: Validator.range(obj.age, 0, 150, "age"),
    )
"""

ValidatorFn = Callable[[T], None]
"""General validation function type.

A callable that validates a value and raises ValidationError on failure.

Example:
    fn: ValidatorFn[str] = lambda s: Validator.not_empty(s, "field")
"""
