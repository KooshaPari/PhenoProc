"""
Project management for credential scoping.
"""

import json
from pathlib import Path

from .models import ProjectInfo


class ProjectManager:
    """Manages project information for credential scoping."""

    def __init__(self, data_dir: Path | None = None):
        """Initialize project manager.

        Args:
            data_dir: Directory for project data files
        """
        self.data_dir = data_dir or Path.home() / ".pheno" / "projects"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.projects_file = self.data_dir / "projects.json"
        self._projects: dict[str, ProjectInfo] = {}
        self._load_projects()

    def _load_projects(self):
        """Load projects from disk."""
        try:
            if self.projects_file.exists():
                with open(self.projects_file) as f:
                    projects_data = json.load(f)

                for project_id, project_data in projects_data.items():
                    self._projects[project_id] = ProjectInfo.from_dict(project_data)

        except Exception:
            # If loading fails, start with empty projects
            self._projects = {}

    def _save_projects(self):
        """Save projects to disk."""
        try:
            projects_data = {
                project_id: project.to_dict()
                for project_id, project in self._projects.items()
            }

            with open(self.projects_file, "w") as f:
                json.dump(projects_data, f, indent=2)

        except Exception:
            # If saving fails, continue without error
            pass

    def create_project(self, project_id: str, name: str, description: str | None = None, path: str | None = None) -> ProjectInfo:
        """Create a new project.

        Args:
            project_id: Unique project identifier
            name: Project name
            description: Optional project description
            path: Optional project path

        Returns:
            Created project info

        Raises:
            ValueError: If project ID already exists
        """
        if project_id in self._projects:
            raise ValueError(f"Project with ID '{project_id}' already exists")

        project = ProjectInfo(
            id=project_id,
            name=name,
            description=description,
            path=path,
        )

        self._projects[project_id] = project
        self._save_projects()

        return project

    def get_project(self, project_id: str) -> ProjectInfo | None:
        """Get project by ID.

        Args:
            project_id: Project identifier

        Returns:
            Project info if found, None otherwise
        """
        return self._projects.get(project_id)

    def update_project(self, project_id: str, **updates) -> ProjectInfo | None:
        """Update project information.

        Args:
            project_id: Project identifier
            **updates: Fields to update

        Returns:
            Updated project info if found, None otherwise
        """
        if project_id not in self._projects:
            return None

        project = self._projects[project_id]

        # Update fields
        for field, value in updates.items():
            if hasattr(project, field):
                setattr(project, field, value)

        # Update last accessed timestamp
        project.last_accessed = datetime.utcnow()

        self._save_projects()
        return project

    def delete_project(self, project_id: str) -> bool:
        """Delete a project.

        Args:
            project_id: Project identifier

        Returns:
            True if deleted, False if not found
        """
        if project_id not in self._projects:
            return False

        del self._projects[project_id]
        self._save_projects()
        return True

    def list_projects(self) -> list[ProjectInfo]:
        """List all projects.

        Returns:
            List of all projects
        """
        return list(self._projects.values())

    def find_project_by_path(self, path: str) -> ProjectInfo | None:
        """Find project by path.

        Args:
            path: Project path

        Returns:
            Project info if found, None otherwise
        """
        path_obj = Path(path).resolve()

        for project in self._projects.values():
            if project.path:
                project_path = Path(project.path).resolve()
                if path_obj == project_path or path_obj.is_relative_to(project_path):
                    return project

        return None

    def find_project_by_name(self, name: str) -> ProjectInfo | None:
        """Find project by name.

        Args:
            name: Project name

        Returns:
            Project info if found, None otherwise
        """
        for project in self._projects.values():
            if project.name.lower() == name.lower():
                return project

        return None

    def detect_project_from_cwd(self) -> ProjectInfo | None:
        """Detect project from current working directory.

        Returns:
            Project info if detected, None otherwise
        """
        cwd = Path.cwd()

        # Look for project markers
        project_markers = [
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "package.json",
            "Cargo.toml",
            ".git",
        ]

        # Walk up directory tree looking for project markers
        current_path = cwd
        while current_path != current_path.parent:
            for marker in project_markers:
                if (current_path / marker).exists():
                    # Try to find existing project
                    project = self.find_project_by_path(str(current_path))
                    if project:
                        return project

                    # Create new project if not found
                    project_id = current_path.name.lower().replace(" ", "-")
                    project_name = current_path.name

                    return self.create_project(
                        project_id=project_id,
                        name=project_name,
                        path=str(current_path),
                        description=f"Auto-detected project from {marker}",
                    )

            current_path = current_path.parent

        return None

    def get_project_credentials(self, project_id: str) -> list[str]:
        """Get list of credential keys for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of credential keys
        """
        project = self.get_project(project_id)
        if not project:
            return []

        # This would typically query the credential store
        # For now, return empty list
        return []

    def get_global_credentials(self) -> list[str]:
        """Get list of global credential keys.

        Returns:
            List of global credential keys
        """
        # This would typically query the credential store
        # For now, return empty list
        return []

    def get_shared_credentials(self, project_id: str) -> list[str]:
        """Get list of credentials shared with a project.

        Args:
            project_id: Project identifier

        Returns:
            List of shared credential keys
        """
        # This would typically query the credential store
        # For now, return empty list
        return []

    def get_project_stats(self, project_id: str) -> dict[str, int]:
        """Get project statistics.

        Args:
            project_id: Project identifier

        Returns:
            Dictionary of project statistics
        """
        project = self.get_project(project_id)
        if not project:
            return {}

        return {
            "total_credentials": len(self.get_project_credentials(project_id)),
            "global_credentials": len(self.get_global_credentials()),
            "shared_credentials": len(self.get_shared_credentials(project_id)),
        }

    def cleanup_unused_projects(self, days_threshold: int = 90) -> list[str]:
        """Clean up unused projects.

        Args:
            days_threshold: Days since last access to consider unused

        Returns:
            List of cleaned up project IDs
        """
        from datetime import datetime, timedelta

        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
        cleaned_up = []

        for project_id, project in list(self._projects.items()):
            if project.last_accessed and project.last_accessed < threshold_date:
                del self._projects[project_id]
                cleaned_up.append(project_id)

        if cleaned_up:
            self._save_projects()

        return cleaned_up


__all__ = ["ProjectManager"]
