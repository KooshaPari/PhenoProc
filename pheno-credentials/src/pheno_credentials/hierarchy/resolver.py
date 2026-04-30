"""
Credential resolver for hierarchical scoping.
"""

from typing import Any
from uuid import UUID

from ..models import Credential
from ..storage import CredentialStore
from .manager import HierarchyManager


class CredentialResolver:
    """Resolves credentials using hierarchical scoping."""

    def __init__(self, credential_store: CredentialStore, hierarchy_manager: HierarchyManager):
        """Initialize credential resolver.

        Args:
            credential_store: Credential store
            hierarchy_manager: Hierarchy manager
        """
        self.credential_store = credential_store
        self.hierarchy_manager = hierarchy_manager

    def resolve_credential(self, name: str, scope_path: str, hierarchy_name: str = "default") -> Credential | None:
        """Resolve credential using hierarchical scoping.

        Args:
            name: Credential name
            scope_path: Current scope path
            hierarchy_name: Hierarchy name

        Returns:
            Resolved credential
        """
        # Get scope paths in resolution order
        scope_paths = self._get_resolution_paths(scope_path, hierarchy_name)

        # Try each scope path
        for scope_path in scope_paths:
            # Try different key variations
            keys_to_try = [
                name,
                f"{scope_path}_{name}",
                f"{scope_path.split('.')[-1]}_{name}",  # Last part of scope
            ]

            for key in keys_to_try:
                credential = self.credential_store.retrieve(key)
                if credential and credential.is_valid:
                    return credential

        return None

    def resolve_credentials_for_scope(self, scope_path: str, hierarchy_name: str = "default") -> list[Credential]:
        """Resolve all credentials for a scope.

        Args:
            scope_path: Scope path
            hierarchy_name: Hierarchy name

        Returns:
            List of credentials
        """
        # Get scope paths in resolution order
        scope_paths = self._get_resolution_paths(scope_path, hierarchy_name)

        all_credentials = []
        seen_credentials = set()

        # Collect credentials from all scope paths
        for scope_path in scope_paths:
            # Get all credentials for this scope
            scope_credentials = self._get_credentials_for_scope_path(scope_path)

            for credential in scope_credentials:
                if credential.id not in seen_credentials:
                    all_credentials.append(credential)
                    seen_credentials.add(credential.id)

        return all_credentials

    def get_credential_scope_info(self, name: str, scope_path: str, hierarchy_name: str = "default") -> dict[str, Any]:
        """Get credential scope information.

        Args:
            name: Credential name
            scope_path: Current scope path
            hierarchy_name: Hierarchy name

        Returns:
            Scope information
        """
        scope_paths = self._get_resolution_paths(scope_path, hierarchy_name)

        info = {
            "credential_name": name,
            "current_scope": scope_path,
            "resolution_paths": scope_paths,
            "found_in_scopes": [],
            "credential_sources": [],
        }

        # Check each scope path
        for scope_path in scope_paths:
            keys_to_try = [
                name,
                f"{scope_path}_{name}",
                f"{scope_path.split('.')[-1]}_{name}",
            ]

            for key in keys_to_try:
                credential = self.credential_store.retrieve(key)
                if credential and credential.is_valid:
                    info["found_in_scopes"].append(scope_path)
                    info["credential_sources"].append({
                        "scope": scope_path,
                        "key": key,
                        "credential_id": str(credential.id),
                        "type": credential.type.value,
                        "scope_type": credential.scope.value,
                    })
                    break

        return info

    def _get_resolution_paths(self, scope_path: str, hierarchy_name: str) -> list[str]:
        """Get credential resolution paths for a scope.

        Args:
            scope_path: Current scope path
            hierarchy_name: Hierarchy name

        Returns:
            List of scope paths in resolution order
        """
        hierarchy = self.hierarchy_manager.get_hierarchy(hierarchy_name)
        if not hierarchy:
            return [scope_path, "global"]

        # Find the node for the current scope
        node = hierarchy.get_node_by_path(scope_path)
        if not node:
            return [scope_path, "global"]

        # Get resolution paths from hierarchy
        return hierarchy.get_credential_scope_paths(node.id)

    def _get_credentials_for_scope_path(self, scope_path: str) -> list[Credential]:
        """Get credentials for a specific scope path.

        Args:
            scope_path: Scope path

        Returns:
            List of credentials
        """
        # This is a simplified implementation
        # In a real system, you'd query the credential store
        # for credentials matching the scope path

        all_credentials = self.credential_store.list_credentials()
        scope_credentials = []

        for credential in all_credentials:
            # Check if credential belongs to this scope
            if self._credential_belongs_to_scope(credential, scope_path):
                scope_credentials.append(credential)

        return scope_credentials

    def _credential_belongs_to_scope(self, credential: Credential, scope_path: str) -> bool:
        """Check if credential belongs to a scope.

        Args:
            credential: Credential to check
            scope_path: Scope path

        Returns:
            True if credential belongs to scope
        """
        # Check if credential name contains scope path
        if scope_path in credential.name:
            return True

        # Check if credential project_id matches scope
        if credential.project_id and scope_path.endswith(credential.project_id):
            return True

        # Check if credential scope matches
        return bool(credential.scope.value == "global" and scope_path == "global")

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
        # Determine the appropriate key for the scope
        key = self._get_credential_key_for_scope(name, scope_path)

        # Create credential
        return self.credential_store.store_credential(
            name=key,
            value=value,
            credential_type=credential_type,
            scope="project",  # Will be overridden by scope_path
            description=f"Credential for scope {scope_path}",
        )

    def _get_credential_key_for_scope(self, name: str, scope_path: str) -> str:
        """Get credential key for a scope.

        Args:
            name: Credential name
            scope_path: Scope path

        Returns:
            Credential key
        """
        # Use the last part of the scope path as prefix
        scope_parts = scope_path.split(".")
        if len(scope_parts) > 1:
            prefix = scope_parts[-1]
            return f"{prefix}_{name}"

        return name

    def get_scope_hierarchy_tree(self, hierarchy_name: str = "default") -> dict[str, Any]:
        """Get scope hierarchy tree.

        Args:
            hierarchy_name: Hierarchy name

        Returns:
            Hierarchy tree structure
        """
        hierarchy = self.hierarchy_manager.get_hierarchy(hierarchy_name)
        if not hierarchy:
            return {}

        def build_tree(node_id: UUID) -> dict[str, Any]:
            node = hierarchy.get_node(node_id)
            if not node:
                return {}

            tree = {
                "id": str(node.id),
                "name": node.name,
                "type": node.type.value,
                "path": node.path,
                "description": node.description,
                "children": [],
            }

            for child_id in node.children_ids:
                child_tree = build_tree(child_id)
                if child_tree:
                    tree["children"].append(child_tree)

            return tree

        if hierarchy.root_node_id:
            return build_tree(hierarchy.root_node_id)

        return {}

    def get_scope_statistics(self, hierarchy_name: str = "default") -> dict[str, Any]:
        """Get scope statistics.

        Args:
            hierarchy_name: Hierarchy name

        Returns:
            Statistics dictionary
        """
        hierarchy = self.hierarchy_manager.get_hierarchy(hierarchy_name)
        if not hierarchy:
            return {}

        stats = self.hierarchy_manager.get_hierarchy_stats(hierarchy_name)

        # Add credential statistics
        all_credentials = self.credential_store.list_keys()
        scope_credential_counts = {}

        for credential_key in all_credentials:
            # Determine which scope this credential belongs to
            scope = self._determine_credential_scope(credential_key)
            scope_credential_counts[scope] = scope_credential_counts.get(scope, 0) + 1

        stats["credential_counts_by_scope"] = scope_credential_counts
        stats["total_credentials"] = len(all_credentials)

        return stats

    def _determine_credential_scope(self, credential_key: str) -> str:
        """Determine which scope a credential belongs to.

        Args:
            credential_key: Credential key to analyze

        Returns:
            Scope path
        """
        # Check if credential key contains scope information
        if "_" in credential_key:
            parts = credential_key.split("_")
            if len(parts) > 1:
                # Assume the first part is the scope
                return parts[0]

        # Default to global
        return "global"


__all__ = ["CredentialResolver"]
