"""Tests for OAuth functionality."""

import pytest

from pheno_credentials import CredentialBroker
from pheno_credentials.models import CredentialType


class TestOAuthCredentialStorage:
    """Tests for OAuth credential storage."""

    def test_store_oauth_token(self, broker):
        """Test storing OAuth token credential."""
        result = broker.store_credential(
            name="GITHUB_TOKEN",
            value="gho_token_value",
            credential_type="oauth_token",
            scope="global",
            service="github",
            auto_refresh=True,
        )
        assert result is True

        credential = broker.get_credential_info("GITHUB_TOKEN")
        assert credential is not None
        assert credential.type.value == "oauth_token"
        assert credential.service == "github"
        assert credential.auto_refresh is True

    def test_store_multiple_oauth_tokens(self, broker):
        """Test storing multiple OAuth tokens for different services."""
        providers = [
            ("github", "gho_github_token"),
            ("google", "ya29_google_token"),
            ("openai", "sk_openai_token"),
        ]

        for provider, token_value in providers:
            result = broker.store_credential(
                name=f"{provider.upper()}_TOKEN",
                value=token_value,
                credential_type="oauth_token",
                scope="global",
                service=provider,
            )
            assert result is True

        all_creds = broker.list_credentials(scope="global")
        oauth_tokens = [c for c in all_creds if c.type == CredentialType.OAUTH_TOKEN]
        assert len(oauth_tokens) >= 3

    def test_oauth_token_lifecycle(self, broker):
        """Test OAuth token update lifecycle."""
        broker.store_credential(
            name="TEST_OAUTH",
            value="initial_token",
            credential_type="oauth_token",
            scope="global",
            service="test",
            auto_refresh=True,
        )

        token = broker.get_credential_info("TEST_OAUTH")
        assert token.auto_refresh is True

        broker.store_credential(
            name="TEST_OAUTH",
            value="refreshed_token",
            credential_type="oauth_token",
            scope="global",
            service="test",
            auto_refresh=True,
        )

        refreshed = broker.get_credential_info("TEST_OAUTH")
        assert refreshed.value == "refreshed_token"


class TestOAuthValidation:
    """Tests for OAuth credential validation."""

    def test_validate_oauth_credential(self, broker):
        """Test validating OAuth credential."""
        broker.store_credential(
            name="VALID_OAUTH",
            value="valid_token",
            credential_type="oauth_token",
            scope="global",
            service="test",
        )

        results = broker.validate_credentials(["VALID_OAUTH"])
        assert results["VALID_OAUTH"] is True

    def test_validate_oauth_credential_not_found(self, broker):
        """Test validating OAuth credential that doesn't exist."""
        results = broker.validate_credentials(["MISSING_OAUTH"])
        assert results["MISSING_OAUTH"] is False
