"""
Enhanced environment variable management.
"""

import os
from pathlib import Path
from typing import Any

from .models import Credential, CredentialScope, ProjectInfo
from .storage import CredentialStore


class EnvironmentManager:
    """Enhanced environment variable manager with credential integration."""

    def __init__(self, credential_store: CredentialStore | None = None):
        """Initialize environment manager.

        Args:
            credential_store: Credential store for secure credential retrieval
        """
        self.credential_store = credential_store
        self._env_cache: dict[str, str] = {}
        self._project_info: ProjectInfo | None = None
        self._load_env_files()

    def _load_env_files(self):
        """Load environment variables from .env files."""
        # Load .env files in order of priority
        env_files = [
            ".env.local",
            ".env",
            ".env.development",
            ".env.production",
        ]

        for env_file in env_files:
            if Path(env_file).exists():
                self._load_env_file(env_file)

    def _load_env_file(self, file_path: str | Path):
        """Load environment variables from a file.

        Args:
            file_path: Path to .env file
        """
        try:
            with open(file_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        self._env_cache[key] = value

        except Exception:
            # If file loading fails, continue without error
            pass

    def set_project(self, project_info: ProjectInfo):
        """Set current project context.

        Args:
            project_info: Project information
        """
        self._project_info = project_info

    def get_project_id(self) -> str | None:
        """Get current project ID.

        Returns:
            Project ID if set, None otherwise
        """
        return self._project_info.id if self._project_info else None

    def get(self, key: str, default: Any = None, prompt: bool = True) -> str:
        """Get environment variable with credential fallback.

        Resolution order:
        1. Secure credential store
        2. Environment variables
        3. .env file cache
        4. Default value
        5. Interactive prompt (if enabled)

        Args:
            key: Environment variable key
            default: Default value if not found
            prompt: Whether to prompt user if not found

        Returns:
            Environment variable value
        """
        # 1. Try secure credential store
        if self.credential_store:
            credential = self._get_credential_from_store(key)
            if credential and credential.is_valid:
                return credential.value

        # 2. Try environment variables
        value = os.getenv(key)
        if value is not None:
            return value

        # 3. Try .env file cache
        value = self._env_cache.get(key)
        if value is not None:
            return value

        # 4. Try default value
        if default is not None:
            return str(default)

        # 5. Prompt user if enabled
        if prompt:
            return self._prompt_for_value(key)

        return ""

    def _get_credential_from_store(self, key: str) -> Credential | None:
        """Get credential from store with project context.

        Args:
            key: Credential key

        Returns:
            Credential if found
        """
        if not self.credential_store:
            return None

        # Try different key variations
        keys_to_try = [key]

        if self._project_info:
            # Try project-scoped key
            keys_to_try.append(f"{self._project_info.short_id}_{key}")

        # Try environment-scoped key
        env = os.getenv("ENVIRONMENT", "development")
        keys_to_try.append(f"{env}_{key}")

        for try_key in keys_to_try:
            credential = self.credential_store.retrieve(try_key)
            if credential and credential.is_valid:
                return credential

        return None

    def _prompt_for_value(self, key: str) -> str:
        """Prompt user for environment variable value.

        Args:
            key: Environment variable key

        Returns:
            User-provided value
        """
        try:
            import getpass

            # Determine if this is a password field
            is_password = any(pw_key in key.lower() for pw_key in ["password", "secret", "key", "token"])

            if is_password:
                value = getpass.getpass(f"Enter {key}: ")
            else:
                value = input(f"Enter {key}: ")

            # Store in credential store if available
            if self.credential_store and value:
                self._store_credential(key, value)

            return value

        except (KeyboardInterrupt, EOFError):
            return ""

    def _store_credential(self, key: str, value: str):
        """Store credential in secure store.

        Args:
            key: Credential key
            value: Credential value
        """
        if not self.credential_store:
            return

        # Determine credential type
        cred_type = self._infer_credential_type(key)

        # Determine scope
        scope = CredentialScope.PROJECT if self._project_info else CredentialScope.GLOBAL

        # Create credential
        credential = Credential(
            name=key,
            value=value,
            type=cred_type,
            scope=scope,
            project_id=self._project_info.id if self._project_info else None,
            environment=os.getenv("ENVIRONMENT", "development"),
            service=self._infer_service(key),
            description=f"Environment variable: {key}",
        )

        # Store credential
        self.credential_store.store(credential)

    def _infer_credential_type(self, key: str) -> str:
        """Infer credential type from key name.

        Args:
            key: Credential key

        Returns:
            Inferred credential type
        """
        key_lower = key.lower()

        if "api_key" in key_lower or "apikey" in key_lower:
            return "api_key"
        if "token" in key_lower:
            return "oauth_token"
        if "password" in key_lower or "passwd" in key_lower:
            return "password"
        if "secret" in key_lower:
            return "secret"
        if "cert" in key_lower or "certificate" in key_lower:
            return "certificate"
        if "ssh" in key_lower:
            return "ssh_key"
        if "database" in key_lower or "db" in key_lower:
            return "database_url"
        return "secret"

    def _infer_service(self, key: str) -> str | None:
        """Infer service from key name.

        Args:
            key: Credential key

        Returns:
            Inferred service name
        """
        key_lower = key.lower()

        services = {
            "openai": ["openai", "gpt"],
            "github": ["github", "gh"],
            "aws": ["aws", "amazon"],
            "azure": ["azure", "microsoft"],
            "google": ["google", "gcp"],
            "docker": ["docker", "registry"],
            "redis": ["redis"],
            "postgres": ["postgres", "postgresql", "pg"],
            "mysql": ["mysql"],
            "mongodb": ["mongo", "mongodb"],
        }

        for service, keywords in services.items():
            if any(keyword in key_lower for keyword in keywords):
                return service

        return None

    def set(self, key: str, value: str, store_secure: bool = False):
        """Set environment variable.

        Args:
            key: Environment variable key
            value: Environment variable value
            store_secure: Whether to store in secure credential store
        """
        os.environ[key] = value
        self._env_cache[key] = value

        if store_secure and self.credential_store:
            self._store_credential(key, value)

    def unset(self, key: str):
        """Unset environment variable.

        Args:
            key: Environment variable key
        """
        if key in os.environ:
            del os.environ[key]
        if key in self._env_cache:
            del self._env_cache[key]

    def get_all(self, prefix: str = "") -> dict[str, str]:
        """Get all environment variables with optional prefix.

        Args:
            prefix: Optional prefix to filter variables

        Returns:
            Dictionary of environment variables
        """
        all_vars = {}

        # Add environment variables
        for key, value in os.environ.items():
            if not prefix or key.startswith(prefix):
                all_vars[key] = value

        # Add .env file variables
        for key, value in self._env_cache.items():
            if not prefix or key.startswith(prefix):
                all_vars[key] = value

        return all_vars

    def export(self, file_path: str | Path, prefix: str = ""):
        """Export environment variables to file.

        Args:
            file_path: Path to export file
            prefix: Optional prefix to filter variables
        """
        env_vars = self.get_all(prefix)

        with open(file_path, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

    def validate_required(self, required_vars: list[str]) -> dict[str, bool]:
        """Validate that required environment variables are set.

        Args:
            required_vars: List of required variable names

        Returns:
            Dictionary mapping variable names to validation status
        """
        results = {}

        for var in required_vars:
            value = self.get(var, prompt=False)
            results[var] = bool(value)

        return results

    def get_missing_required(self, required_vars: list[str]) -> list[str]:
        """Get list of missing required environment variables.

        Args:
            required_vars: List of required variable names

        Returns:
            List of missing variable names
        """
        missing = []

        for var in required_vars:
            value = self.get(var, prompt=False)
            if not value:
                missing.append(var)

        return missing


__all__ = ["EnvironmentManager"]
