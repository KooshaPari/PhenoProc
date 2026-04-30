"""Validation error types."""

from __future__ import annotations

import dataclasses
from typing import Iterator


class ValidationError(Exception):
    """A single validation error.

    Attributes:
        field: The name of the field that failed validation
        message: A human-readable description of the validation failure
    """

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"Validation error on field '{field}': {message}")

    def __repr__(self) -> str:
        return f"ValidationError(field={self.field!r}, message={self.message!r})"

    def __str__(self) -> str:
        return f"Validation error on field '{self.field}': {self.message}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ValidationError):
            return NotImplemented
        return self.field == other.field and self.message == other.message

    def __hash__(self) -> int:
        return hash((self.field, self.message))


class ValidationErrors(Exception):
    """Collection of validation errors.

    Aggregates multiple validation errors for comprehensive
    error reporting.

    Attributes:
        errors: List of collected ValidationError instances
    """

    def __init__(
        self,
        errors: list[ValidationError] | None = None,
    ) -> None:
        self.errors = errors if errors is not None else []
        super().__init__(f"{len(self.errors)} validation error(s)")

    def add(self, error: ValidationError) -> None:
        """Add an error to the collection.

        Args:
            error: The ValidationError to add
        """
        self.errors.append(error)

    def is_empty(self) -> bool:
        """Check if there are any errors.

        Returns:
            True if no errors have been collected
        """
        return len(self.errors) == 0

    def for_field(self, field: str) -> list[ValidationError]:
        """Get errors for a specific field.

        Args:
            field: The field name to filter by

        Returns:
            List of errors associated with the field
        """
        return [e for e in self.errors if e.field == field]

    def __iter__(self) -> Iterator[ValidationError]:
        """Iterate over all errors."""
        return iter(self.errors)

    def __len__(self) -> int:
        """Return the number of errors."""
        return len(self.errors)

    def __bool__(self) -> bool:
        """Return True if there are any errors."""
        return not self.is_empty()

    def __repr__(self) -> str:
        return f"ValidationErrors(errors={self.errors!r})"
