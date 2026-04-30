"""pheno_validation - Runtime validation framework for Python."""

from pheno_validation.protocol import Validate
from pheno_validation.errors import ValidationError, ValidationErrors
from pheno_validation.validators import Validator
from pheno_validation.rules import Rule, rule
from pheno_validation.typing import FieldValidator, ObjectValidator, ValidatorFn
from pheno_validation.helpers import validate_all
from pheno_validation.dataclass_support import ValidatedDataclass

__all__ = [
    "Validate",
    "ValidationError",
    "ValidationErrors",
    "Validator",
    "Rule",
    "rule",
    "FieldValidator",
    "ObjectValidator",
    "ValidatorFn",
    "validate_all",
    "ValidatedDataclass",
]

__version__ = "0.1.0"
