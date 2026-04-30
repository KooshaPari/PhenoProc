"""
Dry-Run System - Non-Destructive Operation Mode

This module provides decorators and context managers for dry-run mode:
- @dry_run_aware: Decorator that respects dry-run flag
- @dry_run_skip: Decorator that skips execution in dry-run mode
- DryRunContext: Context manager for dry-run blocks
- Global dry-run state management

Useful for:
- Testing without side effects
- Preview mode in CLIs
- Safe development/staging operations
- Database migration previews

Extracted from: atoms/scripts/backfill_embeddings.py (--dry-run flag pattern)
"""

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

# Type variable for generic function types
F = TypeVar("F", bound=Callable[..., Any])

# Global dry-run state
_dry_run_enabled = False
_dry_run_logger: logging.Logger | None = None


def set_dry_run(enabled: bool, logger: logging.Logger | None = None):
    """Set global dry-run mode.

    Args:
        enabled: Enable/disable dry-run mode
        logger: Optional logger for dry-run messages

    Examples:
        >>> from pheno.caching.dry import set_dry_run
        >>> import logging
        >>>
        >>> # Enable dry-run mode
        >>> set_dry_run(True, logging.getLogger(__name__))
        >>>
        >>> # Disable dry-run mode
        >>> set_dry_run(False)
    """
    global _dry_run_enabled, _dry_run_logger
    _dry_run_enabled = enabled
    _dry_run_logger = logger


def is_dry_run() -> bool:
    """Check if dry-run mode is enabled.

    Returns:
        True if dry-run mode is active

    Examples:
        >>> from pheno.caching.dry import is_dry_run, set_dry_run
        >>>
        >>> set_dry_run(True)
        >>> assert is_dry_run() == True
        >>>
        >>> set_dry_run(False)
        >>> assert is_dry_run() == False
    """
    return _dry_run_enabled


def _log_dry_run(message: str):
    """
    Log a dry-run message.
    """
    if _dry_run_logger:
        _dry_run_logger.info(f"[DRY RUN] {message}")
    else:
        print(f"[DRY RUN] {message}")


def dry_run_aware(
    operation_name: str | None = None,
    return_value: Any = None,
) -> Callable[[F], F]:
    """Decorator that makes a function dry-run aware.

    In dry-run mode:
    - Logs the operation that would be performed
    - Returns specified return_value instead of executing
    - Preserves function signature and docstring

    Args:
        operation_name: Name of operation (defaults to function name)
        return_value: Value to return in dry-run mode (default: None)

    Examples:
        >>> from pheno.caching.dry import dry_run_aware, set_dry_run
        >>>
        >>> @dry_run_aware(operation_name="insert_record", return_value={"id": "dry-run-id"})
        >>> async def insert_user(name: str, email: str):
        ...     # This will be skipped in dry-run mode
        ...     result = await db.insert("users", {"name": name, "email": email})
        ...     return result
        >>>
        >>> # Enable dry-run mode
        >>> set_dry_run(True)
        >>>
        >>> # This will log but not execute
        >>> result = await insert_user("John", "john@example.com")
        >>> # Returns: {"id": "dry-run-id"}
    """

    def decorator(func: F) -> F:
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if is_dry_run():
                # Log the operation
                args_str = ", ".join(str(a) for a in args)
                kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
                params = ", ".join(filter(None, [args_str, kwargs_str]))
                _log_dry_run(f"Would execute {op_name}({params})")
                return return_value

            # Execute normally
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if is_dry_run():
                # Log the operation
                args_str = ", ".join(str(a) for a in args)
                kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
                params = ", ".join(filter(None, [args_str, kwargs_str]))
                _log_dry_run(f"Would execute {op_name}({params})")
                return return_value

            # Execute normally
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def dry_run_skip(
    operation_name: str | None = None,
    skip_return: Any = None,
) -> Callable[[F], F]:
    """Decorator that skips function execution in dry-run mode.

    Similar to dry_run_aware but more explicit about skipping.

    Args:
        operation_name: Name of operation (defaults to function name)
        skip_return: Value to return when skipped (default: None)

    Examples:
        >>> from pheno.caching.dry import dry_run_skip, set_dry_run
        >>>
        >>> @dry_run_skip(operation_name="delete_records")
        >>> async def delete_old_records():
        ...     # This will be completely skipped in dry-run mode
        ...     await db.delete("records", {"age": {"gt": 30}})
        >>>
        >>> set_dry_run(True)
        >>> await delete_old_records()  # Logs skip message, returns None
    """

    def decorator(func: F) -> F:
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if is_dry_run():
                _log_dry_run(f"Skipping {op_name}")
                return skip_return

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if is_dry_run():
                _log_dry_run(f"Skipping {op_name}")
                return skip_return

            return func(*args, **kwargs)

        # Return appropriate wrapper
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


