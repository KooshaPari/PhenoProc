"""
OAuth flow implementations.
"""

import secrets
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlencode

import httpx

from .models import (
    OAuthError,
    OAuthFlow,
    OAuthProviderType,
    OAuthToken,
)


class OAuthProvider(ABC):
    """Abstract OAuth provider."""

    def __init__(self, flow: OAuthFlow):
        """Initialize OAuth provider.

        Args:
            flow: OAuth flow configuration
        """
        self.flow = flow
        self.client = httpx.AsyncClient()

    @property
    @abstractmethod
    def provider_type(self) -> OAuthProviderType:
        """Get provider type."""

    @property
    @abstractmethod
    def authorization_url(self) -> str:
        """Get authorization URL."""

    @property
    @abstractmethod
    def token_url(self) -> str:
        """Get token URL."""

    @property
    @abstractmethod
    def revoke_url(self) -> str | None:
        """Get revoke URL."""

    def generate_state(self) -> str:
        """Generate state parameter for CSRF protection."""
        return secrets.token_urlsafe(32)

    def build_authorization_url(self, state: str) -> str:
        """Build authorization URL.

        Args:
            state: State parameter for CSRF protection

        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.flow.client_id,
            "redirect_uri": self.flow.redirect_uri,
            "scope": " ".join(self.flow.scopes),
            "state": state,
            "response_type": "code",
        }

        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str, state: str) -> OAuthToken:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code
            state: State parameter

        Returns:
            OAuth token

        Raises:
            OAuthError: If token exchange fails
        """
        data = {
            "grant_type": "authorization_code",
            "client_id": self.flow.client_id,
            "client_secret": self.flow.client_secret,
            "code": code,
            "redirect_uri": self.flow.redirect_uri,
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            response = await self.client.post(
                self.token_url,
                data=data,
                headers=headers,
            )
            response.raise_for_status()

            token_data = response.json()
            return self._parse_token_response(token_data)

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            raise OAuthError(
                error=error_data.get("error", "token_exchange_failed"),
                error_description=error_data.get("error_description", str(e)),
                state=state,
            )
        except Exception as e:
            raise OAuthError(
                error="token_exchange_failed",
                error_description=str(e),
                state=state,
            )

    async def refresh_token(self, token: OAuthToken) -> OAuthToken:
        """Refresh access token.

        Args:
            token: Token to refresh

        Returns:
            Refreshed token

        Raises:
            OAuthError: If token refresh fails
        """
        if not token.refresh_token:
            raise OAuthError(
                error="no_refresh_token",
                error_description="Token cannot be refreshed",
            )

        data = {
            "grant_type": "refresh_token",
            "client_id": self.flow.client_id,
            "client_secret": self.flow.client_secret,
            "refresh_token": token.refresh_token,
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            response = await self.client.post(
                self.token_url,
                data=data,
                headers=headers,
            )
            response.raise_for_status()

            token_data = response.json()
            return self._parse_token_response(token_data)

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            raise OAuthError(
                error=error_data.get("error", "token_refresh_failed"),
                error_description=error_data.get("error_description", str(e)),
            )
        except Exception as e:
            raise OAuthError(
                error="token_refresh_failed",
                error_description=str(e),
            )

    async def revoke_token(self, token: OAuthToken) -> bool:
        """Revoke access token.

        Args:
            token: Token to revoke

        Returns:
            True if successful
        """
        if not self.revoke_url:
            return False

        data = {
            "token": token.access_token,
            "client_id": self.flow.client_id,
            "client_secret": self.flow.client_secret,
        }

        try:
            response = await self.client.post(
                self.revoke_url,
                data=data,
            )
            return response.status_code == 200

        except Exception:
            return False

    def _parse_token_response(self, data: dict[str, Any]) -> OAuthToken:
        """Parse token response from provider.

        Args:
            data: Token response data

        Returns:
            OAuth token
        """
        expires_in = data.get("expires_in")
        expires_at = None

        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        return OAuthToken(
            provider=self.provider_type,
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=data.get("scope", "").split() if data.get("scope") else [],
            provider_data=data,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class GitHubOAuthProvider(OAuthProvider):
    """GitHub OAuth provider."""

    @property
    def provider_type(self) -> OAuthProviderType:
        return OAuthProviderType.GITHUB

    @property
    def authorization_url(self) -> str:
        return "https://github.com/login/oauth/authorize"

    @property
    def token_url(self) -> str:
        return "https://github.com/login/oauth/access_token"

    @property
    def revoke_url(self) -> str | None:
        return "https://api.github.com/applications/{client_id}/token"

    def build_authorization_url(self, state: str) -> str:
        """Build GitHub authorization URL."""
        params = {
            "client_id": self.flow.client_id,
            "redirect_uri": self.flow.redirect_uri,
            "scope": " ".join(self.flow.scopes),
            "state": state,
        }

        return f"{self.authorization_url}?{urlencode(params)}"


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth provider."""

    @property
    def provider_type(self) -> OAuthProviderType:
        return OAuthProviderType.GOOGLE

    @property
    def authorization_url(self) -> str:
        return "https://accounts.google.com/o/oauth2/v2/auth"

    @property
    def token_url(self) -> str:
        return "https://oauth2.googleapis.com/token"

    @property
    def revoke_url(self) -> str | None:
        return "https://oauth2.googleapis.com/revoke"

    def build_authorization_url(self, state: str) -> str:
        """Build Google authorization URL."""
        params = {
            "client_id": self.flow.client_id,
            "redirect_uri": self.flow.redirect_uri,
            "scope": " ".join(self.flow.scopes),
            "state": state,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
        }

        return f"{self.authorization_url}?{urlencode(params)}"


class MicrosoftOAuthProvider(OAuthProvider):
    """Microsoft OAuth provider."""

    @property
    def provider_type(self) -> OAuthProviderType:
        return OAuthProviderType.MICROSOFT

    @property
    def authorization_url(self) -> str:
        return "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"

    @property
    def token_url(self) -> str:
        return "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    @property
    def revoke_url(self) -> str | None:
        return None  # Microsoft doesn't provide a revoke URL


class OpenAIOAuthProvider(OAuthProvider):
    """OpenAI OAuth provider."""

    @property
    def provider_type(self) -> OAuthProviderType:
        return OAuthProviderType.OPENAI

    @property
    def authorization_url(self) -> str:
        return "https://auth0.openai.com/authorize"

    @property
    def token_url(self) -> str:
        return "https://auth0.openai.com/oauth/token"

    @property
    def revoke_url(self) -> str | None:
        return None


class GenericOAuthProvider(OAuthProvider):
    """Generic OAuth provider."""

    @property
    def provider_type(self) -> OAuthProviderType:
        return OAuthProviderType.GENERIC

    @property
    def authorization_url(self) -> str:
        return self.flow.authorization_url or ""

    @property
    def token_url(self) -> str:
        return self.flow.token_url or ""

    @property
    def revoke_url(self) -> str | None:
        return self.flow.revoke_url


class OAuthFlowManager:
    """OAuth flow manager."""

    def __init__(self):
        """Initialize OAuth flow manager."""
        self.providers = {
            OAuthProviderType.GITHUB: GitHubOAuthProvider,
            OAuthProviderType.GOOGLE: GoogleOAuthProvider,
            OAuthProviderType.MICROSOFT: MicrosoftOAuthProvider,
            OAuthProviderType.OPENAI: OpenAIOAuthProvider,
            OAuthProviderType.GENERIC: GenericOAuthProvider,
        }
        self.active_flows: dict[str, OAuthProvider] = {}

    def create_provider(self, flow: OAuthFlow) -> OAuthProvider:
        """Create OAuth provider for flow.

        Args:
            flow: OAuth flow configuration

        Returns:
            OAuth provider instance
        """
        provider_class = self.providers.get(flow.provider)
        if not provider_class:
            raise ValueError(f"Unsupported OAuth provider: {flow.provider}")

        return provider_class(flow)

    async def start_flow(self, flow: OAuthFlow) -> tuple[str, str]:
        """Start OAuth flow.

        Args:
            flow: OAuth flow configuration

        Returns:
            Tuple of (authorization_url, state)
        """
        provider = self.create_provider(flow)
        state = provider.generate_state()
        auth_url = provider.build_authorization_url(state)

        # Store active flow
        self.active_flows[state] = provider

        return auth_url, state

    async def complete_flow(self, code: str, state: str) -> OAuthToken:
        """Complete OAuth flow.

        Args:
            code: Authorization code
            state: State parameter

        Returns:
            OAuth token

        Raises:
            OAuthError: If flow completion fails
        """
        provider = self.active_flows.get(state)
        if not provider:
            raise OAuthError(
                error="invalid_state",
                error_description="Invalid or expired state parameter",
            )

        try:
            return await provider.exchange_code_for_token(code, state)
        finally:
            # Clean up active flow
            del self.active_flows[state]
            await provider.close()

    async def refresh_token(self, flow: OAuthFlow, token: OAuthToken) -> OAuthToken:
        """Refresh OAuth token.

        Args:
            flow: OAuth flow configuration
            token: Token to refresh

        Returns:
            Refreshed token
        """
        provider = self.create_provider(flow)
        try:
            return await provider.refresh_token(token)
        finally:
            await provider.close()

    async def revoke_token(self, flow: OAuthFlow, token: OAuthToken) -> bool:
        """Revoke OAuth token.

        Args:
            flow: OAuth flow configuration
            token: Token to revoke

        Returns:
            True if successful
        """
        provider = self.create_provider(flow)
        try:
            return await provider.revoke_token(token)
        finally:
            await provider.close()


__all__ = [
    "GenericOAuthProvider",
    "GitHubOAuthProvider",
    "GoogleOAuthProvider",
    "MicrosoftOAuthProvider",
    "OAuthFlowManager",
    "OAuthProvider",
    "OpenAIOAuthProvider",
]
