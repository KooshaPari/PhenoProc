"""
Credential storage backends.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from .encryption import EncryptionService
from .models import Credential, CredentialSearch


class CredentialStore(ABC):
    """Abstract base class for credential storage backends."""

    @abstractmethod
    def store(self, credential: Credential) -> bool:
        """Store a credential.

        Args:
            credential: Credential to store

        Returns:
            True if successful
        """

    @abstractmethod
    def retrieve(self, key: str) -> Credential | None:
        """Retrieve a credential by key.

        Args:
            key: Credential key

        Returns:
            Credential if found, None otherwise
        """

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a credential by key.

        Args:
            key: Credential key

        Returns:
            True if successful
        """

    @abstractmethod
    def list_keys(self) -> list[str]:
        """List all credential keys.

        Returns:
            List of credential keys
        """

    @abstractmethod
    def search(self, search: CredentialSearch) -> list[Credential]:
        """Search for credentials.

        Args:
            search: Search criteria

        Returns:
            List of matching credentials
        """


class KeyringStore(CredentialStore):
    """Credential storage using OS keyring."""

    def __init__(self, service_name: str = "pheno-credentials"):
        """Initialize keyring store.

        Args:
            service_name: Keyring service name
        """
        if not KEYRING_AVAILABLE:
            raise ImportError("keyring package not available")

        self.service_name = service_name

    def store(self, credential: Credential) -> bool:
        """Store credential in keyring."""
        try:
            # Store credential metadata as JSON
            metadata = {
                "id": str(credential.id),
                "type": credential.type.value,
                "scope": credential.scope.value,
                "project_id": credential.project_id,
                "environment": credential.environment,
                "service": credential.service,
                "description": credential.description,
                "tags": credential.tags,
                "encrypted": credential.encrypted,
                "expires_at": credential.expires_at.isoformat() if credential.expires_at else None,
                "last_used": credential.last_used.isoformat() if credential.last_used else None,
                "last_modified": credential.last_modified.isoformat(),
                "created_at": credential.created_at.isoformat(),
                "read_only": credential.read_only,
                "auto_refresh": credential.auto_refresh,
                "metadata": credential.metadata,
            }

            # Store value and metadata separately
            keyring.set_password(self.service_name, f"{credential.key}_value", credential.value)
            keyring.set_password(self.service_name, f"{credential.key}_meta", json.dumps(metadata))

            return True

        except Exception:
            return False

    def retrieve(self, key: str) -> Credential | None:
        """Retrieve credential from keyring."""
        try:
            # Get value and metadata
            value = keyring.get_password(self.service_name, f"{key}_value")
            meta_str = keyring.get_password(self.service_name, f"{key}_meta")

            if not value or not meta_str:
                return None

            # Parse metadata
            metadata = json.loads(meta_str)

            # Create credential object
            return Credential(
                id=metadata["id"],
                name=key,
                value=value,
                type=metadata["type"],
                scope=metadata["scope"],
                project_id=metadata.get("project_id"),
                environment=metadata.get("environment"),
                service=metadata.get("service"),
                description=metadata.get("description"),
                tags=metadata.get("tags", []),
                encrypted=metadata.get("encrypted", True),
                expires_at=metadata["expires_at"] and datetime.fromisoformat(metadata["expires_at"]),
                last_used=metadata["last_used"] and datetime.fromisoformat(metadata["last_used"]),
                last_modified=datetime.fromisoformat(metadata["last_modified"]),
                created_at=datetime.fromisoformat(metadata["created_at"]),
                read_only=metadata.get("read_only", False),
                auto_refresh=metadata.get("auto_refresh", False),
                metadata=metadata.get("metadata", {}),
            )


        except Exception:
            return None

    def delete(self, key: str) -> bool:
        """Delete credential from keyring."""
        try:
            keyring.delete_password(self.service_name, f"{key}_value")
            keyring.delete_password(self.service_name, f"{key}_meta")
            return True
        except Exception:
            return False

    def list_keys(self) -> list[str]:
        """List all credential keys from keyring."""
        # Note: keyring doesn't provide a way to list all keys
        # This is a limitation of the keyring backend
        return []

    def search(self, search: CredentialSearch) -> list[Credential]:
        """Search credentials in keyring."""
        # Note: keyring doesn't support search
        # This is a limitation of the keyring backend
        return []


