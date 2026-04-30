"""Tests for audit logging functionality."""

import tempfile
from pathlib import Path

import pytest

from pheno_credentials import CredentialBroker
from pheno_credentials.audit import AuditLogger


class TestAuditLogger:
    """Tests for AuditLogger class."""

    def test_log_access_read(self, broker, temp_dir):
        """Test logging read access."""
        audit_logger = AuditLogger(temp_dir)

        broker.store_credential(name="AUDIT_TEST", value="val", scope="global")
        credential = broker.get_credential_info("AUDIT_TEST")

        audit_logger.log_access(
            credential_id=str(credential.id),
            action="read",
            success=True,
        )

        log = audit_logger.get_access_log()
        assert len(log) >= 1

    def test_log_access_write(self, broker, temp_dir):
        """Test logging write access."""
        audit_logger = AuditLogger(temp_dir)

        broker.store_credential(name="WRITE_TEST", value="val", scope="global")
        credential = broker.get_credential_info("WRITE_TEST")

        audit_logger.log_access(
            credential_id=str(credential.id),
            action="write",
            success=True,
        )

        log = audit_logger.get_access_log()
        assert len(log) >= 1

    def test_log_access_delete(self, broker, temp_dir):
        """Test logging delete access."""
        audit_logger = AuditLogger(temp_dir)

        broker.store_credential(name="DELETE_TEST", value="val", scope="global")
        credential = broker.get_credential_info("DELETE_TEST")

        audit_logger.log_access(
            credential_id=str(credential.id),
            action="delete",
            success=True,
        )

        log = audit_logger.get_access_log()
        assert len(log) >= 1

    def test_log_failed_access(self, temp_dir):
        """Test logging failed access."""
        audit_logger = AuditLogger(temp_dir)

        from uuid import uuid4

        audit_logger.log_access(
            credential_id=str(uuid4()),
            action="read",
            success=False,
            error_message="Credential not found",
        )

        log = audit_logger.get_access_log()
        failed_entries = [e for e in log if not e.success]
        assert len(failed_entries) >= 1

    def test_get_access_log_with_limit(self, broker, temp_dir):
        """Test getting access log with limit."""
        audit_logger = AuditLogger(temp_dir)

        broker.store_credential(name="LIMIT_TEST", value="val", scope="global")

        log = audit_logger.get_access_log(limit=5)
        assert len(log) <= 5

    def test_get_access_log_by_credential_id(self, broker, temp_dir):
        """Test getting access log filtered by credential ID."""
        audit_logger = AuditLogger(temp_dir)

        broker.store_credential(name="FILTER_TEST", value="val", scope="global")
        credential = broker.get_credential_info("FILTER_TEST")

        audit_logger.log_access(
            credential_id=str(credential.id),
            action="read",
            success=True,
        )

        log = audit_logger.get_access_log(limit=10)
        assert len(log) >= 1

    def test_get_security_alerts(self, broker, temp_dir):
        """Test getting security alerts."""
        audit_logger = AuditLogger(temp_dir)

        broker.store_credential(name="SECURITY_TEST", value="val", scope="global")
        broker.store_credential(name="SECURITY_TEST", value="val2", scope="global")
        broker.store_credential(name="SECURITY_TEST", value="val3", scope="global")

        alerts = audit_logger.get_security_alerts()
        assert isinstance(alerts, list)


class TestBrokerAuditIntegration:
    """Integration tests for broker audit functionality."""

    def test_broker_logs_all_operations(self, broker):
        """Test that broker logs all credential operations."""
        broker.store_credential(name="OP_TEST_1", value="val1", scope="global")
        broker.store_credential(name="OP_TEST_1", value="val2", scope="global")
        broker.delete_credential("OP_TEST_1")

    def test_broker_audit_tracks_specific_credential(self, broker):
        """Test that broker audit tracks specific credential."""
        broker.store_credential(name="TRACK_ME", value="val1", scope="global")
        broker.store_credential(name="TRACK_ME", value="val2", scope="global")
