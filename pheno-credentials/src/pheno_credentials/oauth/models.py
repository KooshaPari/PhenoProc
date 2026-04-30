"""
OAuth models and data structures.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class OAuthGrantType(StrEnum):
    """OAuth grant types."""

    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"
    PASSWORD = "password"
    DEVICE_CODE = "device_code"


class OAuthScope(StrEnum):
    """Common OAuth scopes."""

    # GitHub
    GITHUB_READ_USER = "read:user"
    GITHUB_REPO = "repo"
    GITHUB_WORKFLOW = "workflow"
    GITHUB_PACKAGES = "packages"

    # Google
    GOOGLE_DRIVE = "https://www.googleapis.com/auth/drive"
    GOOGLE_GMAIL = "https://www.googleapis.com/auth/gmail.readonly"
    GOOGLE_CALENDAR = "https://www.googleapis.com/auth/calendar"
    GOOGLE_CLOUD = "https://www.googleapis.com/auth/cloud-platform"

    # Microsoft
    MICROSOFT_GRAPH = "https://graph.microsoft.com/.default"
    MICROSOFT_AZURE = "https://management.azure.com/.default"
    MICROSOFT_OFFICE = "https://graph.microsoft.com/Files.ReadWrite"

    # OpenAI
    OPENAI_API = "openai"

    # Generic
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class OAuthProviderType(StrEnum):
    """OAuth provider types."""

    GITHUB = "github"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    OPENAI = "openai"
    GENERIC = "generic"


class OAuthToken(BaseModel):
    """OAuth token model."""

    id: UUID = Field(default_factory=uuid4)
    provider: OAuthProviderType = Field(..., description="OAuth provider")
    access_token: str = Field(..., description="Access token")
    refresh_token: str | None = Field(None, description="Refresh token")
    token_type: str = Field("Bearer", description="Token type")
    expires_at: datetime | None = Field(None, description="Expiration timestamp")
    scope: list[str] = Field(default_factory=list, description="Token scopes")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: datetime | None = Field(None, description="Last usage timestamp")
    last_refreshed: datetime | None = Field(None, description="Last refresh timestamp")

    # Provider-specific data
    provider_data: dict[str, Any] = Field(default_factory=dict, description="Provider-specific data")

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid."""
        return not self.is_expired and bool(self.access_token)

    @property
    def can_refresh(self) -> bool:
        """Check if token can be refreshed."""
        return bool(self.refresh_token)

    def to_authorization_header(self) -> str:
        """Convert to Authorization header value."""
        return f"{self.token_type} {self.access_token}"


class OAuthFlow(BaseModel):
    """OAuth flow configuration."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Flow name")
    provider: OAuthProviderType = Field(..., description="OAuth provider")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    redirect_uri: str = Field(..., description="Redirect URI")
    scopes: list[str] = Field(default_factory=list, description="Requested scopes")
    grant_type: OAuthGrantType = Field(OAuthGrantType.AUTHORIZATION_CODE, description="Grant type")

    # Configuration
    auto_refresh: bool = Field(True, description="Auto-refresh tokens")
    refresh_threshold: int = Field(300, description="Refresh threshold in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")

    # URLs
    authorization_url: str | None = Field(None, description="Authorization URL")
    token_url: str | None = Field(None, description="Token URL")
    revoke_url: str | None = Field(None, description="Revoke URL")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: datetime | None = Field(None, description="Last usage timestamp")
    is_active: bool = Field(True, description="Whether flow is active")

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, v):
        """Validate scopes."""
        if not v:
            return []
        return [scope.value if hasattr(scope, "value") else str(scope) for scope in v]


class OAuthAuthorization(BaseModel):
    """OAuth authorization result."""

    id: UUID = Field(default_factory=uuid4)
    flow_id: UUID = Field(..., description="OAuth flow ID")
    code: str = Field(..., description="Authorization code")
    state: str | None = Field(None, description="State parameter")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Code expiration")

    @property
    def is_expired(self) -> bool:
        """Check if authorization code is expired."""
        return datetime.utcnow() >= self.expires_at


class OAuthError(BaseModel):
    """OAuth error information."""

    error: str = Field(..., description="Error code")
    error_description: str | None = Field(None, description="Error description")
    error_uri: str | None = Field(None, description="Error URI")
    state: str | None = Field(None, description="State parameter")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AutomationRule(BaseModel):
    """Automation rule for credential management."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Rule name")
    description: str | None = Field(None, description="Rule description")

    # Trigger conditions
    trigger_type: str = Field(..., description="Trigger type (schedule, event, condition)")
    trigger_config: dict[str, Any] = Field(default_factory=dict, description="Trigger configuration")

    # Actions
    actions: list[str] = Field(..., description="Actions to perform")
    action_config: dict[str, Any] = Field(default_factory=dict, description="Action configuration")

    # Target credentials
    credential_patterns: list[str] = Field(default_factory=list, description="Credential name patterns")
    providers: list[OAuthProviderType] = Field(default_factory=list, description="Target providers")

    # Configuration
    enabled: bool = Field(True, description="Whether rule is enabled")
    priority: int = Field(0, description="Rule priority")
    max_executions: int | None = Field(None, description="Maximum executions per day")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_executed: datetime | None = Field(None, description="Last execution timestamp")
    execution_count: int = Field(0, description="Total execution count")

    @property
    def can_execute(self) -> bool:
        """Check if rule can be executed."""
        if not self.enabled:
            return False

        return not (self.max_executions and self.execution_count >= self.max_executions)


class AutomationEvent(BaseModel):
    """Automation event."""

    id: UUID = Field(default_factory=uuid4)
    event_type: str = Field(..., description="Event type")
    source: str = Field(..., description="Event source")
    data: dict[str, Any] = Field(default_factory=dict, description="Event data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = Field(False, description="Whether event has been processed")


class TokenRefreshJob(BaseModel):
    """Token refresh job."""

    id: UUID = Field(default_factory=uuid4)
    token_id: UUID = Field(..., description="Token ID to refresh")
    scheduled_at: datetime = Field(..., description="Scheduled refresh time")
    retry_count: int = Field(0, description="Retry count")
    max_retries: int = Field(3, description="Maximum retries")
    status: str = Field("pending", description="Job status")
    error_message: str | None = Field(None, description="Error message")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_due(self) -> bool:
        """Check if job is due for execution."""
        return datetime.utcnow() >= self.scheduled_at

    @property
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries


__all__ = [
    "AutomationEvent",
    "AutomationRule",
    "OAuthAuthorization",
    "OAuthError",
    "OAuthFlow",
    "OAuthGrantType",
    "OAuthProviderType",
    "OAuthScope",
    "OAuthToken",
    "TokenRefreshJob",
]
