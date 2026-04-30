"""
Hierarchical scoping models and data structures.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ScopeType(StrEnum):
    """Scope type enumeration."""

    GLOBAL = "global"
    GROUP = "group"
    ORG = "org"
    PROGRAM = "program"
    PORTFOLIO = "portfolio"
    PROJECT = "project"
    ENVIRONMENT = "environment"
    USER = "user"


class ScopeRelationship(StrEnum):
    """Scope relationship types."""

    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    ANCESTOR = "ancestor"
    DESCENDANT = "descendant"
    PEER = "peer"


class ScopeNode(BaseModel):
    """A node in the scope hierarchy."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Node name")
    type: ScopeType = Field(..., description="Node type")
    path: str = Field(..., description="Hierarchical path (e.g., 'org.group.subgroup')")
    parent_id: UUID | None = Field(None, description="Parent node ID")
    children_ids: list[UUID] = Field(default_factory=list, description="Child node IDs")

    # Metadata
    description: str | None = Field(None, description="Node description")
    tags: list[str] = Field(default_factory=list, description="Tags for organization")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime | None = Field(None, description="Last access timestamp")

    # Access control
    is_active: bool = Field(True, description="Whether node is active")
    access_level: str = Field("read", description="Access level (read, write, admin)")
    inherits_from_parent: bool = Field(True, description="Whether to inherit from parent")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v):
        """Validate hierarchical path."""
        if not v or not v.strip():
            raise ValueError("Path cannot be empty")

        # Path should be dot-separated
        parts = v.split(".")
        if not all(part.strip() for part in parts):
            raise ValueError("Path parts cannot be empty")

        return v

    @property
    def depth(self) -> int:
        """Get node depth in hierarchy."""
        return len(self.path.split("."))

    @property
    def parent_path(self) -> str | None:
        """Get parent path."""
        parts = self.path.split(".")
        if len(parts) <= 1:
            return None
        return ".".join(parts[:-1])

    @property
    def is_root(self) -> bool:
        """Check if node is root (global)."""
        return self.type == ScopeType.GLOBAL

    @property
    def is_leaf(self) -> bool:
        """Check if node is leaf (has no children)."""
        return len(self.children_ids) == 0

    def get_ancestor_paths(self) -> list[str]:
        """Get all ancestor paths."""
        paths = []
        current_path = self.parent_path

        while current_path:
            paths.append(current_path)
            parts = current_path.split(".")
            if len(parts) <= 1:
                break
            current_path = ".".join(parts[:-1])

        return paths

    def is_ancestor_of(self, other: ScopeNode) -> bool:
        """Check if this node is an ancestor of another node."""
        return self.path in other.get_ancestor_paths()

    def is_descendant_of(self, other: ScopeNode) -> bool:
        """Check if this node is a descendant of another node."""
        return other.path in self.get_ancestor_paths()

    def get_relationship(self, other: ScopeNode) -> ScopeRelationship | None:
        """Get relationship to another node."""
        if self.id == other.id:
            return None

        if self.is_ancestor_of(other):
            return ScopeRelationship.ANCESTOR
        if self.is_descendant_of(other):
            return ScopeRelationship.DESCENDANT
        if self.parent_id == other.id:
            return ScopeRelationship.PARENT
        if other.parent_id == self.id:
            return ScopeRelationship.CHILD
        if self.parent_id == other.parent_id:
            return ScopeRelationship.SIBLING
        return ScopeRelationship.PEER


