"""
Hierarchical scoping system for credential management.

Provides deeply composable and recursive scoping:
- Global (system-wide)
- Group/Org/Program/Portfolio (third layer - deeply composable)
- Project (specific projects)
- Environment (dev/staging/prod)

The third layer is deeply composable and recursive:
global > group > subgroup > sub-subgroup > ... > project
"""

from .builder import ScopeBuilder
from .manager import HierarchyManager
from .models import ScopeHierarchy, ScopeNode, ScopeRelationship, ScopeType
from .resolver import CredentialResolver

__all__ = [
    "CredentialResolver",
    "HierarchyManager",
    "ScopeBuilder",
    "ScopeHierarchy",
    "ScopeNode",
    "ScopeRelationship",
    "ScopeType",
]
