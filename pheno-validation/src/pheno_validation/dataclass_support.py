"""Dataclass integration utilities."""

from __future__ import annotations

import dataclasses
from typing import Self

from pheno_validation.errors import ValidationError, ValidationErrors
from pheno_validation.protocol import Validate


@dataclasses.dataclass
class ValidatedDataclass:
    """Base class for dataclasses with built-in validation.

    Inherit from this class and override the `validate` method
    to add validation to your dataclasses.

    Example:
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
        user.validate()  # Raises ValidationErrors if invalid
    """

    def validate(self) -> None:
        """Validate this instance.

        Override in subclasses to add validation logic.
        Call `super().validate()` to ensure parent validation runs.

        Raises:
            ValidationErrors: If validation fails
        """
        pass

    def is_valid(self) -> bool:
        """Check if validation passes without raising.

        Returns:
            True if validation succeeds, False otherwise
        """
        try:
            self.validate()
            return True
        except (ValidationError, ValidationErrors):
            return False

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create instance from dictionary with validation.

        Args:
            data: Dictionary containing field values

        Returns:
            A new instance of the dataclass

        Raises:
            ValidationErrors: If data is invalid
        """
        instance = cls(**data)
        instance.validate()
        return instance
