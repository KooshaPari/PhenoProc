"""Validate protocol for structural subtyping."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Validate(Protocol):
    """Protocol for types that can validate themselves.

    Any class implementing this protocol can be validated
    using the validation framework.

    Example:
        @dataclass
        class User(Validate):
            email: str
            age: int

            def validate(self) -> None:
                validate_all(
                    lambda: Validator.email(self.email),
                    lambda: Validator.range(self.age, 0, 150, "age"),
                )
    """

    def validate(self) -> None:
        """Validate this instance.

        Raises:
            ValidationErrors: If validation fails (aggregate of all errors)
        """
        ...
