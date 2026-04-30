import tempfile
from pathlib import Path

import pytest

from pheno_credentials import CredentialBroker


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def broker(temp_dir):
    """Create CredentialBroker for testing."""
    return CredentialBroker(data_dir=temp_dir / ".pheno" / "credentials")


@pytest.fixture
def broker_with_credentials(broker):
    """Create broker with some test credentials."""
    broker.store_credential(
        name="TEST_API_KEY",
        value="test-api-key-value",
        credential_type="api_key",
        scope="global",
    )
    broker.store_credential(
        name="TEST_SECRET",
        value="test-secret-value",
        credential_type="secret",
        scope="global",
    )
    return broker
