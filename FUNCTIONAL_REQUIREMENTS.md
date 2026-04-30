# Functional Requirements — PhenoProc

Traces to: PRD.md epics E1–E6.
ID format: FR-PHENOPROC-{NNN}.

---

## Process Registry

**FR-PHENOPROC-001**: The system SHALL maintain a registry of long-running processes (daemons, services, workers) with metadata (name, version, status, health).
Traces to: E1.1

**FR-PHENOPROC-002**: The system SHALL expose a CLI interface for querying process status, starting, stopping, and restarting services.
Traces to: E1.2

**FR-PHENOPROC-003**: The system SHALL detect and report process failures with automatic restart attempts and escalation policies.
Traces to: E1.3

---

## Health & Monitoring

**FR-PHENOPROC-004**: The system SHALL execute health checks (HTTP, TCP, command-based) for registered processes at configurable intervals.
Traces to: E2.1

**FR-PHENOPROC-005**: The system SHALL emit health events to the event bus for integration with observability systems.
Traces to: E2.2

---

## Lifecycle Management

**FR-PHENOPROC-006**: The system SHALL support ordered startup and shutdown sequences based on service dependencies.
Traces to: E3.1

---

## Trace & Test Guidance

All tests MUST reference a Functional Requirement (FR):

```rust
// Traces to: FR-PHENOPROC-NNN
#[test]
fn test_process_registry() { ... }
```
