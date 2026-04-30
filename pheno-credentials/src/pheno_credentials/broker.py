"""
Main credential broker for managing credentials across the system.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from .audit import AuditLogger
from .encryption import EncryptionService
from .environment import EnvironmentManager
from .hierarchy import CredentialResolver, HierarchyManager
from .models import Credential, CredentialSearch, ProjectInfo
from .oauth import (
    AutomationEngine,
    OAuthFlow,
    OAuthFlowManager,
    TokenManager,
    TokenRefreshScheduler,
)
from .project import ProjectManager
from .storage import CompositeStore, EncryptedFileStore, KeyringStore


class CredentialBroker:
    """Main credential broker for managing credentials across the system."""

    def __init__(self, data_dir: Path | None = None, master_password: str | None = None):
        """Initialize credential broker.

        Args:
            data_dir: Directory for credential data
            master_password: Master password for encryption
        """
        self.data_dir = data_dir or Path.home() / ".pheno" / "credentials"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize services
        self.encryption_service = EncryptionService(master_password)
        self.project_manager = ProjectManager(self.data_dir)
        self.audit_logger = AuditLogger(self.data_dir)

        # Initialize storage backends
        self._init_storage()

        # Initialize environment manager
        self.environment_manager = EnvironmentManager(self.credential_store)

        # Initialize OAuth components
        self.oauth_flow_manager = OAuthFlowManager()
        self.token_manager = TokenManager(self.credential_store, self.oauth_flow_manager)
        self.token_scheduler = TokenRefreshScheduler(self.token_manager)
        self.automation_engine = AutomationEngine(self.credential_store, self.token_manager)

        # Initialize hierarchical scoping
        self.hierarchy_manager = HierarchyManager(self.data_dir)
        self.credential_resolver = CredentialResolver(self.credential_store, self.hierarchy_manager)

        # Set up project context
        self._setup_project_context()

    def _init_storage(self):
        """Initialize credential storage backends."""
        # Create composite store with multiple backends
        stores = []

        # Add keyring store if available
        try:
            keyring_store = KeyringStore()
            stores.append(keyring_store)
        except ImportError:
            pass

        # Add encrypted file store
        file_store = EncryptedFileStore(
            data_dir=self.data_dir,
            encryption_service=self.encryption_service,
        )
        stores.append(file_store)

        # Create composite store
        self.credential_store = CompositeStore(stores)

    def _setup_project_context(self):
        """Set up project context from current directory."""
        project = self.project_manager.detect_project_from_cwd()
        if project:
            self.environment_manager.set_project(project)

    def set_project(self, project_id: str):
        """Set current project context.

        Args:
            project_id: Project identifier
        """
        project = self.project_manager.get_project(project_id)
        if project:
            self.environment_manager.set_project(project)
        else:
            raise ValueError(f"Project '{project_id}' not found")

    def create_project(self, project_id: str, name: str, description: str | None = None,
                      path: str | None = None) -> ProjectInfo:
        """Create a new project.

        Args:
            project_id: Unique project identifier
            name: Project name
            description: Optional project description
            path: Optional project path

        Returns:
            Created project info
        """
        project = self.project_manager.create_project(project_id, name, description, path)
        self.environment_manager.set_project(project)
        return project

    def store_credential(self, name: str, value: str, credential_type: str = "secret",
                        scope: str = "project", service: str | None = None,
                        description: str | None = None, tags: list[str] | None = None,
                        expires_at: datetime | None = None, auto_refresh: bool = False) -> bool:
        """Store a credential.

        Args:
            name: Credential name
            value: Credential value
            credential_type: Type of credential
            scope: Credential scope (global, project, environment)
            service: Service provider
            description: Human-readable description
            tags: Tags for organization
            expires_at: Expiration timestamp
            auto_refresh: Whether to auto-refresh OAuth tokens

        Returns:
            True if successful
        """
        try:
            # Get current project context
            project_id = self.environment_manager.get_project_id()

            # Create credential
            credential = Credential(
                name=name,
                value=value,
                type=credential_type,
                scope=scope,
                project_id=project_id if scope == "project" else None,
                environment=self.environment_manager.get("ENVIRONMENT", "development"),
                service=service,
                description=description,
                tags=tags or [],
                expires_at=expires_at,
                auto_refresh=auto_refresh,
            )

            # Store credential
            success = self.credential_store.store(credential)

            if success:
                # Log access
                self.audit_logger.log_access(
                    credential_id=str(credential.id),
                    action="write",
                    success=True,
                    project_id=project_id,
                )

            return success

        except Exception as e:
            # Log error
            self.audit_logger.log_access(
                credential_id="unknown",
                action="write",
                success=False,
                error_message=str(e),
            )
            return False

    def get_credential(self, name: str, default: Any = None, prompt: bool = True) -> str:
        """Get a credential value.

        Args:
            name: Credential name
            default: Default value if not found
            prompt: Whether to prompt user if not found

        Returns:
            Credential value
        """
        # Use environment manager for smart resolution
        return self.environment_manager.get(name, default, prompt)

    def get_credential_info(self, name: str) -> Credential | None:
        """Get credential information.

        Args:
            name: Credential name

        Returns:
            Credential info if found
        """
        # Try different key variations
        keys_to_try = [name]

        project_id = self.environment_manager.get_project_id()
        if project_id:
            keys_to_try.append(f"{project_id[:4]}_{name}")

        env = self.environment_manager.get("ENVIRONMENT", "development")
        keys_to_try.append(f"{env}_{name}")

        for key in keys_to_try:
            credential = self.credential_store.retrieve(key)
            if credential and credential.is_valid:
                # Log access
                self.audit_logger.log_access(
                    credential_id=str(credential.id),
                    action="read",
                    success=True,
                    project_id=project_id,
                )
                return credential

        return None

    def delete_credential(self, name: str) -> bool:
        """Delete a credential.

        Args:
            name: Credential name

        Returns:
            True if successful
        """
        try:
            # Get credential info first
            credential = self.get_credential_info(name)
            if not credential:
                return False

            # Delete credential
            success = self.credential_store.delete(credential.key)

            if success:
                # Log access
                self.audit_logger.log_access(
                    credential_id=str(credential.id),
                    action="delete",
                    success=True,
                    project_id=credential.project_id,
                )

            return success

        except Exception as e:
            # Log error
            self.audit_logger.log_access(
                credential_id="unknown",
                action="delete",
                success=False,
                error_message=str(e),
            )
            return False

    def list_credentials(self, scope: str | None = None,
                        project_id: str | None = None) -> list[Credential]:
        """List credentials.

        Args:
            scope: Filter by scope
            project_id: Filter by project ID

        Returns:
            List of credentials
        """
        search = CredentialSearch(
            scope=scope,
            project_id=project_id,
        )

        return self.credential_store.search(search)

    def search_credentials(self, search: CredentialSearch) -> list[Credential]:
        """Search credentials.

        Args:
            search: Search criteria

        Returns:
            List of matching credentials
        """
        return self.credential_store.search(search)

    def validate_credentials(self, required_credentials: list[str]) -> dict[str, bool]:
        """Validate that required credentials are available.

        Args:
            required_credentials: List of required credential names

        Returns:
            Dictionary mapping credential names to validation status
        """
        results = {}

        for cred_name in required_credentials:
            credential = self.get_credential_info(cred_name)
            results[cred_name] = credential is not None and credential.is_valid

        return results

    def refresh_oauth_token(self, name: str) -> bool:
        """Refresh OAuth token.

        Args:
            name: Credential name

        Returns:
            True if successful
        """
        credential = self.get_credential_info(name)
        if not credential or not credential.auto_refresh:
            return False

        # This would typically implement OAuth refresh flow
        # For now, just return False
        return False

    def export_credentials(self, file_path: Path, format: str = "json",
                          scope: str | None = None) -> bool:
        """Export credentials to file.

        Args:
            file_path: Path to export file
            format: Export format (json, csv)
            scope: Filter by scope

        Returns:
            True if successful
        """
        try:
            credentials = self.list_credentials(scope=scope)

            if format == "json":
                import json
                with open(file_path, "w") as f:
                    json.dump([cred.to_dict() for cred in credentials], f, indent=2)

            elif format == "csv":
                import csv
                if credentials:
                    with open(file_path, "w", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=credentials[0].to_dict().keys())
                        writer.writeheader()
                        for cred in credentials:
                            writer.writerow(cred.to_dict())

            else:
                raise ValueError(f"Unsupported export format: {format}")

            return True

        except Exception:
            return False

    def get_audit_log(self, credential_id: str | None = None,
                     limit: int = 100) -> list[dict[str, Any]]:
        """Get audit log.

        Args:
            credential_id: Filter by credential ID
            limit: Maximum number of entries

        Returns:
            List of audit log entries
        """
        accesses = self.audit_logger.get_access_log(
            credential_id=credential_id,
            limit=limit,
        )

        return [access.to_dict() for access in accesses]

    def get_security_alerts(self) -> list[dict[str, str]]:
        """Get security alerts.

        Returns:
            List of security alerts
        """
        return self.audit_logger.get_security_alerts()

    def cleanup_expired_credentials(self) -> int:
        """Clean up expired credentials.

        Returns:
            Number of credentials cleaned up
        """
        credentials = self.list_credentials()
        cleaned_count = 0

        for credential in credentials:
            if credential.is_expired:
                if self.delete_credential(credential.name):
                    cleaned_count += 1

        return cleaned_count

    def get_stats(self) -> dict[str, Any]:
        """Get credential broker statistics.

        Returns:
            Dictionary of statistics
        """
        credentials = self.list_credentials()

        stats = {
            "total_credentials": len(credentials),
            "expired_credentials": sum(1 for c in credentials if c.is_expired),
            "valid_credentials": sum(1 for c in credentials if c.is_valid),
            "global_credentials": sum(1 for c in credentials if c.scope == "global"),
            "project_credentials": sum(1 for c in credentials if c.scope == "project"),
            "environment_credentials": sum(1 for c in credentials if c.scope == "environment"),
            "oauth_tokens": sum(1 for c in credentials if c.type == "oauth_token"),
            "api_keys": sum(1 for c in credentials if c.type == "api_key"),
        }

        # Add OAuth statistics
        oauth_stats = self.token_manager.get_refresh_status()
        stats.update({
            "oauth_refresh_jobs": oauth_stats,
            "total_refresh_jobs": sum(oauth_stats.values()),
        })

        # Add automation statistics
        automation_stats = self.automation_engine.get_automation_status()
        stats.update({
            "automation_rules": automation_stats["total_rules"],
            "enabled_rules": automation_stats["enabled_rules"],
            "automation_events": automation_stats["total_events"],
        })

        return stats

    # OAuth Methods

    async def start_oauth_flow(self, flow: OAuthFlow) -> tuple[str, str]:
        """Start OAuth flow.

        Args:
            flow: OAuth flow configuration

        Returns:
            Tuple of (authorization_url, state)
        """
        return await self.oauth_flow_manager.start_flow(flow)

    async def complete_oauth_flow(self, code: str, state: str) -> bool:
        """Complete OAuth flow.

        Args:
            code: Authorization code
            state: State parameter

        Returns:
            True if successful
        """
        try:
            token = await self.oauth_flow_manager.complete_flow(code, state)

            # Find the flow that was used
            flow = await self._find_flow_for_state(state)
            if flow:
                await self.token_manager.store_token(token, flow)
                return True

            return False
        except Exception:
            return False

    async def refresh_oauth_token(self, flow: OAuthFlow) -> bool:
        """Refresh OAuth token.

        Args:
            flow: OAuth flow configuration

        Returns:
            True if successful
        """
        try:
            refreshed_token = await self.token_manager.refresh_token(flow)
            return refreshed_token is not None
        except Exception:
            return False

    async def revoke_oauth_token(self, flow: OAuthFlow) -> bool:
        """Revoke OAuth token.

        Args:
            flow: OAuth flow configuration

        Returns:
            True if successful
        """
        return await self.token_manager.revoke_token(flow)

    async def start_services(self):
        """Start background services."""
        await self.token_scheduler.start()
        await self.automation_engine.start()

    async def stop_services(self):
        """Stop background services."""
        await self.token_scheduler.stop()
        await self.automation_engine.stop()

    # Automation Methods

    def add_automation_rule(self, rule) -> bool:
        """Add automation rule.

        Args:
            rule: Automation rule

        Returns:
            True if successful
        """
        return self.automation_engine.add_rule(rule)

    def remove_automation_rule(self, rule_id: str) -> bool:
        """Remove automation rule.

        Args:
            rule_id: Rule ID

        Returns:
            True if successful
        """
        return self.automation_engine.remove_rule(rule_id)

    def list_automation_rules(self):
        """List automation rules.

        Returns:
            List of automation rules
        """
        return self.automation_engine.list_rules()

    async def trigger_automation_event(self, event_type: str, source: str, data: dict[str, Any] | None = None):
        """Trigger automation event.

        Args:
            event_type: Event type
            source: Event source
            data: Event data
        """
        await self.automation_engine.trigger_event(event_type, source, data)

    async def _find_flow_for_state(self, state: str):
        """Find OAuth flow for state.

        Args:
            state: State parameter

        Returns:
            OAuth flow if found
        """
        # This is a simplified implementation
        # In a real system, you'd maintain a mapping between states and flows
        return

    # Hierarchical Scoping Methods

    def create_hierarchy(self, name: str, description: str | None = None):
        """Create a new scope hierarchy.

        Args:
            name: Hierarchy name
            description: Hierarchy description

        Returns:
            Created hierarchy
        """
        return self.hierarchy_manager.create_hierarchy(name, description)

    def get_hierarchy(self, name: str = "default"):
        """Get scope hierarchy.

        Args:
            name: Hierarchy name

        Returns:
            Scope hierarchy
        """
        return self.hierarchy_manager.get_hierarchy(name)

    def get_or_create_default_hierarchy(self):
        """Get or create default hierarchy.

        Returns:
            Default hierarchy
        """
        return self.hierarchy_manager.get_or_create_default_hierarchy()

    def resolve_credential_hierarchical(self, name: str, scope_path: str, hierarchy_name: str = "default") -> str:
        """Resolve credential using hierarchical scoping.

        Args:
            name: Credential name
            scope_path: Current scope path
            hierarchy_name: Hierarchy name

        Returns:
            Resolved credential value
        """
        credential = self.credential_resolver.resolve_credential(name, scope_path, hierarchy_name)
        if credential and credential.is_valid:
            return credential.value
        return ""

    def get_scope_credentials(self, scope_path: str, hierarchy_name: str = "default"):
        """Get all credentials for a scope.

        Args:
            scope_path: Scope path
            hierarchy_name: Hierarchy name

        Returns:
            List of credentials
        """
        return self.credential_resolver.resolve_credentials_for_scope(scope_path, hierarchy_name)

    def create_scope_credential(self, name: str, value: str, scope_path: str,
                               credential_type: str = "secret", hierarchy_name: str = "default") -> bool:
        """Create credential in a specific scope.

        Args:
            name: Credential name
            value: Credential value
            scope_path: Scope path
            credential_type: Credential type
            hierarchy_name: Hierarchy name

        Returns:
            True if successful
        """
        return self.credential_resolver.create_scope_credential(
            name, value, scope_path, credential_type, hierarchy_name,
        )

    def get_scope_hierarchy_tree(self, hierarchy_name: str = "default"):
        """Get scope hierarchy tree.

        Args:
            hierarchy_name: Hierarchy name

        Returns:
            Hierarchy tree structure
        """
        return self.credential_resolver.get_scope_hierarchy_tree(hierarchy_name)

    def get_scope_statistics(self, hierarchy_name: str = "default"):
        """Get scope statistics.

        Args:
            hierarchy_name: Hierarchy name

        Returns:
            Statistics dictionary
        """
        return self.credential_resolver.get_scope_statistics(hierarchy_name)

    def find_scope_for_project(self, project_path: str) -> str:
        """Find scope for a project.

        Args:
            project_path: Project directory path

        Returns:
            Scope path
        """
        return self.hierarchy_manager.find_scope_for_project(project_path)


# Global credential broker instance
_credential_broker: CredentialBroker | None = None


def get_credential_broker() -> CredentialBroker:
    """Get the global credential broker instance.

    Returns:
        Global credential broker instance
    """
    global _credential_broker

    if _credential_broker is None:
        _credential_broker = CredentialBroker()

    return _credential_broker


def get_credential(name: str, default: Any = None, prompt: bool = True) -> str:
    """Convenience function to get a credential.

    Args:
        name: Credential name
        default: Default value if not found
        prompt: Whether to prompt user if not found

    Returns:
        Credential value
    """
    return get_credential_broker().get_credential(name, default, prompt)


__all__ = [
    "CredentialBroker",
    "get_credential",
    "get_credential_broker",
]
