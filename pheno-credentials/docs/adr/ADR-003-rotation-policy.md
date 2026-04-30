# ADR-003: Credential Rotation Policy

**Document ID:** PHENOTYPE_CREDENTIALS_ADR_003  
**Status:** Proposed  
**Last Updated:** 2026-04-03  
**Author:** Phenotype Architecture Team  
**Supersedes:** N/A  
**Related:** ADR-001 (Storage Backend), ADR-002 (Encryption Model)

---

## Table of Contents

1. [Title](#adr-003-credential-rotation-policy)
2. [Context](#context)
3. [Decision](#decision)
4. [Consequences](#consequences)
5. [Architecture](#architecture)
6. [Implementation Details](#implementation-details)
7. [Code Examples](#code-examples)
8. [Cross-References](#cross-references)

---

## Context

### Problem Statement

The pheno-credentials system currently supports credential storage and retrieval but lacks automated credential rotation capabilities. Without rotation, credentials remain valid indefinitely, increasing the blast radius of credential compromise. Industry standards (SOC 2, ISO 27001, NIST SP 800-53) require periodic credential rotation as a fundamental security control.

The system already has partial rotation infrastructure:
- `Credential.expires_at` field for expiration tracking
- `Credential.auto_refresh` flag for OAuth tokens
- `cleanup_expired_credentials()` method in `CredentialBroker`
- `TokenRefreshScheduler` for OAuth token refresh
- `AutomationEngine` for event-driven automation

However, these are not integrated into a cohesive rotation policy framework.

### Requirements

1. **Configurable Rotation Policies:** Different credential types require different rotation frequencies
2. **Automated Rotation:** System should automatically rotate credentials approaching expiration
3. **Zero-Downtime Rotation:** Rotation must not disrupt active services using the credential
4. **Audit Trail:** All rotation events must be logged with before/after state
5. **Rollback Capability:** Failed rotations must be reversible
6. **Notification:** Stakeholders must be notified before and after rotation
7. **Compliance Reporting:** Rotation status must be reportable for compliance audits

### Constraints

- Must work within the existing storage backend architecture (ADR-001)
- Must use the existing encryption model (ADR-002)
- Must integrate with the existing audit logging system
- Must support both interactive (CLI/TUI) and automated (scheduler) rotation
- OAuth token refresh is already implemented and must be leveraged

### Options Considered

#### Option 1: Scheduled Rotation Only

Rotate credentials on fixed schedules (cron-based).

**Pros:**
- Simple to implement and understand
- Predictable rotation timeline
- Easy to audit and report

**Cons:**
- No response to security incidents
- Wasteful rotation of unused credentials
- Cannot handle emergency rotation needs
- Fixed schedules may not align with business needs

#### Option 2: Event-Driven Rotation Only

Rotate credentials only in response to specific events (security incident, team member departure, etc.).

**Pros:**
- Responsive to actual security needs
- No unnecessary rotation of stable credentials
- Aligns with zero-trust principles

**Cons:**
- Requires reliable event detection
- No compliance coverage for periodic rotation
- Complex event sourcing infrastructure needed
- May miss rotation windows if events are not detected

#### Option 3: Policy-Based Rotation (Selected)

Define rotation policies per credential type with configurable schedules, triggers, and approval workflows. Combines scheduled and event-driven approaches.

**Pros:**
- Flexible and configurable per credential type
- Supports both scheduled and event-driven rotation
- Compliance-friendly (documented policies)
- Supports approval workflows for sensitive credentials
- Can integrate with existing automation engine

**Cons:**
- More complex configuration
- Requires policy management interface
- Multiple rotation paths increase testing surface

#### Option 4: Dynamic/Adaptive Rotation

Use machine learning to determine optimal rotation timing based on usage patterns, threat intelligence, and risk scoring.

**Pros:**
- Optimal rotation timing
- Risk-based prioritization
- Minimal disruption to services

**Cons:**
- Overly complex for current needs
- Requires significant data collection
- Unpredictable rotation timing
- Difficult to audit and explain

---

## Decision

**We will implement a Policy-Based Rotation system** that combines scheduled rotation with event-driven triggers, configurable per credential type and scope.

### Rotation Policy Framework

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Rotation Policy Framework                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                   RotationPolicy                              │ │
│  │                                                               │ │
│  │  name: str                      # Policy identifier           │ │
│  │  credential_types: list         # Which types this applies to │ │
│  │  max_age: timedelta             # Maximum credential lifetime │ │
│  │  warn_threshold: timedelta      # When to start warning       │ │
│  │  rotation_method: str           # automatic|manual|semi-auto  │ │
│  │  approval_required: bool        # Needs human approval?       │ │
│  │  rollback_window: timedelta     # How long to keep old cred   │ │
│  │  notification_channels: list    # Where to send alerts        │ │
│  │  grace_period: timedelta        # Time between warn & rotate  │ │
│  │  max_retries: int               # Retry count on failure      │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Default Policies:                                                  │
│  ─────────────────                                                  │
│  ┌──────────────────┬──────────┬──────────┬───────────┬──────────┐ │
│  │ Policy           │ Max Age  │ Warn     │ Method    │ Approval │ │
│  ├──────────────────┼──────────┼──────────┼───────────┼──────────┤ │
│  │ api_key          │ 90 days  │ 30 days  │ semi-auto │ No       │ │
│  │ oauth_token      │ Per exp  │ 5 min    │ automatic │ No       │ │
│  │ password         │ 90 days  │ 14 days  │ manual    │ Yes      │ │
│  │ database_url     │ 30 days  │ 7 days   │ semi-auto │ Yes      │ │
│  │ ssh_key          │ 180 days │ 30 days  │ automatic │ No       │ │
│  │ certificate      │ Per exp  │ 7 days   │ automatic │ No       │ │
│  │ secret           │ 90 days  │ 14 days  │ semi-auto │ No       │ │
│  │ connection_str   │ 30 days  │ 7 days   │ semi-auto │ Yes      │ │
│  └──────────────────┴──────────┴──────────┴───────────┴──────────┘ │
│                                                                     │
│  Event Triggers:                                                    │
│  ──────────────                                                     │
│  • security_incident    → Immediate rotation of affected creds     │
│  • team_member_departure → Rotation of creds accessible by member  │
│  • credential_exposure  → Immediate rotation of exposed cred       │
│  • compliance_audit     → Verify all creds within rotation policy  │
│  • suspicious_access    → Rotate cred + investigate                │
│  • policy_violation     → Rotate cred + alert admin                │
└─────────────────────────────────────────────────────────────────────┘
```

### Rotation Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Credential Rotation Lifecycle                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │ Created │───▶│ Active   │───▶│ Warning  │───▶│ Rotating │      │
│  │ (t=0)   │    │          │    │          │    │          │      │
│  └─────────┘    └──────────┘    └──────────┘    └────┬─────┘      │
│       │               │               │               │            │
│       │               │               │         ┌─────┴─────┐     │
│       │               │               │         │           │     │
│       │               │               │         ▼           ▼     │
│       │               │               │    ┌────────┐ ┌────────┐ │
│       │               │               │    │Success │ │Failure │ │
│       │               │               │    └───┬────┘ └───┬────┘ │
│       │               │               │        │          │       │
│       │               │               │        ▼          ▼       │
│       │               │               │   ┌────────┐ ┌────────┐  │
│       │               │               │   │Active  │ │Rollback│  │
│       │               │               │   │(new    │ │(retry  │  │
│       │               │               │   │ cred)  │ │ or     │  │
│       │               │               │   └────────┘ │alert)  │  │
│       │               │               │              └────────┘  │
│       │               │               │                          │
│       ▼               ▼               ▼                          │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Timeline                                 │ │
│  │                                                             │ │
│  │  Day 0          Day 60         Day 75         Day 90       │ │
│  │  │              │              │              │             │ │
│  │  ▼              ▼              ▼              ▼             │ │
│  │  ┌────┐    ┌──────────┐  ┌──────────┐  ┌──────────┐       │ │
│  │  │New │    │          │  │Warning   │  │Rotation  │       │ │
│  │  │Cred│    │ Monitor  │  │(15d left)│  │Initiated │       │ │
│  │  │    │    │          │  │          │  │          │       │ │
│  │  └────┘    └──────────┘  └──────────┘  └──────────┘       │ │
│  │                                                             │ │
│  │  Status:      Normal         Alert         Action           │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Consequences

### Positive Consequences

1. **Compliance Coverage:** Documented rotation policies with configurable parameters satisfy SOC 2, ISO 27001, and NIST SP 800-53 requirements for credential lifecycle management.

2. **Risk Reduction:** Automatic rotation of credentials approaching expiration reduces the window of exposure if a credential is compromised without detection.

3. **Type-Specific Policies:** Different credential types have appropriate rotation frequencies — OAuth tokens refresh automatically (per expiry), while API keys rotate on a 90-day schedule, and passwords require manual rotation with approval.

4. **Grace Period:** The warning threshold (e.g., 30 days before expiry for API keys) provides time for human intervention in semi-automatic and manual rotation modes.

5. **Rollback Window:** Keeping the old credential accessible during the rollback window (e.g., 24 hours) enables quick recovery if the new credential causes service disruption.

6. **Event-Driven Emergency Rotation:** Security incidents trigger immediate rotation of affected credentials, independent of the scheduled rotation timeline.

7. **Integration with Existing Systems:** Leverages the existing `TokenRefreshScheduler` for OAuth tokens, `AutomationEngine` for event-driven rotation, and `AuditLogger` for rotation event logging.

8. **Notification System:** Configurable notification channels ensure stakeholders are informed before and after rotation events.

### Negative Consequences

1. **Implementation Complexity:** The policy-based approach requires a policy engine, scheduler integration, event handling, approval workflows, and notification system — significantly more complex than simple scheduled rotation.

2. **Configuration Overhead:** Each credential type requires policy configuration, and organizations may need custom policies for specific credentials, increasing administrative burden.

3. **Service Disruption Risk:** Automatic rotation of credentials in use by active services can cause outages if the rotation is not coordinated with service restarts or configuration reloads.

4. **Rollback Complexity:** Implementing reliable rollback requires maintaining the old credential alongside the new one, managing the transition period, and detecting rotation failures accurately.

5. **Approval Workflow Friction:** Manual rotation with approval requirements introduces delays and operational overhead, particularly for high-frequency rotation (e.g., database URLs every 30 days).

6. **Policy Enforcement Gap:** The current system has no mechanism to enforce rotation policies — credentials can exist without expiration dates, bypassing rotation entirely.

7. **Testing Complexity:** Multiple rotation paths (scheduled, event-driven, manual, emergency) with different credential types and approval workflows create a large testing surface.

### Mitigation Strategies

| Consequence | Mitigation |
|------------|------------|
| Implementation complexity | Phase implementation: scheduled → event-driven → approval workflows |
| Configuration overhead | Provide sensible defaults; allow policy inheritance from type defaults |
| Service disruption | Implement dual-key rotation pattern (old + new active during grace period) |
| Rollback complexity | Store old credential with expiration; automatic cleanup after rollback window |
| Approval friction | Auto-approve for low-risk credentials; escalate only for sensitive types |
| Policy enforcement | Add validation that rejects credentials without expiry in production mode |
| Testing complexity | Create rotation test harness with mock credential stores and time control |

---

## Architecture

### Rotation Engine Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Rotation Engine Architecture                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                   RotationEngine                              │ │
│  │                                                               │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │ │
│  │  │ PolicyManager   │  │ RotationScheduler│ │ EventRouter   │ │ │
│  │  │                 │  │                 │  │               │ │ │
│  │  │ • Load policies │  │ • Cron-based    │  │ • Subscribe   │ │ │
│  │  │ • Validate      │  │   checks        │  │   to events   │ │ │
│  │  │ • Apply defaults│  │ • Pre-expiry    │  │ • Match to    │ │ │
│  │  │ • Inheritance   │  │   scheduling    │  │   policies    │ │ │
│  │  │ • Override mgmt │  │ • Retry logic   │  │ • Trigger     │ │ │
│  │  └────────┬────────┘  └────────┬────────┘  │   rotation    │ │ │
│  │           │                    │            └───────┬───────┘ │ │
│  │           ▼                    ▼                    │         │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │                   RotationExecutor                       │ │ │
│  │  │                                                          │ │ │
│  │  │  1. Generate new credential                              │ │ │
│  │  │  2. Store new credential (dual-key mode)                 │ │ │
│  │  │  3. Notify stakeholders                                  │ │ │
│  │  │  4. Wait for grace period                                │ │ │
│  │  │  5. Deactivate old credential                            │ │ │
│  │  │  6. Log rotation event                                   │ │ │
│  │  │  7. Schedule cleanup of old credential                   │ │ │
│  │  │                                                          │ │ │
│  │  │  On Failure:                                             │ │ │
│  │  │  1. Attempt retry (up to max_retries)                    │ │ │
│  │  │  2. If retries exhausted, alert admin                    │ │ │
│  │  │  3. Keep old credential active                           │ │ │
│  │  │  4. Log failure event                                    │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Integration Points:                                                │
│  ───────────────────                                                │
│  • CredentialBroker.store_credential() — Store new credentials     │
│  • CredentialBroker.delete_credential() — Remove old credentials   │
│  • AuditLogger.log_access() — Log rotation events                  │
│  • TokenRefreshScheduler — OAuth token refresh                     │
│  • AutomationEngine — Event-driven rotation triggers               │
│  • NotificationService — Alert stakeholders (future)               │
└─────────────────────────────────────────────────────────────────────┘
```

### Dual-Key Rotation Pattern

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Dual-Key Rotation Pattern                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Phase 1: Preparation (T - grace_period)                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Old Credential: ACTIVE                                     │   │
│  │  New Credential: GENERATED (not yet active)                 │   │
│  │  Action: Generate new credential, store in pending state    │   │
│  │  Notification: Alert stakeholders of upcoming rotation      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Phase 2: Activation (T)                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Old Credential: ACTIVE (draining)                          │   │
│  │  New Credential: ACTIVE                                     │   │
│  │  Action: Activate new credential, mark old as draining      │   │
│  │  Notification: Confirm rotation initiated                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Phase 3: Drain (T + drain_period)                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Old Credential: DRAINING (accepting existing connections)  │   │
│  │  New Credential: ACTIVE (accepting new connections)         │   │
│  │  Action: Monitor for errors, verify new credential works    │   │
│  │  Notification: Send rotation completion notice              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Phase 4: Cleanup (T + rollback_window)                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Old Credential: REMOVED                                    │   │
│  │  New Credential: ACTIVE                                     │   │
│  │  Action: Delete old credential, update audit log            │   │
│  │  Notification: Confirm rotation complete                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Default Timings:                                                   │
│  ───────────────                                                    │
│  grace_period:    24 hours (warning before rotation)               │
│  drain_period:    1 hour (both credentials active)                 │
│  rollback_window: 72 hours (old credential available for rollback) │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### Rotation Policy Model

```python
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class RotationMethod(StrEnum):
    AUTOMATIC = "automatic"
    SEMI_AUTOMATIC = "semi-automatic"
    MANUAL = "manual"


class RotationPolicy(BaseModel):
    """Rotation policy for credential types."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Policy identifier")
    credential_types: list[str] = Field(..., description="Applicable credential types")

    # Timing
    max_age: timedelta = Field(..., description="Maximum credential lifetime")
    warn_threshold: timedelta = Field(..., description="When to start warning")
    grace_period: timedelta = Field(timedelta(hours=24), description="Warning to rotation time")
    rollback_window: timedelta = Field(timedelta(hours=72), description="Old credential retention")
    drain_period: timedelta = Field(timedelta(hours=1), description="Dual-key active period")

    # Method
    rotation_method: RotationMethod = Field(RotationMethod.SEMI_AUTOMATIC)
    approval_required: bool = Field(False, description="Requires human approval")
    max_retries: int = Field(3, description="Maximum retry attempts")

    # Notification
    notification_channels: list[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    enabled: bool = Field(True)
```

### Default Policies

```python
DEFAULT_ROTATION_POLICIES = {
    "api_key": RotationPolicy(
        name="api_key",
        credential_types=["api_key"],
        max_age=timedelta(days=90),
        warn_threshold=timedelta(days=30),
        rotation_method=RotationMethod.SEMI_AUTOMATIC,
        approval_required=False,
    ),
    "oauth_token": RotationPolicy(
        name="oauth_token",
        credential_types=["oauth_token"],
        max_age=timedelta(hours=1),  # Per-token expiry
        warn_threshold=timedelta(minutes=5),
        rotation_method=RotationMethod.AUTOMATIC,
        approval_required=False,
    ),
    "password": RotationPolicy(
        name="password",
        credential_types=["password"],
        max_age=timedelta(days=90),
        warn_threshold=timedelta(days=14),
        rotation_method=RotationMethod.MANUAL,
        approval_required=True,
    ),
    "database_url": RotationPolicy(
        name="database_url",
        credential_types=["database_url", "connection_string"],
        max_age=timedelta(days=30),
        warn_threshold=timedelta(days=7),
        rotation_method=RotationMethod.SEMI_AUTOMATIC,
        approval_required=True,
    ),
    "ssh_key": RotationPolicy(
        name="ssh_key",
        credential_types=["ssh_key"],
        max_age=timedelta(days=180),
        warn_threshold=timedelta(days=30),
        rotation_method=RotationMethod.AUTOMATIC,
        approval_required=False,
    ),
    "certificate": RotationPolicy(
        name="certificate",
        credential_types=["certificate"],
        max_age=timedelta(days=365),  # Per-certificate expiry
        warn_threshold=timedelta(days=7),
        rotation_method=RotationMethod.AUTOMATIC,
        approval_required=False,
    ),
    "secret": RotationPolicy(
        name="secret",
        credential_types=["secret"],
        max_age=timedelta(days=90),
        warn_threshold=timedelta(days=14),
        rotation_method=RotationMethod.SEMI_AUTOMATIC,
        approval_required=False,
    ),
}
```

### Rotation Status Tracking

```python
class RotationStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DRAINING = "draining"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RotationRecord(BaseModel):
    """Record of a credential rotation event."""

    id: UUID = Field(default_factory=uuid4)
    credential_id: UUID = Field(..., description="Original credential ID")
    credential_name: str = Field(..., description="Credential name")
    policy_name: str = Field(..., description="Applied rotation policy")

    # Timing
    scheduled_at: datetime = Field(..., description="Scheduled rotation time")
    started_at: datetime | None = Field(None, description="Rotation start time")
    completed_at: datetime | None = Field(None, description="Rotation completion time")

    # Status
    status: RotationStatus = Field(RotationStatus.PENDING)
    error_message: str | None = Field(None, description="Error if failed")
    retry_count: int = Field(0, description="Number of retries")

    # Old/New credential tracking
    old_credential_id: UUID | None = Field(None, description="Old credential (for rollback)")
    new_credential_id: UUID | None = Field(None, description="New credential ID")
    old_credential_expires_at: datetime | None = Field(None, description="When old cred is removed")

    # Audit
    initiated_by: str | None = Field(None, description="Who/what initiated rotation")
    approved_by: str | None = Field(None, description="Who approved (if required)")
    audit_log_id: UUID | None = Field(None, description="Link to audit log entry")
```

---

## Code Examples

### Rotation Engine Implementation

```python
from datetime import datetime, timedelta
from typing import Protocol


class RotationEngine:
    """Engine for managing credential rotation."""

    def __init__(self, broker, policies: dict[str, RotationPolicy] | None = None):
        self.broker = broker
        self.policies = policies or dict(DEFAULT_ROTATION_POLICIES)
        self._rotation_records: dict[UUID, RotationRecord] = {}

    def check_rotation_due(self) -> list[RotationRecord]:
        """Check all credentials for rotation due."""
        due_rotations = []
        credentials = self.broker.list_credentials()

        for credential in credentials:
            policy = self._get_policy(credential)
            if not policy or not policy.enabled:
                continue

            # Check if rotation is due
            age = datetime.utcnow() - credential.created_at
            if age >= policy.max_age:
                record = self._create_rotation_record(credential, policy)
                due_rotations.append(record)
            elif self._is_approaching_expiry(credential, policy):
                # Warning phase
                self._send_warning(credential, policy)

        return due_rotations

    async def execute_rotation(self, record: RotationRecord) -> bool:
        """Execute a credential rotation."""
        policy = self.policies[record.policy_name]
        credential = self.broker.get_credential_info(record.credential_name)

        if not credential:
            record.status = RotationStatus.FAILED
            record.error_message = "Credential not found"
            return False

        # Check approval requirement
        if policy.approval_required and not record.approved_by:
            record.status = RotationStatus.PENDING
            self._request_approval(record)
            return False

        try:
            record.status = RotationStatus.IN_PROGRESS
            record.started_at = datetime.utcnow()

            # Phase 1: Generate new credential
            new_value = await self._generate_new_credential(credential)

            # Phase 2: Store new credential (dual-key mode)
            success = self.broker.store_credential(
                name=credential.name,
                value=new_value,
                credential_type=credential.type.value,
                scope=credential.scope.value,
                service=credential.service,
                description=f"Rotated from {credential.id}",
                expires_at=datetime.utcnow() + policy.max_age,
            )

            if not success:
                raise RotationError("Failed to store new credential")

            record.new_credential_id = self.broker.get_credential_info(credential.name).id
            record.old_credential_id = credential.id
            record.old_credential_expires_at = (
                datetime.utcnow() + policy.rollback_window
            )

            # Phase 3: Drain period (both credentials active)
            await self._wait_for_drain(policy.drain_period)

            # Phase 4: Verify new credential works
            verified = await self._verify_credential(credential.name, new_value)
            if not verified:
                raise RotationError("New credential verification failed")

            # Phase 5: Complete rotation
            record.status = RotationStatus.COMPLETED
            record.completed_at = datetime.utcnow()

            # Log rotation event
            self.broker.audit_logger.log_access(
                credential_id=str(record.id),
                action="rotate",
                success=True,
                user="rotation_engine",
            )

            # Schedule old credential cleanup
            self._schedule_cleanup(record)

            return True

        except Exception as e:
            record.status = RotationStatus.FAILED
            record.error_message = str(e)
            record.retry_count += 1

            if record.retry_count < policy.max_retries:
                # Retry on next check
                pass
            else:
                # Max retries exhausted — alert admin
                self._alert_admin(record)

            return False

    def _get_policy(self, credential) -> RotationPolicy | None:
        """Get rotation policy for a credential."""
        return self.policies.get(credential.type.value)

    def _is_approaching_expiry(self, credential, policy) -> bool:
        """Check if credential is approaching expiry."""
        if not credential.expires_at:
            age = datetime.utcnow() - credential.created_at
            remaining = policy.max_age - age
            return remaining <= policy.warn_threshold

        remaining = credential.expires_at - datetime.utcnow()
        return remaining <= policy.warn_threshold

    def _create_rotation_record(self, credential, policy) -> RotationRecord:
        """Create a rotation record for a credential."""
        record = RotationRecord(
            credential_id=credential.id,
            credential_name=credential.name,
            policy_name=policy.name,
            scheduled_at=datetime.utcnow(),
            initiated_by="rotation_scheduler",
        )
        self._rotation_records[record.id] = record
        return record

    async def _generate_new_credential(self, credential) -> str:
        """Generate a new credential value."""
        # This would be provider-specific in a real implementation
        # For now, generate a random token
        import secrets
        return secrets.token_urlsafe(32)

    async def _verify_credential(self, name: str, value: str) -> bool:
        """Verify that the new credential works."""
        # This would be provider-specific in a real implementation
        # For now, just check that the credential was stored
        stored = self.broker.get_credential_info(name)
        return stored is not None

    async def _wait_for_drain(self, drain_period: timedelta):
        """Wait for the drain period."""
        import asyncio
        await asyncio.sleep(drain_period.total_seconds())

    def _schedule_cleanup(self, record: RotationRecord):
        """Schedule cleanup of old credential."""
        # In a real implementation, this would use a scheduler
        # For now, just log the scheduled cleanup time
        pass

    def _send_warning(self, credential, policy):
        """Send warning notification for approaching expiry."""
        # In a real implementation, this would send notifications
        pass

    def _request_approval(self, record: RotationRecord):
        """Request approval for rotation."""
        # In a real implementation, this would trigger an approval workflow
        pass

    def _alert_admin(self, record: RotationRecord):
        """Alert admin of rotation failure."""
        # In a real implementation, this would send an alert
        pass


class RotationError(Exception):
    """Error during credential rotation."""
    pass
```

### CLI Commands for Rotation

```python
@app.command()
def rotation_check(
    credential: str | None = typer.Option(None, "--credential", "-c", help="Check specific credential"),
    policy: str | None = typer.Option(None, "--policy", "-p", help="Check specific policy"),
):
    """Check credentials for rotation due."""
    engine = RotationEngine(get_broker())
    due = engine.check_rotation_due()

    if not due:
        console.print("[green]No credentials due for rotation[/green]")
        return

    table = Table(title="Credentials Due for Rotation")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Policy", style="blue")
    table.add_column("Status", style="yellow")
    table.add_column("Scheduled", style="dim")

    for record in due:
        table.add_row(
            record.credential_name,
            record.policy_name,
            record.policy_name,
            record.status.value,
            record.scheduled_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


@app.command()
def rotation_execute(
    credential: str = typer.Argument(..., help="Credential to rotate"),
    force: bool = typer.Option(False, "--force", "-f", help="Force rotation without approval"),
):
    """Execute credential rotation."""
    engine = RotationEngine(get_broker())
    credentials = engine.broker.list_credentials()

    for cred in credentials:
        if cred.name == credential:
            policy = engine._get_policy(cred)
            record = engine._create_rotation_record(cred, policy)

            if force:
                record.approved_by = "cli_force"

            import asyncio
            success = asyncio.run(engine.execute_rotation(record))

            if success:
                console.print(f"[green]Credential '{credential}' rotated successfully[/green]")
            else:
                console.print(f"[red]Rotation failed: {record.error_message}[/red]")
                raise typer.Exit(1)
            return

    console.print(f"[red]Credential '{credential}' not found[/red]")
    raise typer.Exit(1)


@app.command()
def rotation_status(
    credential: str | None = typer.Option(None, "--credential", "-c", help="Filter by credential"),
):
    """Show rotation status."""
    engine = RotationEngine(get_broker())

    table = Table(title="Rotation Status")
    table.add_column("Credential", style="cyan")
    table.add_column("Policy", style="green")
    table.add_column("Status", style="blue")
    table.add_column("Scheduled", style="yellow")
    table.add_column("Retries", style="dim")

    for record in engine._rotation_records.values():
        if credential and record.credential_name != credential:
            continue

        table.add_row(
            record.credential_name,
            record.policy_name,
            record.status.value,
            record.scheduled_at.strftime("%Y-%m-%d %H:%M") if record.scheduled_at else "N/A",
            str(record.retry_count),
        )

    console.print(table)
```

---

## Cross-References

- **ADR-001 (Storage Backend):** Defines the storage backends used by the rotation engine to store new credentials and remove old ones during the cleanup phase.
- **ADR-002 (Encryption Model):** Defines the encryption model used when storing rotated credentials. The key versioning strategy enables re-encryption with updated parameters during rotation.
- **SOTA Research (CREDENTIALS_MGMT_SOTA_001):** Comprehensive analysis of credential rotation strategies, including scheduled, event-driven, and policy-based approaches.
- **NIST SP 800-53 IA-5:** Authenticator Management — requires periodic credential rotation.
- **SOC 2 CC6.1:** Logical Access Security — requires credential lifecycle management.

---

*This ADR was proposed on 2026-04-03. Implementation is planned for the next development cycle. The existing `TokenRefreshScheduler` and `AutomationEngine` provide partial infrastructure for this feature.*
