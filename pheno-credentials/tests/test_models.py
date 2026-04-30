"""Tests for credential models."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from pheno_credentials.models import (
    Credential,
    CredentialAccess,
    CredentialScope,
    CredentialSearch,
    CredentialStatus,
    CredentialType,
    EncryptionKey,
    ProjectInfo,
)


class TestCredentialModel:
    """Tests for Credential model."""

    def test_create_basic_credential(self):
        """Test creating a basic credential."""
        cred = Credential(
            name="TEST_KEY",
            value="test-value",
            type=CredentialType.API_KEY,
            scope=CredentialScope.GLOBAL,
        )
        assert cred.name == "TEST_KEY"
        assert cred.value == "test-value"
        assert cred.type == CredentialType.API_KEY
        assert cred.scope == CredentialScope.GLOBAL

    def test_credential_name_normalization(self):
        """Test that credential names are normalized to uppercase."""
        cred = Credential(
            name="test_key",
            value="value",
            type=CredentialType.SECRET,
            scope=CredentialScope.GLOBAL,
        )
        assert cred.name == "TEST_KEY"

    def test_credential_invalid_name_raises(self):
        """Test that invalid credential names raise validation error."""
        with pytest.raises(ValidationError):
            Credential(
                name="invalid name!",
                value="value",
                type=CredentialType.SECRET,
                scope=CredentialScope.GLOBAL,
            )

    def test_credential_empty_name_raises(self):
        """Test that empty credential name raises validation error."""
        with pytest.raises(ValidationError):
            Credential(
                name="",
                value="value",
                type=CredentialType.SECRET,
                scope=CredentialScope.GLOBAL,
            )

    def test_credential_is_valid(self):
        """Test credential validity check."""
        cred = Credential(
            name="VALID",
            value="value",
            type=CredentialType.SECRET,
            scope=CredentialScope.GLOBAL,
        )
        assert cred.is_valid is True

    def test_credential_key_for_global_scope(self):
        """Test credential key for global scope."""
        cred = Credential(
            name="GLOBAL_KEY",
            value="value",
            type=CredentialType.SECRET,
            scope=CredentialScope.GLOBAL,
        )
        assert cred.key == "GLOBAL_KEY"

    def test_credential_key_for_project_scope(self):
        """Test credential key for project scope."""
        cred = Credential(
            name="PROJECT_KEY",
            value="value",
            type=CredentialType.SECRET,
            scope=CredentialScope.PROJECT,
            project_id="proj1234",
        )
        assert cred.key == "proj_PROJECT_KEY"

    def test_credential_key_for_environment_scope(self):
        """Test credential key for environment scope."""
        cred = Credential(
            name="ENV_KEY",
            value="value",
            type=CredentialType.SECRET,
            scope=CredentialScope.ENVIRONMENT,
            environment="production",
        )
        assert cred.key == "production_ENV_KEY"

    def test_credential_to_dict(self):
        """Test converting credential to dictionary."""
        cred = Credential(
            name="TEST",
            value="value",
            type=CredentialType.API_KEY,
            scope=CredentialScope.GLOBAL,
        )
        data = cred.to_dict()
        assert isinstance(data, dict)
        assert data["name"] == "TEST"
        assert data["value"] == "value"

    def test_credential_from_dict(self):
        """Test creating credential from dictionary."""
        data = {
            "name": "TEST",
            "value": "value",
            "type": "api_key",
            "scope": "global",
        }
        cred = Credential.from_dict(data)
        assert cred.name == "TEST"
        assert cred.value == "value"


class TestCredentialScope:
    """Tests for CredentialScope enum."""

    def test_scope_values(self):
        """Test scope enum values."""
        assert CredentialScope.GLOBAL.value == "global"
        assert CredentialScope.PROJECT.value == "project"
        assert CredentialScope.ENVIRONMENT.value == "environment"
        assert CredentialScope.USER.value == "user"


class TestCredentialType:
    """Tests for CredentialType enum."""

    def test_type_values(self):
        """Test type enum values."""
        assert CredentialType.API_KEY.value == "api_key"
        assert CredentialType.OAUTH_TOKEN.value == "oauth_token"
        assert CredentialType.PASSWORD.value == "password"
        assert CredentialType.SECRET.value == "secret"
        assert CredentialType.CERTIFICATE.value == "certificate"
        assert CredentialType.SSH_KEY.value == "ssh_key"


class TestCredentialStatus:
    """Tests for CredentialStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert CredentialStatus.ACTIVE.value == "active"
        assert CredentialStatus.EXPIRED.value == "expired"
        assert CredentialStatus.INVALID.value == "invalid"
        assert CredentialStatus.PENDING.value == "pending"
        assert CredentialStatus.REVOKED.value == "revoked"


class TestCredentialSearch:
    """Tests for CredentialSearch model."""

    def test_create_empty_search(self):
        """Test creating empty search criteria."""
        search = CredentialSearch()
        assert search.name is None
        assert search.scope is None

    def test_create_search_with_filters(self):
        """Test creating search with filters."""
        search = CredentialSearch(
            scope=CredentialScope.GLOBAL,
            type=CredentialType.API_KEY,
            service="github",
        )
        assert search.scope == CredentialScope.GLOBAL
        assert search.type == CredentialType.API_KEY
        assert search.service == "github"


class TestCredentialAccess:
    """Tests for CredentialAccess model."""

    def test_create_access_log_entry(self):
        """Test creating access log entry."""
        access = CredentialAccess(
            credential_id=uuid4(),
            action="read",
        )
        assert access.action == "read"
        assert access.success is True

    def test_access_log_with_failure(self):
        """Test access log entry for failed action."""
        access = CredentialAccess(
            credential_id=uuid4(),
            action="write",
            success=False,
            error_message="Access denied",
        )
        assert access.success is False
        assert access.error_message == "Access denied"


class TestProjectInfo:
    """Tests for ProjectInfo model."""

    def test_create_project_info(self):
        """Test creating project info."""
        project = ProjectInfo(
            id="test-project-123",
            name="Test Project",
        )
        assert project.id == "test-project-123"
        assert project.name == "Test Project"

    def test_project_short_id(self):
        """Test project short ID property."""
        project = ProjectInfo(
            id="test-project-123",
            name="Test Project",
        )
        assert project.short_id == "test"


class TestEncryptionKey:
    """Tests for EncryptionKey model."""

    def test_create_encryption_key(self):
        """Test creating encryption key."""
        key = EncryptionKey(id="test-key-1")
        assert key.id == "test-key-1"
        assert key.algorithm == "fernet"

    def test_to_keyring_key(self):
        """Test converting to keyring key."""
        key = EncryptionKey(id="my-key")
        assert key.to_keyring_key() == "pheno_credentials_my-key"
