"""
Credentials Broker System for pheno-credentials.

A comprehensive credential management system that provides:
- Secure credential storage using OS keyring and encrypted files
- Project-scoped and global credential management
- Enhanced environment variable resolution
- Interactive credential setup and management
- Audit logging and access tracking
- OAuth flow automation and token refresh

Usage:
    >>> from pheno_credentials import CredentialBroker
    >>> broker = CredentialBroker()
    >>> api_key = broker.get_credential("OPENAI_API_KEY")
    >>> # Automatically resolves from secure store, env vars, or prompts user
"""

from .audit import AuditLogger
from .broker import CredentialBroker, get_credential, get_credential_broker
from .encryption import EncryptionService
from .environment import EnvironmentManager
from .models import Credential, CredentialScope, CredentialType
from .project import ProjectManager
from .storage import CredentialStore, EncryptedFileStore, KeyringStore

__all__ = [
    "AuditLogger",
    "Credential",
    "CredentialBroker",
    "CredentialScope",
    "CredentialStore",
    "CredentialType",
    "EncryptedFileStore",
    "EncryptionService",
    "EnvironmentManager",
    "KeyringStore",
    "ProjectManager",
    "get_credential",
    "get_credential_broker",
]
