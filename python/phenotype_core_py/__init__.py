"""Python bindings for Phenotype Core.

This module provides FFI bindings to the Rust phenotype-core crate.
"""

try:
    from ._phenotype_core_py import (
        EntityId,
        Config,
        validate_entity,
    )
except ImportError:
    # Fallback for development
    raise ImportError(
        "phenotype_core_py native module not found. "
        "Build with: cd PhenoKit/rust/phenotype-core-py && maturin develop"
    )

__all__ = ["EntityId", "Config", "validate_entity"]
__version__ = "0.1.0"