class ScopeHierarchy(BaseModel):
    """Complete scope hierarchy."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Hierarchy name")
    description: str | None = Field(None, description="Hierarchy description")

    # Nodes
    nodes: dict[UUID, ScopeNode] = Field(default_factory=dict, description="All nodes")
    root_node_id: UUID | None = Field(None, description="Root node ID")

    # Indexes for fast lookup
    path_index: dict[str, UUID] = Field(default_factory=dict, description="Path to node ID mapping")
    type_index: dict[ScopeType, list[UUID]] = Field(default_factory=dict, description="Type to node IDs mapping")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(1, description="Hierarchy version")

    def add_node(self, node: ScopeNode) -> bool:
        """Add node to hierarchy.

        Args:
            node: Node to add

        Returns:
            True if successful
        """
        try:
            # Validate parent exists
            if node.parent_id and node.parent_id not in self.nodes:
                return False

            # Add node
            self.nodes[node.id] = node

            # Update indexes
            self.path_index[node.path] = node.id

            if node.type not in self.type_index:
                self.type_index[node.type] = []
            self.type_index[node.type].append(node.id)

            # Update parent's children
            if node.parent_id:
                parent = self.nodes[node.parent_id]
                if node.id not in parent.children_ids:
                    parent.children_ids.append(node.id)

            # Set root if this is the first global node
            if node.type == ScopeType.GLOBAL and not self.root_node_id:
                self.root_node_id = node.id

            self.updated_at = datetime.utcnow()
            self.version += 1

            return True

        except Exception:
            return False

    def remove_node(self, node_id: UUID) -> bool:
        """Remove node from hierarchy.

        Args:
            node_id: Node ID to remove

        Returns:
            True if successful
        """
        try:
            if node_id not in self.nodes:
                return False

            node = self.nodes[node_id]

            # Cannot remove root node
            if node_id == self.root_node_id:
                return False

            # Remove from parent's children
            if node.parent_id and node.parent_id in self.nodes:
                parent = self.nodes[node.parent_id]
                if node_id in parent.children_ids:
                    parent.children_ids.remove(node_id)

            # Remove children first (recursive)
            for child_id in node.children_ids.copy():
                self.remove_node(child_id)

            # Remove from indexes
            if node.path in self.path_index:
                del self.path_index[node.path]

            if node.type in self.type_index and node_id in self.type_index[node.type]:
                self.type_index[node.type].remove(node_id)

            # Remove node
            del self.nodes[node_id]

            self.updated_at = datetime.utcnow()
            self.version += 1

            return True

        except Exception:
            return False

    def get_node(self, node_id: UUID) -> ScopeNode | None:
        """Get node by ID.

        Args:
            node_id: Node ID

        Returns:
            Node if found
        """
        return self.nodes.get(node_id)

    def get_node_by_path(self, path: str) -> ScopeNode | None:
        """Get node by path.

        Args:
            path: Node path

        Returns:
            Node if found
        """
        node_id = self.path_index.get(path)
        if node_id:
            return self.nodes.get(node_id)
        return None

    def get_nodes_by_type(self, node_type: ScopeType) -> list[ScopeNode]:
        """Get nodes by type.

        Args:
            node_type: Node type

        Returns:
            List of nodes
        """
        node_ids = self.type_index.get(node_type, [])
        return [self.nodes[node_id] for node_id in node_ids if node_id in self.nodes]

    def get_children(self, node_id: UUID) -> list[ScopeNode]:
        """Get child nodes.

        Args:
            node_id: Parent node ID

        Returns:
            List of child nodes
        """
        node = self.get_node(node_id)
        if not node:
            return []

        return [self.nodes[child_id] for child_id in node.children_ids if child_id in self.nodes]

    def get_ancestors(self, node_id: UUID) -> list[ScopeNode]:
        """Get ancestor nodes.

        Args:
            node_id: Node ID

        Returns:
            List of ancestor nodes
        """
        node = self.get_node(node_id)
        if not node:
            return []

        ancestors = []
        current = node

        while current.parent_id:
            parent = self.get_node(current.parent_id)
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break

        return ancestors

    def get_descendants(self, node_id: UUID) -> list[ScopeNode]:
        """Get descendant nodes.

        Args:
            node_id: Node ID

        Returns:
            List of descendant nodes
        """
        descendants = []
        node = self.get_node(node_id)
        if not node:
            return descendants

        def collect_descendants(current_node_id: UUID):
            current_node = self.get_node(current_node_id)
            if not current_node:
                return

            for child_id in current_node.children_ids:
                child_node = self.get_node(child_id)
                if child_node:
                    descendants.append(child_node)
                    collect_descendants(child_id)

        collect_descendants(node_id)
        return descendants

    def get_credential_scope_paths(self, node_id: UUID) -> list[str]:
        """Get credential scope paths for a node.

        Args:
            node_id: Node ID

        Returns:
            List of scope paths in resolution order
        """
        node = self.get_node(node_id)
        if not node:
            return []

        # Start with the node itself
        paths = [node.path]

        # Add all ancestors
        ancestors = self.get_ancestors(node_id)
        for ancestor in ancestors:
            paths.append(ancestor.path)

        # Add global if not already included
        if not any(node.type == ScopeType.GLOBAL for node in ancestors):
            global_nodes = self.get_nodes_by_type(ScopeType.GLOBAL)
            if global_nodes:
                paths.append(global_nodes[0].path)

        return paths

    def validate_hierarchy(self) -> list[str]:
        """Validate hierarchy integrity.

        Returns:
            List of validation errors
        """
        errors = []

        # Check for orphaned nodes
        for node_id, node in self.nodes.items():
            if node.parent_id and node.parent_id not in self.nodes:
                errors.append(f"Node {node.name} has invalid parent {node.parent_id}")

        # Check for circular references
        for node_id, node in self.nodes.items():
            if self._has_circular_reference(node_id, set()):
                errors.append(f"Circular reference detected for node {node.name}")

        # Check for duplicate paths
        path_counts = {}
        for node in self.nodes.values():
            path_counts[node.path] = path_counts.get(node.path, 0) + 1

        for path, count in path_counts.items():
            if count > 1:
                errors.append(f"Duplicate path: {path}")

        return errors

    def _has_circular_reference(self, node_id: UUID, visited: set[UUID]) -> bool:
        """Check for circular reference.

        Args:
            node_id: Node ID to check
            visited: Set of visited node IDs

        Returns:
            True if circular reference found
        """
        if node_id in visited:
            return True

        visited.add(node_id)
        node = self.get_node(node_id)

        if node and node.parent_id:
            return self._has_circular_reference(node.parent_id, visited)

        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert hierarchy to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "nodes": {str(node_id): node.to_dict() for node_id, node in self.nodes.items()},
            "root_node_id": str(self.root_node_id) if self.root_node_id else None,
            "path_index": self.path_index,
            "type_index": {node_type.value: [str(node_id) for node_id in node_ids]
                          for node_type, node_ids in self.type_index.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScopeHierarchy:
        """Create hierarchy from dictionary."""
        nodes = {}
        for node_id_str, node_data in data.get("nodes", {}).items():
            node_id = UUID(node_id_str)
            nodes[node_id] = ScopeNode.from_dict(node_data)

        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            description=data.get("description"),
            nodes=nodes,
            root_node_id=UUID(data["root_node_id"]) if data.get("root_node_id") else None,
            path_index=data.get("path_index", {}),
            type_index={ScopeType(node_type): [UUID(node_id) for node_id in node_ids]
                       for node_type, node_ids in data.get("type_index", {}).items()},
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
        )


class ScopeBuilder:
    """Builder for creating scope hierarchies."""

    def __init__(self, name: str):
        """Initialize scope builder.

        Args:
            name: Hierarchy name
        """
        self.hierarchy = ScopeHierarchy(name=name)
        self._current_path = ""

    def add_global(self, name: str = "global", description: str | None = None) -> ScopeBuilder:
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

    def add_group(self, name: str, parent_path: str | None = None, description: str | None = None) -> ScopeBuilder:
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

    def add_org(self, name: str, parent_path: str | None = None, description: str | None = None) -> ScopeBuilder:
        """Add organization scope.

        Args:
            name: Organization name
            parent_path: Parent path
            description: Description

        Returns:
            Self for chaining
        """
        return self._add_scope(ScopeType.ORG, name, parent_path, description)

    def add_program(self, name: str, parent_path: str | None = None, description: str | None = None) -> ScopeBuilder:
        """Add program scope.

        Args:
            name: Program name
            parent_path: Parent path
            description: Description

        Returns:
            Self for chaining
        """
        return self._add_scope(ScopeType.PROGRAM, name, parent_path, description)

    def add_portfolio(self, name: str, parent_path: str | None = None, description: str | None = None) -> ScopeBuilder:
        """Add portfolio scope.

        Args:
            name: Portfolio name
            parent_path: Parent path
            description: Description

        Returns:
            Self for chaining
        """
        return self._add_scope(ScopeType.PORTFOLIO, name, parent_path, description)

    def add_project(self, name: str, parent_path: str | None = None, description: str | None = None) -> ScopeBuilder:
        """Add project scope.

        Args:
            name: Project name
            parent_path: Parent path
            description: Description

        Returns:
            Self for chaining
        """
        return self._add_scope(ScopeType.PROJECT, name, parent_path, description)

    def _add_scope(self, scope_type: ScopeType, name: str, parent_path: str | None = None, description: str | None = None) -> ScopeBuilder:
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


__all__ = [
    "ScopeBuilder",
    "ScopeHierarchy",
    "ScopeNode",
    "ScopeRelationship",
    "ScopeType",
]
