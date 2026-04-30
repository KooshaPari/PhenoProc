"""
Audit logging for credential access and changes.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from .models import CredentialAccess


class AuditLogger:
    """Audit logger for credential operations."""

    def __init__(self, data_dir: Path | None = None):
        """Initialize audit logger.

        Args:
            data_dir: Directory for audit log files
        """
        self.data_dir = data_dir or Path.home() / ".pheno" / "audit"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.data_dir / "credential_access.jsonl"
        self._access_log: list[CredentialAccess] = []
        self._load_recent_logs()

    def _load_recent_logs(self, max_entries: int = 1000):
        """Load recent audit logs from disk.

        Args:
            max_entries: Maximum number of entries to load
        """
        try:
            if not self.log_file.exists():
                return

            with open(self.log_file) as f:
                lines = f.readlines()

            # Load last max_entries lines
            recent_lines = lines[-max_entries:] if len(lines) > max_entries else lines

            for line in recent_lines:
                try:
                    data = json.loads(line.strip())
                    access = CredentialAccess.from_dict(data)
                    self._access_log.append(access)
                except Exception:
                    # Skip malformed log entries
                    continue

        except Exception:
            # If loading fails, start with empty log
            self._access_log = []

    def _append_to_file(self, access: CredentialAccess):
        """Append access log entry to file.

        Args:
            access: Access log entry
        """
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(access.to_dict()) + "\n")

        except Exception:
            # If file writing fails, continue without error
            pass

    def log_access(self, credential_id: str, action: str, success: bool = True,
                   error_message: str | None = None, user: str | None = None,
                   project_id: str | None = None) -> CredentialAccess:
        """Log credential access.

        Args:
            credential_id: ID of accessed credential
            action: Action performed (read, write, delete)
            success: Whether action was successful
            error_message: Error message if failed
            user: User who performed action
            project_id: Project context

        Returns:
            Created access log entry
        """
        # Get additional context
        ip_address = self._get_ip_address()
        user_agent = self._get_user_agent()

        access = CredentialAccess(
            credential_id=credential_id,
            action=action,
            success=success,
            error_message=error_message,
            user=user or self._get_current_user(),
            project_id=project_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Add to memory log
        self._access_log.append(access)

        # Append to file
        self._append_to_file(access)

        # Keep memory log size manageable
        if len(self._access_log) > 1000:
            self._access_log = self._access_log[-500:]

        return access

    def _get_ip_address(self) -> str | None:
        """Get current IP address.

        Returns:
            IP address if available
        """
        try:
            import socket
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return None

    def _get_user_agent(self) -> str | None:
        """Get current user agent.

        Returns:
            User agent if available
        """
        try:
            import sys
            return f"pheno-credentials/{sys.version_info.major}.{sys.version_info.minor}"
        except Exception:
            return None

    def _get_current_user(self) -> str | None:
        """Get current user.

        Returns:
            Username if available
        """
        try:
            import getpass
            return getpass.getuser()
        except Exception:
            return os.getenv("USER", os.getenv("USERNAME"))

    def get_access_log(self, credential_id: str | None = None,
                      action: str | None = None,
                      user: str | None = None,
                      project_id: str | None = None,
                      limit: int = 100) -> list[CredentialAccess]:
        """Get access log entries.

        Args:
            credential_id: Filter by credential ID
            action: Filter by action
            user: Filter by user
            project_id: Filter by project ID
            limit: Maximum number of entries to return

        Returns:
            List of access log entries
        """
        filtered_logs = []

        for access in self._access_log:
            if credential_id and access.credential_id != credential_id:
                continue
            if action and access.action != action:
                continue
            if user and access.user != user:
                continue
            if project_id and access.project_id != project_id:
                continue

            filtered_logs.append(access)

            if len(filtered_logs) >= limit:
                break

        return filtered_logs

    def get_credential_access_summary(self, credential_id: str) -> dict[str, int]:
        """Get access summary for a credential.

        Args:
            credential_id: Credential ID

        Returns:
            Dictionary of access statistics
        """
        accesses = self.get_access_log(credential_id=credential_id)

        return {
            "total_accesses": len(accesses),
            "successful_accesses": sum(1 for a in accesses if a.success),
            "failed_accesses": sum(1 for a in accesses if not a.success),
            "read_accesses": sum(1 for a in accesses if a.action == "read"),
            "write_accesses": sum(1 for a in accesses if a.action == "write"),
            "delete_accesses": sum(1 for a in accesses if a.action == "delete"),
        }


    def get_user_activity(self, user: str, days: int = 30) -> dict[str, int]:
        """Get user activity summary.

        Args:
            user: Username
            days: Number of days to look back

        Returns:
            Dictionary of user activity statistics
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        user_accesses = [
            access for access in self._access_log
            if access.user == user and access.timestamp >= cutoff_date
        ]

        return {
            "total_actions": len(user_accesses),
            "successful_actions": sum(1 for a in user_accesses if a.success),
            "failed_actions": sum(1 for a in user_accesses if not a.success),
            "unique_credentials": len({a.credential_id for a in user_accesses}),
            "unique_projects": len({a.project_id for a in user_accesses if a.project_id}),
        }

    def get_security_alerts(self) -> list[dict[str, str]]:
        """Get security alerts from access logs.

        Returns:
            List of security alerts
        """
        alerts = []

        # Check for failed access attempts
        failed_accesses = [a for a in self._access_log if not a.success]
        if len(failed_accesses) > 10:
            alerts.append({
                "type": "high_failure_rate",
                "message": f"High number of failed access attempts: {len(failed_accesses)}",
                "severity": "high",
            })

        # Check for unusual access patterns
        recent_accesses = [
            a for a in self._access_log
            if a.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ]

        if len(recent_accesses) > 100:
            alerts.append({
                "type": "high_activity",
                "message": f"Unusually high activity in last hour: {len(recent_accesses)} accesses",
                "severity": "medium",
            })

        return alerts

    def export_logs(self, file_path: Path, format: str = "json"):
        """Export audit logs to file.

        Args:
            file_path: Path to export file
            format: Export format (json, csv)
        """
        if format == "json":
            with open(file_path, "w") as f:
                json.dump([access.to_dict() for access in self._access_log], f, indent=2)

        elif format == "csv":
            import csv

            with open(file_path, "w", newline="") as f:
                if self._access_log:
                    writer = csv.DictWriter(f, fieldnames=self._access_log[0].to_dict().keys())
                    writer.writeheader()
                    for access in self._access_log:
                        writer.writerow(access.to_dict())

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def cleanup_old_logs(self, days: int = 90):
        """Clean up old audit logs.

        Args:
            days: Number of days to keep
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Filter recent logs
        recent_logs = [
            access for access in self._access_log
            if access.timestamp >= cutoff_date
        ]

        # Update memory log
        self._access_log = recent_logs

        # Rewrite log file
        try:
            with open(self.log_file, "w") as f:
                for access in recent_logs:
                    f.write(json.dumps(access.to_dict()) + "\n")

        except Exception:
            # If file writing fails, continue without error
            pass


__all__ = ["AuditLogger"]
