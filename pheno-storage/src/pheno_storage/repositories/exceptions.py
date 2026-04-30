"""Repository exceptions."""


class RepositoryError(Exception):
    """Base exception for repository operations."""


class EntityNotFoundError(RepositoryError):
    """Entity not found in repository."""


class ConnectionError(RepositoryError):
    """Connection to backend failed."""


class TransactionError(RepositoryError):
    """Transaction operation failed."""
