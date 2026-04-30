"""
Encryption service for secure credential storage.
"""

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .models import EncryptionKey


class EncryptionService:
    """Service for encrypting and decrypting credential values."""

    def __init__(self, master_password: str | None = None):
        """Initialize encryption service.

        Args:
            master_password: Master password for key derivation. If None, will prompt user.
        """
        self.master_password = master_password
        self._key_cache: dict[str, bytes] = {}

    def _derive_key(self, key_id: str, salt: bytes) -> bytes:
        """Derive encryption key from master password.

        Args:
            key_id: Key identifier
            salt: Salt for key derivation

        Returns:
            Derived encryption key
        """
        cache_key = f"{key_id}:{base64.b64encode(salt).decode()}"

        if cache_key in self._key_cache:
            return self._key_cache[cache_key]

        if not self.master_password:
            self.master_password = self._get_master_password()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
        self._key_cache[cache_key] = key

        return key

    def _get_master_password(self) -> str:
        """Get master password from user.

        Returns:
            Master password
        """
        import getpass

        password = getpass.getpass("Enter master password for credential encryption: ")
        if not password:
            raise ValueError("Master password cannot be empty")
        return password

    def encrypt(self, value: str, key_id: str = "default") -> tuple[str, str]:
        """Encrypt a credential value.

        Args:
            value: Value to encrypt
            key_id: Key identifier

        Returns:
            Tuple of (encrypted_value, salt) as base64 strings
        """
        if not value:
            return "", ""

        # Generate random salt
        salt = os.urandom(16)

        # Derive key
        key = self._derive_key(key_id, salt)

        # Encrypt value
        fernet = Fernet(key)
        encrypted_value = fernet.encrypt(value.encode())

        # Return base64 encoded values
        return (
            base64.urlsafe_b64encode(encrypted_value).decode(),
            base64.urlsafe_b64encode(salt).decode(),
        )

    def decrypt(self, encrypted_value: str, salt: str, key_id: str = "default") -> str:
        """Decrypt a credential value.

        Args:
            encrypted_value: Encrypted value (base64)
            salt: Salt used for encryption (base64)
            key_id: Key identifier

        Returns:
            Decrypted value
        """
        if not encrypted_value or not salt:
            return ""

        try:
            # Decode base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value)
            salt_bytes = base64.urlsafe_b64decode(salt)

            # Derive key
            key = self._derive_key(key_id, salt_bytes)

            # Decrypt value
            fernet = Fernet(key)
            decrypted_bytes = fernet.decrypt(encrypted_bytes)

            return decrypted_bytes.decode()

        except Exception as e:
            raise ValueError(f"Failed to decrypt credential: {e}")

    def generate_key(self) -> EncryptionKey:
        """Generate a new encryption key.

        Returns:
            New encryption key metadata
        """
        import secrets

        key_id = secrets.token_urlsafe(16)
        return EncryptionKey(id=key_id)

    def verify_master_password(self, password: str) -> bool:
        """Verify master password without storing it.

        Args:
            password: Password to verify

        Returns:
            True if password is correct
        """
        # This is a simplified verification - in production, you'd want
        # to store a hash of the master password and verify against it
        return password == self.master_password


__all__ = ["EncryptionService"]