class DryRunContext:
    """Context manager for dry-run blocks.

    Temporarily enables/disables dry-run mode within a context.

    Examples:
        >>> from pheno.caching.dry import DryRunContext
        >>>
        >>> # Temporarily enable dry-run mode
        >>> with DryRunContext(enabled=True):
        ...     # All operations in this block are dry-run
        ...     await insert_user("John", "john@example.com")
        ...     await delete_old_records()
        >>>
        >>> # Outside context, dry-run mode is restored to previous state
    """

    def __init__(self, enabled: bool, logger: logging.Logger | None = None):
        """Initialize dry-run context.

        Args:
            enabled: Enable/disable dry-run mode in this context
            logger: Optional logger for dry-run messages
        """
        self.enabled = enabled
        self.logger = logger
        self._previous_enabled = False
        self._previous_logger: logging.Logger | None = None

    def __enter__(self):
        """
        Enter dry-run context.
        """
        global _dry_run_enabled, _dry_run_logger
        self._previous_enabled = _dry_run_enabled
        self._previous_logger = _dry_run_logger
        _dry_run_enabled = self.enabled
        if self.logger is not None:
            _dry_run_logger = self.logger
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit dry-run context and restore previous state.
        """
        global _dry_run_enabled, _dry_run_logger
        _dry_run_enabled = self._previous_enabled
        _dry_run_logger = self._previous_logger


class DryRunMixin:
    """Mixin to add dry-run support to classes.

    Provides instance-level dry-run state and helper methods.

    Examples:
        >>> from pheno.caching.dry import DryRunMixin
        >>>
        >>> class DatabaseAdapter(DryRunMixin):
        ...     def __init__(self, dry_run: bool = False):
        ...         self._init_dry_run(dry_run)
        ...
        ...     async def insert(self, table: str, data: dict):
        ...         if self.is_dry_run():
        ...             self.log_dry_run(f"Would insert into {table}: {data}")
        ...             return {"id": "dry-run-id"}
        ...
        ...         # Actual insert
        ...         return await self._execute_insert(table, data)
        ...
        ...     async def delete(self, table: str, filters: dict):
        ...         if self.is_dry_run():
        ...             self.log_dry_run(f"Would delete from {table}: {filters}")
        ...             return
        ...
        ...         # Actual delete
        ...         await self._execute_delete(table, filters)
    """

    def _init_dry_run(self, enabled: bool = False, logger: logging.Logger | None = None):
        """Initialize dry-run state for instance.

        Args:
            enabled: Enable/disable dry-run mode
            logger: Optional logger for dry-run messages
        """
        self._dry_run_enabled = enabled
        self._dry_run_logger = logger

    def is_dry_run(self) -> bool:
        """
        Check if dry-run mode is enabled for this instance.
        """
        return getattr(self, "_dry_run_enabled", False)

    def set_dry_run(self, enabled: bool):
        """
        Set dry-run mode for this instance.
        """
        self._dry_run_enabled = enabled

    def log_dry_run(self, message: str):
        """
        Log a dry-run message.
        """
        logger = getattr(self, "_dry_run_logger", None)
        if logger:
            logger.info(f"[DRY RUN] {message}")
        else:
            print(f"[DRY RUN] {message}")


def dry_run_method(
    operation_name: str | None = None,
    return_value: Any = None,
) -> Callable[[F], F]:
    """Decorator for class methods that respects instance dry-run state.

    Requires class to have is_dry_run() and log_dry_run() methods
    (provided by DryRunMixin).

    Args:
        operation_name: Name of operation (defaults to method name)
        return_value: Value to return in dry-run mode

    Examples:
        >>> from pheno.caching.dry import DryRunMixin, dry_run_method
        >>>
        >>> class Service(DryRunMixin):
        ...     def __init__(self, dry_run: bool = False):
        ...         self._init_dry_run(dry_run)
        ...
        ...     @dry_run_method(return_value={"status": "skipped"})
        ...     async def process_data(self, data: dict):
        ...         # Will be skipped if dry_run=True
        ...         result = await self._expensive_operation(data)
        ...         return result
    """

    def decorator(func: F) -> F:
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            if hasattr(self, "is_dry_run") and self.is_dry_run():
                args_str = ", ".join(str(a) for a in args)
                kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
                params = ", ".join(filter(None, [args_str, kwargs_str]))
                if hasattr(self, "log_dry_run"):
                    self.log_dry_run(f"Would execute {op_name}({params})")
                return return_value

            return await func(self, *args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            if hasattr(self, "is_dry_run") and self.is_dry_run():
                args_str = ", ".join(str(a) for a in args)
                kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
                params = ", ".join(filter(None, [args_str, kwargs_str]))
                if hasattr(self, "log_dry_run"):
                    self.log_dry_run(f"Would execute {op_name}({params})")
                return return_value

            return func(self, *args, **kwargs)

        # Return appropriate wrapper
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


__all__ = [
    "DryRunContext",
    "DryRunMixin",
    "dry_run_aware",
    "dry_run_method",
    "dry_run_skip",
    "is_dry_run",
    "set_dry_run",
]
