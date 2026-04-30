"""
Dry-Run System - Non-Destructive Operation Mode

Provides decorators and context managers for dry-run mode, enabling:
- Safe testing without side effects
- Preview mode in CLIs
- Development/staging safety
- Database migration previews

Usage:
    >>> from pheno.caching.dry import (
    ...     set_dry_run,
    ...     dry_run_aware,
    ...     dry_run_skip,
    ...     DryRunContext,
    ...     DryRunMixin
    ... )
    >>>
    >>> # Enable dry-run mode globally
    >>> set_dry_run(True)
    >>>
    >>> # Decorate functions
    >>> @dry_run_aware(operation_name="insert_user", return_value={"id": "dry-run"})
    >>> async def insert_user(name: str):
    ...     return await db.insert("users", {"name": name})
    >>>
    >>> # Use context manager
    >>> with DryRunContext(enabled=True):
    ...     await insert_user("John")  # Will not execute
    >>>
    >>> # Add to classes
    >>> class Service(DryRunMixin):
    ...     def __init__(self, dry_run: bool = False):
    ...         self._init_dry_run(dry_run)

Components:
- set_dry_run/is_dry_run: Global state management
- dry_run_aware: Decorator that respects dry-run flag
- dry_run_skip: Decorator that skips in dry-run mode
- dry_run_method: Decorator for class methods
- DryRunContext: Context manager for dry-run blocks
- DryRunMixin: Mixin for dry-run support in classes
"""

from .decorators import (
    DryRunContext,
    DryRunMixin,
    dry_run_aware,
    dry_run_method,
    dry_run_skip,
    is_dry_run,
    set_dry_run,
)

__all__ = [
    "DryRunContext",
    "DryRunMixin",
    "dry_run_aware",
    "dry_run_method",
    "dry_run_skip",
    "is_dry_run",
    "set_dry_run",
]
