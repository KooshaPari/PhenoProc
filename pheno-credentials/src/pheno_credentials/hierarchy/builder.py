"""
Scope builder for creating hierarchical structures.
"""

from .models import ScopeBuilder, ScopeHierarchy, ScopeNode, ScopeType


class ScopeBuilder:
    """Builder for creating scope hierarchies."""

    def __init__(self, name: str):
        """Initialize scope builder.

        Args:
            name: Hierarchy name
        """
        self.hierarchy = ScopeHierarchy(name=name)
        self._current_path = ""

    def add_global(self, name: str = "global", description: str | None = None) -> "ScopeBuilder":
        """Add global scope.

        Args:
            name: Global scope name
            description: Description

        Returns:
            Self for chaining
        """
        node = ScopeNode(
            name=name,
            type=ScopeType.GLOBAL,
            path=name,
            description=description,
        )

        self.hierarchy.add_node(node)
        self._current_path = name
        return self

    def add_group(self, name: str, parent_path: str | None = None, description: str | None = None) -> "ScopeBuilder":
        """Add group scope.

        Args:
            name: Group name
            parent_path: Parent path (defaults to current path)
            description: Description

        Returns:
            Self for chaining
        """
        parent_path = parent_path or self._current_path
        path = f"{parent_path}.{name}" if parent_path else name

        parent_node = self.hierarchy.get_node_by_path(parent_path)
        parent_id = parent_node.id if parent_node else None

        node = ScopeNode(
            name=name,
            type=ScopeType.GROUP,
            path=path,
            parent_id=parent_id,
            description=description,
        )

        self.hierarchy.add_node(node)
        self._current_path = path
        return self

    def add_org(self, name: str, parent_path: str | None = None, description: str | None = None) -> "ScopeBuilder":
        """Add organization scope.

        Args:
            name: Organization name
            parent_path: Parent path
            description: Description

        Returns:
            Self for chaining
        """
        return self._add_scope(ScopeType.ORG, name, parent_path, description)

    def add_program(self, name: str, parent_path: str | None = None, description: str | None = None) -> "ScopeBuilder":
        """Add program scope.

        Args:
            name: Program name
            parent_path: Parent path
            description: Description

        Returns:
            Self for chaining
        """
        return self._add_scope(ScopeType.PROGRAM, name, parent_path, description)

    def add_portfolio(self, name: str, parent_path: str | None = None, description: str | None = None) -> "ScopeBuilder":
        """Add portfolio scope.

        Args:
            name: Portfolio name
            parent_path: Parent path
            description: Description

        Returns:
            Self for chaining
        """
        return self._add_scope(ScopeType.PORTFOLIO, name, parent_path, description)

    def add_project(self, name: str, parent_path: str | None = None, description: str | None = None) -> "ScopeBuilder":
        """Add project scope.

        Args:
            name: Project name
            parent_path: Parent path
            description: Description

        Returns:
            Self for chaining
        """
        return self._add_scope(ScopeType.PROJECT, name, parent_path, description)

    def _add_scope(self, scope_type: ScopeType, name: str, parent_path: str | None = None, description: str | None = None) -> "ScopeBuilder":
        """Add scope of any type.

        Args:
            scope_type: Scope type
            name: Scope name
            parent_path: Parent path
            description: Description

        Returns:
            Self for chaining
        """
        parent_path = parent_path or self._current_path
        path = f"{parent_path}.{name}" if parent_path else name

        parent_node = self.hierarchy.get_node_by_path(parent_path)
        parent_id = parent_node.id if parent_node else None

        node = ScopeNode(
            name=name,
            type=scope_type,
            path=path,
            parent_id=parent_id,
            description=description,
        )

        self.hierarchy.add_node(node)
        self._current_path = path
        return self

    def build(self) -> ScopeHierarchy:
        """Build the scope hierarchy.

        Returns:
            Built scope hierarchy
        """
        return self.hierarchy


class ScopeTemplate:
    """Templates for common scope hierarchies."""

    @staticmethod
    def create_enterprise_hierarchy(org_name: str) -> ScopeBuilder:
        """Create enterprise hierarchy template.

        Args:
            org_name: Organization name

        Returns:
            Scope builder
        """
        builder = ScopeBuilder(f"{org_name}-enterprise")

        (builder
         .add_global("global", "Global enterprise scope")
         .add_org(org_name, "Enterprise organization")
         .add_group("infrastructure", "Infrastructure group")
         .add_group("applications", "Applications group")
         .add_group("data", "Data group")
         .add_group("security", "Security group")
        )

        return builder

    @staticmethod
    def create_development_hierarchy(org_name: str) -> ScopeBuilder:
        """Create development hierarchy template.

        Args:
            org_name: Organization name

        Returns:
            Scope builder
        """
        builder = ScopeBuilder(f"{org_name}-development")

        (builder
         .add_global("global", "Global development scope")
         .add_org(org_name, "Development organization")
         .add_group("platform", "Platform group")
         .add_program("core-services", "Core services program")
         .add_portfolio("apis", "APIs portfolio")
         .add_project("pheno-sdk", "Pheno SDK project")
         .add_project("krouter", "KRouter project")
         .add_project("zen-mcp-server", "Zen MCP Server project")
         .add_project("morph", "Morph project")
        )

        return builder

    @staticmethod
    def create_team_hierarchy(team_name: str) -> ScopeBuilder:
        """Create team hierarchy template.

        Args:
            team_name: Team name

        Returns:
            Scope builder
        """
        builder = ScopeBuilder(f"{team_name}-team")

        (builder
         .add_global("global", "Global team scope")
         .add_group(team_name, f"{team_name} team")
         .add_program("active-projects", "Active projects program")
         .add_project("current-sprint", "Current sprint project")
        )

        return builder


__all__ = ["ScopeBuilder", "ScopeTemplate"]
