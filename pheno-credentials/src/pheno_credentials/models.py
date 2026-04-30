"""
Credential data models and types.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class CredentialScope(StrEnum):
    """Credential scope enumeration."""

    GLOBAL = "global"
    PROJECT = "project"
    ENVIRONMENT = "environment"
    USER = "user"


class CredentialType(StrEnum):
    """Credential type enumeration."""

    API_KEY = "api_key"
    OAUTH_TOKEN = "oauth_token"
    PASSWORD = "password"
    SECRET = "secret"
    CERTIFICATE = "certificate"
    SSH_KEY = "ssh_key"
    DATABASE_URL = "database_url"
    CONNECTION_STRING = "connection_string"


class CredentialStatus(StrEnum):
    """Credential status enumeration."""

    ACTIVE = "active"
    EXPIRED = "expired"
    INVALID = "invalid"
    PENDING = "pending"
    REVOKED = "revoked"


class Credential(BaseModel):
    """Credential model with metadata and security features."""

    id: UUID = Field(default_factory=uuid4, description="Unique credential identifier")
    name: str = Field(..., description="Credential name/key")
    value: str = Field(..., description="Credential value (encrypted)")
    type: CredentialType = Field(..., description="Type of credential")
    scope: CredentialScope = Field(..., description="Credential scope")
    project_id: str | None = Field(None, description="Project identifier for project-scoped credentials")
    environment: str | None = Field(None, description="Environment (dev/staging/prod)")
    service: str | None = Field(None, description="Service provider (e.g., 'openai', 'github')")
    description: str | None = Field(None, description="Human-readable description")
    tags: list[str] = Field(default_factory=list, description="Tags for organization")

    # Security and lifecycle
    encrypted: bool = Field(True, description="Whether the value is encrypted")
    expires_at: datetime | None = Field(None, description="Expiration timestamp")
    last_used: datetime | None = Field(None, description="Last access timestamp")
    last_modified: datetime = Field(default_factory=datetime.utcnow, description="Last modification timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    # Access control
    read_only: bool = Field(False, description="Whether credential is read-only")
    auto_refresh: bool = Field(False, description="Whether to auto-refresh OAuth tokens")
    refresh_token: str | None = Field(None, description="OAuth refresh token (encrypted)")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate credential name format."""
        if not v or not v.strip():
            raise ValueError("Credential name cannot be empty")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Credential name must be alphanumeric with underscores or hyphens")
        return v.upper()

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, v):
        """Validate expiration is in the future."""
        if v and v <= datetime.utcnow():
            raise ValueError("Expiration must be in the future")
        return v

    @property
    def is_expired(self) -> bool:
        """Check if credential is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if credential is valid and not expired."""
        return not self.is_expired and self.value is not None

    @property
    def key(self) -> str:
        """Get the credential key for storage."""
        if self.scope == CredentialScope.PROJECT and self.project_id:
            return f"{self.project_id[:4]}_{self.name}"
        if self.scope == CredentialScope.ENVIRONMENT and self.environment:
            return f"{self.environment}_{self.name}"
        return self.name

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Credential:
        """Create from dictionary."""
        return cls(**data)


class CredentialSearch(BaseModel):
    """Search criteria for credentials."""

    name: str | None = None
    type: CredentialType | None = None
    scope: CredentialScope | None = None
    project_id: str | None = None
    environment: str | None = None
    service: str | None = None
    tags: list[str] | None = None
    expired_only: bool = False
    valid_only: bool = False


class CredentialAccess(BaseModel):
    """Credential access log entry."""

    id: UUID = Field(default_factory=uuid4)
    credential_id: UUID = Field(..., description="ID of accessed credential")
    action: str = Field(..., description="Action performed (read, write, delete)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user: str | None = Field(None, description="User who performed action")
    project_id: str | None = Field(None, description="Project context")
    ip_address: str | None = Field(None, description="IP address")
    user_agent: str | None = Field(None, description="User agent")
    success: bool = Field(True, description="Whether action was successful")
    error_message: str | None = Field(None, description="Error message if failed")


class ProjectInfo(BaseModel):
    """Project information for credential scoping."""

    id: str = Field(..., description="Project identifier")
    name: str = Field(..., description="Project name")
    description: str | None = Field(None, description="Project description")
    path: str | None = Field(None, description="Project path")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime | None = Field(None, description="Last access timestamp")

    @property
    def short_id(self) -> str:
        """Get short project ID (first 4 characters)."""
        return self.id[:4]


class EncryptionKey(BaseModel):
    """Encryption key metadata."""

    id: str = Field(..., description="Key identifier")
    algorithm: str = Field("fernet", description="Encryption algorithm")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: datetime | None = Field(None, description="Last usage timestamp")
    key_derivation: str = Field("pbkdf2", description="Key derivation method")
    iterations: int = Field(100000, description="Key derivation iterations")

    def to_keyring_key(self) -> str:
        """Get keyring key for this encryption key."""
        return f"pheno_credentials_{self.id}"


__all__ = [
    "Credential",
    "CredentialAccess",
    "CredentialScope",
    "CredentialSearch",
    "CredentialStatus",
    "CredentialType",
    "EncryptionKey",
    "ProjectInfo",
]
