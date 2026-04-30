"""
Hierarchy manager for scope management.
"""

import json
from pathlib import Path
from uuid import UUID

from .models import ScopeBuilder, ScopeHierarchy, ScopeNode, ScopeType


class HierarchyManager:
    """Manages scope hierarchies."""

    def __init__(self, data_dir: Path | None = None):
        """Initialize hierarchy manager.

        Args:
            data_dir: Directory for hierarchy data files
        """
        self.data_dir = data_dir or Path.home() / ".pheno" / "hierarchy"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.hierarchies_file = self.data_dir / "hierarchies.json"
        self._hierarchies: dict[str, ScopeHierarchy] = {}
        self._load_hierarchies()

    def _load_hierarchies(self):
        """Load hierarchies from disk."""
        try:
            if self.hierarchies_file.exists():
                with open(self.hierarchies_file) as f:
                    hierarchies_data = json.load(f)

                for name, hierarchy_data in hierarchies_data.items():
                    self._hierarchies[name] = ScopeHierarchy.from_dict(hierarchy_data)

        except Exception:
            # If loading fails, start with empty hierarchies
            self._hierarchies = {}

    def _save_hierarchies(self):
        """Save hierarchies to disk."""
        try:
            hierarchies_data = {
                name: hierarchy.to_dict()
                for name, hierarchy in self._hierarchies.items()
            }

            with open(self.hierarchies_file, "w") as f:
                json.dump(hierarchies_data, f, indent=2)

        except Exception:
            # If saving fails, continue without error
            pass

    def create_hierarchy(self, name: str, description: str | None = None) -> ScopeHierarchy:
        """Create a new scope hierarchy.

        Args:
            name: Hierarchy name
            description: Hierarchy description

        Returns:
            Created hierarchy

        Raises:
            ValueError: If hierarchy already exists
        """
        if name in self._hierarchies:
            raise ValueError(f"Hierarchy '{name}' already exists")

        hierarchy = ScopeHierarchy(name=name, description=description)
        self._hierarchies[name] = hierarchy
        self._save_hierarchies()

        return hierarchy

    def get_hierarchy(self, name: str) -> ScopeHierarchy | None:
        """Get hierarchy by name.

        Args:
            name: Hierarchy name

        Returns:
            Hierarchy if found
        """
        return self._hierarchies.get(name)

    def list_hierarchies(self) -> list[str]:
        """List all hierarchy names.

        Returns:
            List of hierarchy names
        """
        return list(self._hierarchies.keys())

    def delete_hierarchy(self, name: str) -> bool:
        """Delete hierarchy.

        Args:
            name: Hierarchy name

        Returns:
            True if deleted
        """
        if name in self._hierarchies:
            del self._hierarchies[name]
            self._save_hierarchies()
            return True
        return False

    def add_node(self, hierarchy_name: str, node: ScopeNode) -> bool:
        """Add node to hierarchy.

        Args:
            hierarchy_name: Hierarchy name
            node: Node to add

        Returns:
            True if successful
        """
        hierarchy = self.get_hierarchy(hierarchy_name)
        if not hierarchy:
            return False

        success = hierarchy.add_node(node)
        if success:
            self._save_hierarchies()

        return success

    def remove_node(self, hierarchy_name: str, node_id: UUID) -> bool:
        """Remove node from hierarchy.

        Args:
            hierarchy_name: Hierarchy name
            node_id: Node ID to remove

        Returns:
            True if successful
        """
        hierarchy = self.get_hierarchy(hierarchy_name)
        if not hierarchy:
            return False

        success = hierarchy.remove_node(node_id)
        if success:
            self._save_hierarchies()

        return success

    def get_node(self, hierarchy_name: str, node_id: UUID) -> ScopeNode | None:
        """Get node by ID.

        Args:
            hierarchy_name: Hierarchy name
            node_id: Node ID

        Returns:
            Node if found
        """
        hierarchy = self.get_hierarchy(hierarchy_name)
        if not hierarchy:
            return None

        return hierarchy.get_node(node_id)

    def get_node_by_path(self, hierarchy_name: str, path: str) -> ScopeNode | None:
        """Get node by path.

        Args:
            hierarchy_name: Hierarchy name
            path: Node path

        Returns:
            Node if found
        """
        hierarchy = self.get_hierarchy(hierarchy_name)
        if not hierarchy:
            return None

        return hierarchy.get_node_by_path(path)

    def get_credential_scope_paths(self, hierarchy_name: str, node_id: UUID) -> list[str]:
        """Get credential scope paths for a node.

        Args:
            hierarchy_name: Hierarchy name
            node_id: Node ID

        Returns:
            List of scope paths in resolution order
        """
        hierarchy = self.get_hierarchy(hierarchy_name)
        if not hierarchy:
            return []

        return hierarchy.get_credential_scope_paths(node_id)

    def find_scope_for_project(self, project_path: str) -> str | None:
        """Find scope for a project path.

        Args:
            project_path: Project directory path

        Returns:
            Scope path if found
        """
        # This is a simplified implementation
        # In a real system, you'd analyze the project structure
        # to determine the appropriate scope

        project_path_obj = Path(project_path)

        # Look for scope markers in the project
        scope_markers = [
            ".pheno-scope",
            "scope.json",
            ".scope",
        ]

        for marker in scope_markers:
            marker_path = project_path_obj / marker
            if marker_path.exists():
                try:
                    with open(marker_path) as f:
                        scope_data = json.load(f)
                    return scope_data.get("scope_path")
                except Exception:
                    continue

        # Default to global scope
        return "global"

    def create_default_hierarchy(self) -> ScopeHierarchy:
        """Create default hierarchy structure.

        Returns:
            Default hierarchy
        """
        builder = ScopeBuilder("default")

        # Create default hierarchy
        (builder
         .add_global("global", "Global scope for system-wide credentials")
         .add_org("atoms", "ATOMS organization")
         .add_group("infrastructure", "Infrastructure group")
         .add_program("platform", "Platform program")
         .add_portfolio("core-services", "Core services portfolio")
         .add_project("pheno-sdk", "Pheno SDK project")
         .add_project("krouter", "KRouter project")
         .add_project("zen-mcp-server", "Zen MCP Server project")
         .add_project("morph", "Morph project")
        )

        hierarchy = builder.build()
        self._hierarchies["default"] = hierarchy
        self._save_hierarchies()

        return hierarchy

    def get_or_create_default_hierarchy(self) -> ScopeHierarchy:
        """Get or create default hierarchy.

        Returns:
            Default hierarchy
        """
        if "default" not in self._hierarchies:
            return self.create_default_hierarchy()

        return self._hierarchies["default"]

    def validate_hierarchy(self, hierarchy_name: str) -> list[str]:
        """Validate hierarchy integrity.

        Args:
            hierarchy_name: Hierarchy name

        Returns:
            List of validation errors
        """
        hierarchy = self.get_hierarchy(hierarchy_name)
        if not hierarchy:
            return [f"Hierarchy '{hierarchy_name}' not found"]

        return hierarchy.validate_hierarchy()

    def get_hierarchy_stats(self, hierarchy_name: str) -> dict[str, int]:
        """Get hierarchy statistics.

        Args:
            hierarchy_name: Hierarchy name

        Returns:
            Dictionary of statistics
        """
        hierarchy = self.get_hierarchy(hierarchy_name)
        if not hierarchy:
            return {}

        stats = {
            "total_nodes": len(hierarchy.nodes),
            "depth": max((node.depth for node in hierarchy.nodes.values()), default=0),
        }

        # Count by type
        for node_type in ScopeType:
            count = len(hierarchy.get_nodes_by_type(node_type))
            stats[f"{node_type.value}_nodes"] = count

        return stats


__all__ = ["HierarchyManager"]
