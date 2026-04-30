"""Validation decorators for enhanced validation workflows."""

from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from pheno_validation.errors import ValidationError, ValidationErrors

T = TypeVar("T")


def validated(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that validates method arguments.

    The decorated method should accept a `validator` keyword argument
    that will be called to perform validation.

    Example:
        @validated
        def create_user(name: str, email: str, *, validator=None) -> User:
            validator()
            return User(name=name, email=email)
    """

    @wraps(func)
    def wrapper(*args: ..., **kwargs: ...) -> T:
        validator = kwargs.pop("validator", None)
        if validator is not None:
            validator()
        return func(*args, **kwargs)

    return wrapper


def collect_errors(func: Callable[..., None]) -> Callable[..., ValidationErrors]:
    """Decorator that collects validation errors instead of raising.

    Instead of raising ValidationErrors on the first error,
    this decorator collects all errors and returns them.

    Example:
        @collect_errors
        def validate_user(user: User) -> None:
            Validator.email(user.email)
            Validator.range(user.age, 0, 150, "age")
    """

    @wraps(func)
    def wrapper(*args: ..., **kwargs: ...) -> ValidationErrors:
        errors = ValidationErrors()
        try:
            func(*args, **kwargs)
        except ValidationError as e:
            errors.add(e)
        return errors

    return wrapper


def require_validated(method: Callable[..., T]) -> Callable[..., T]:
    """Decorator that ensures object is valid before method execution.

    The decorated method will first call `self.validate()` and
    raise ValidationErrors if validation fails.

    Example:
        class User:
            def validate(self) -> None:
                validate_all(...)

            @require_validated
            def save(self) -> None:
                # Save user to database
                pass
    """

    @wraps(method)
    def wrapper(self: object, *args: ..., **kwargs: ...) -> T:
        if hasattr(self, "validate"):
            try:
                getattr(self, "validate")()
            except ValidationErrors as e:
                raise e
        return method(self, *args, **kwargs)

    return wrapper