class EncryptedFileStore(CredentialStore):
    """Credential storage using encrypted files."""

    def __init__(self, data_dir: Path | None = None, encryption_service: EncryptionService | None = None):
        """Initialize encrypted file store.

        Args:
            data_dir: Directory for credential files
            encryption_service: Encryption service instance
        """
        self.data_dir = data_dir or Path.home() / ".pheno" / "credentials"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.encryption_service = encryption_service or EncryptionService()
        self._cache: dict[str, Credential] = {}
        self._load_cache()

    def _load_cache(self):
        """Load all credentials into cache."""
        try:
            cache_file = self.data_dir / "cache.json"
            if cache_file.exists():
                with open(cache_file) as f:
                    cache_data = json.load(f)

                for key, cred_data in cache_data.items():
                    # Decrypt value if needed
                    if cred_data.get("encrypted", True):
                        value = self.encryption_service.decrypt(
                            cred_data["value"],
                            cred_data["salt"],
                            cred_data.get("key_id", "default"),
                        )
                    else:
                        value = cred_data["value"]

                    # Create credential object
                    cred_data["value"] = value
                    credential = Credential.from_dict(cred_data)
                    self._cache[key] = credential

        except Exception:
            # If cache loading fails, start with empty cache
            self._cache = {}

    def _save_cache(self):
        """Save cache to disk."""
        try:
            cache_file = self.data_dir / "cache.json"
            cache_data = {}

            for key, credential in self._cache.items():
                cred_data = credential.to_dict()

                # Encrypt value if needed
                if credential.encrypted:
                    encrypted_value, salt = self.encryption_service.encrypt(credential.value)
                    cred_data["value"] = encrypted_value
                    cred_data["salt"] = salt
                    cred_data["key_id"] = "default"
                else:
                    cred_data["salt"] = ""
                    cred_data["key_id"] = "default"

                cache_data[key] = cred_data

            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

        except Exception:
            # If cache saving fails, continue without error
            pass

    def store(self, credential: Credential) -> bool:
        """Store credential in encrypted file."""
        try:
            self._cache[credential.key] = credential
            self._save_cache()
            return True
        except Exception:
            return False

    def retrieve(self, key: str) -> Credential | None:
        """Retrieve credential from encrypted file."""
        return self._cache.get(key)

    def delete(self, key: str) -> bool:
        """Delete credential from encrypted file."""
        try:
            if key in self._cache:
                del self._cache[key]
                self._save_cache()
            return True
        except Exception:
            return False

    def list_keys(self) -> list[str]:
        """List all credential keys."""
        return list(self._cache.keys())

    def search(self, search: CredentialSearch) -> list[Credential]:
        """Search credentials."""
        results = []

        for credential in self._cache.values():
            if self._matches_search(credential, search):
                results.append(credential)

        return results

    def _matches_search(self, credential: Credential, search: CredentialSearch) -> bool:
        """Check if credential matches search criteria."""
        if search.name and search.name.lower() not in credential.name.lower():
            return False

        if search.type and credential.type != search.type:
            return False

        if search.scope and credential.scope != search.scope:
            return False

        if search.project_id and credential.project_id != search.project_id:
            return False

        if search.environment and credential.environment != search.environment:
            return False

        if search.service and credential.service != search.service:
            return False

        if search.tags:
            if not any(tag in credential.tags for tag in search.tags):
                return False

        if search.expired_only and not credential.is_expired:
            return False

        return not (search.valid_only and not credential.is_valid)


class CompositeStore(CredentialStore):
    """Composite storage that tries multiple backends."""

    def __init__(self, stores: list[CredentialStore]):
        """Initialize composite store.

        Args:
            stores: List of storage backends to try
        """
        self.stores = stores

    def store(self, credential: Credential) -> bool:
        """Store credential in all backends."""
        success = False
        for store in self.stores:
            if store.store(credential):
                success = True
        return success

    def retrieve(self, key: str) -> Credential | None:
        """Retrieve credential from first available backend."""
        for store in self.stores:
            credential = store.retrieve(key)
            if credential:
                return credential
        return None

    def delete(self, key: str) -> bool:
        """Delete credential from all backends."""
        success = False
        for store in self.stores:
            if store.delete(key):
                success = True
        return success

    def list_keys(self) -> list[str]:
        """List keys from all backends."""
        all_keys = set()
        for store in self.stores:
            all_keys.update(store.list_keys())
        return list(all_keys)

    def search(self, search: CredentialSearch) -> list[Credential]:
        """Search all backends."""
        all_credentials = []
        for store in self.stores:
            all_credentials.extend(store.search(search))

        # Remove duplicates based on credential ID
        seen_ids = set()
        unique_credentials = []
        for credential in all_credentials:
            if credential.id not in seen_ids:
                seen_ids.add(credential.id)
                unique_credentials.append(credential)

        return unique_credentials


__all__ = [
    "CompositeStore",
    "CredentialStore",
    "EncryptedFileStore",
    "KeyringStore",
]
