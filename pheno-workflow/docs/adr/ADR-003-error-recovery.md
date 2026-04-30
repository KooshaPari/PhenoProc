# ADR-003: Error Recovery Strategy

**Document ID:** PHENOTYPE_PHENOWORKFLOW_ADR_003  
**Status:** Proposed  
**Last Updated:** 2026-04-03  
**Author:** Phenotype Architecture Team  
**Supersedes:** N/A  
**Related:** ADR-001 (Workflow Execution Model), ADR-002 (DAG Scheduler)

---

## Table of Contents

1. [Title](#title)
2. [Context](#context)
3. [Decision](#decision)
4. [Consequences](#consequences)
5. [Implementation Details](#implementation-details)
6. [Alternatives Considered](#alternatives-considered)
7. [References](#references)

---

## Context

### Problem Statement

Workflow execution is inherently unreliable. Steps can fail due to:

- **Transient failures**: Network timeouts, temporary service unavailability, rate limiting
- **Permanent failures**: Invalid input, missing resources, logic errors
- **Infrastructure failures**: Process crashes, out-of-memory, disk full
- **External failures**: Third-party API errors, database connection issues

The error recovery strategy must handle all these failure modes while maintaining
workflow consistency and providing clear visibility into what went wrong.

### Forces

| Force | Description | Tension |
|-------|-------------|---------|
| Reliability | Workflows should complete successfully | vs. accepting inevitable failures |
| Consistency | Partial failures shouldn't corrupt state | vs. performance overhead |
| Visibility | Failures should be observable and debuggable | vs. noise from transient errors |
| Recovery | Failed workflows should be recoverable | vs. complexity of recovery logic |
| Simplicity | Error handling shouldn't overwhelm business logic | vs. comprehensive coverage |

### Current State

The current implementation provides basic retry with exponential backoff:

```python
# Current retry implementation (orchestrator.py:443-514)
max_retries = step.retry_policy.get("max_retries", 3)
backoff_factor = step.retry_policy.get("backoff_factor", 2)

for attempt in range(max_retries + 1):
    try:
        if attempt > 0:
            result.status = StepStatus.RETRYING
            await asyncio.sleep(backoff_factor ** attempt)

        if step.timeout:
            output = await asyncio.wait_for(
                self._call_handler(step.handler, execution.context),
                timeout=step.timeout,
            )
        else:
            output = await self._call_handler(step.handler, execution.context)

        result.status = StepStatus.COMPLETED
        result.output = output
        return result

    except TimeoutError:
        if attempt == max_retries:
            result.status = StepStatus.FAILED
            if step.on_failure == "fail":
                raise
            if step.on_failure == "continue":
                return result

    except Exception as e:
        if attempt == max_retries:
            result.status = StepStatus.FAILED
            if step.on_failure == "fail":
                raise
            if step.on_failure == "continue":
                return result
```

**Identified Gaps:**
1. No distinction between transient and permanent failures
2. No circuit breaker to prevent cascading failures
3. No dead letter queue for permanently failed steps
4. No automatic workflow resume after infrastructure recovery
5. No compensation for partially completed workflows (saga pattern exists separately)
6. No retry budget or rate limiting
7. No exponential backoff with jitter (thundering herd risk)

### Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | Retry transient failures with configurable policy | Must |
| R2 | Distinguish transient vs. permanent failures | Must |
| R3 | Support exponential backoff with jitter | Must |
| R4 | Support per-step and per-workflow timeouts | Must |
| R5 | Support configurable failure behavior (fail/continue/skip) | Must |
| R6 | Support saga compensation for distributed transactions | Must |
| R7 | Circuit breaker for repeated failures | Should |
| R8 | Dead letter queue for permanently failed steps | Should |
| R9 | Automatic workflow resume after recovery | Should |
| R10 | Retry budget to prevent infinite retry loops | Should |
| R11 | Error classification and categorization | Should |
| R12 | Structured error reporting with context | Should |

---

## Decision

### Chosen Approach: Layered Error Recovery with Classification, Retry, and Compensation

We adopt a **layered error recovery strategy** with four distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│              Layered Error Recovery Strategy                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: Error Classification                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Classify errors as:                                │   │
│  │  - Transient (retryable)                            │   │
│  │  - Permanent (non-retryable)                        │   │
│  │  - Infrastructure (system-level)                    │   │
│  │  - Business logic (domain-specific)                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│  Layer 2: Retry Strategy                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  For transient errors:                              │   │
│  │  - Exponential backoff with jitter                  │   │
│  │  - Configurable max retries per step                │   │
│  │  - Retry budget per workflow                        │   │
│  │  - Circuit breaker for repeated failures            │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│  Layer 3: Failure Handling                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  For permanent/ exhausted errors:                   │   │
│  │  - on_failure: 'fail' — stop workflow               │   │
│  │  - on_failure: 'continue' — mark failed, continue   │   │
│  │  - on_failure: 'skip_branch' — skip dependents      │   │
│  │  - Dead letter queue for investigation              │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│  Layer 4: Compensation (Saga)                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  For distributed transactions:                      │   │
│  │  - Automatic compensation in reverse order          │   │
│  │  - Compensation retry with backoff                  │   │
│  │  - Compensation failure logging and alerting        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Layer 1: Error Classification

```python
from enum import Enum
from dataclasses import dataclass


class ErrorType(Enum):
    """Classification of error types for recovery decisions."""
    TRANSIENT = "transient"       # Temporary, retryable
    PERMANENT = "permanent"       # Won't succeed on retry
    INFRASTRUCTURE = "infrastructure"  # System-level issue
    BUSINESS = "business"         # Domain logic error
    TIMEOUT = "timeout"           # Execution timeout
    CANCELLED = "cancelled"       # Explicitly cancelled


@dataclass
class ClassifiedError:
    """Error with classification metadata."""
    original_error: Exception
    error_type: ErrorType
    message: str
    retryable: bool
    step_id: str | None = None
    context: dict | None = None


def classify_error(error: Exception) -> ClassifiedError:
    """
    Classify an exception for recovery decisions.

    Classification rules:
    - TimeoutError → TIMEOUT (retryable)
    - ConnectionError → TRANSIENT (retryable)
    - ValueError → PERMANENT (non-retryable)
    - KeyboardInterrupt → CANCELLED (non-retryable)
    - OSError with specific codes → TRANSIENT or INFRASTRUCTURE
    - All others → PERMANENT (conservative default)
    """
    if isinstance(error, TimeoutError):
        return ClassifiedError(
            original_error=error,
            error_type=ErrorType.TIMEOUT,
            message=str(error),
            retryable=True,
        )

    if isinstance(error, ConnectionError):
        return ClassifiedError(
            original_error=error,
            error_type=ErrorType.TRANSIENT,
            message=str(error),
            retryable=True,
        )

    if isinstance(error, ValueError):
        return ClassifiedError(
            original_error=error,
            error_type=ErrorType.PERMANENT,
            message=str(error),
            retryable=False,
        )

    if isinstance(error, KeyboardInterrupt):
        return ClassifiedError(
            original_error=error,
            error_type=ErrorType.CANCELLED,
            message="Execution cancelled",
            retryable=False,
        )

    if isinstance(error, OSError):
        # Some OS errors are transient (network), some are permanent
        if error.errno in (11, 104, 111):  # EAGAIN, ECONNRESET, ECONNREFUSED
            return ClassifiedError(
                original_error=error,
                error_type=ErrorType.TRANSIENT,
                message=str(error),
                retryable=True,
            )
        return ClassifiedError(
            original_error=error,
            error_type=ErrorType.INFRASTRUCTURE,
            message=str(error),
            retryable=True,
        )

    # Default: permanent (conservative)
    return ClassifiedError(
        original_error=error,
        error_type=ErrorType.PERMANENT,
        message=str(error),
        retryable=False,
    )
```

### Layer 2: Retry Strategy with Jitter

```python
import random
import asyncio


class RetryPolicy:
    """Configurable retry policy with exponential backoff and jitter."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retryable_errors: tuple[type[Exception], ...] = (
            TimeoutError,
            ConnectionError,
            OSError,
        ),
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retryable_errors = retryable_errors

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given attempt.

        Formula: min(base_delay * backoff_factor^attempt, max_delay)
        With jitter: delay * random(0.5, 1.5)

        Example (base=1, factor=2, max=60):
            Attempt 0: 1.0s  (no delay, first attempt)
            Attempt 1: 2.0s  (1 * 2^1)
            Attempt 2: 4.0s  (1 * 2^2)
            Attempt 3: 8.0s  (1 * 2^3)
            Attempt 4: 16.0s (1 * 2^4)
            Attempt 5: 32.0s (1 * 2^5)
            Attempt 6: 60.0s (capped at max_delay)
        """
        if attempt == 0:
            return 0.0

        delay = min(
            self.base_delay * (self.backoff_factor ** attempt),
            self.max_delay,
        )

        if self.jitter:
            # Full jitter: random(0, delay)
            delay = random.uniform(0, delay)

        return delay

    def is_retryable(self, error: Exception) -> bool:
        """Check if the error type is retryable."""
        return isinstance(error, self.retryable_errors)


async def execute_with_retry(
    handler,
    context: dict,
    policy: RetryPolicy,
    timeout: float | None = None,
) -> any:
    """
    Execute a handler with retry logic.

    Flow:
    1. Attempt execution
    2. If successful, return result
    3. If failed and retryable and retries remaining:
       a. Calculate delay with backoff + jitter
       b. Sleep for delay
       c. Go to step 1
    4. If failed and not retryable or no retries:
       a. Raise original error
    """
    last_error = None

    for attempt in range(policy.max_retries + 1):
        try:
            if timeout:
                result = await asyncio.wait_for(
                    _call_handler(handler, context),
                    timeout=timeout,
                )
            else:
                result = await _call_handler(handler, context)

            return result

        except Exception as e:
            last_error = e
            classified = classify_error(e)

            if not classified.retryable or not policy.is_retryable(e):
                # Non-retryable error, don't retry
                raise

            if attempt < policy.max_retries:
                delay = policy.get_delay(attempt + 1)
                await asyncio.sleep(delay)

    raise last_error
```

### Layer 3: Failure Handling with Dead Letter Queue

```python
from collections import deque
from datetime import datetime


@dataclass
class DeadLetterEntry:
    """Entry in the dead letter queue."""
    execution_id: str
    step_id: str
    error: ClassifiedError
    context_snapshot: dict
    timestamp: datetime = None
    retry_count: int = 0


class DeadLetterQueue:
    """
    Queue for permanently failed steps that need manual intervention.

    Entries can be:
    - Inspected for debugging
    - Replayed for retry
    - Archived after resolution
    """

    def __init__(self, max_size: int = 10000):
        self._queue: deque[DeadLetterEntry] = deque(maxlen=max_size)

    def add(self, entry: DeadLetterEntry):
        entry.timestamp = datetime.utcnow()
        self._queue.append(entry)

    def get_all(self) -> list[DeadLetterEntry]:
        return list(self._queue)

    def get_by_execution(self, execution_id: str) -> list[DeadLetterEntry]:
        return [e for e in self._queue if e.execution_id == execution_id]

    def clear(self):
        self._queue.clear()
```

### Layer 4: Saga Compensation

The saga pattern (already implemented in `patterns/saga.py`) provides
compensation for distributed transactions:

```python
# Saga compensation flow
async def _compensate(self, saga, context):
    """
    Compensate completed steps in reverse order.

    Flow:
    1. Get completed steps in reverse order
    2. For each step, execute its compensation function
    3. If compensation fails, log and continue (best effort)
    4. Mark saga as COMPENSATED
    """
    for step_name in reversed(context.completed_steps):
        step = next((s for s in saga.steps if s.name == step_name), None)
        if not step or not step.compensation:
            continue

        try:
            await self._call_action(step.compensation, context)
        except Exception as comp_error:
            # Log compensation failure but continue with other compensations
            logger.error(
                f"Compensation failed for {step_name}: {comp_error}"
            )
            # Add to dead letter queue for manual intervention
            self.dead_letter_queue.add(DeadLetterEntry(
                execution_id=context.saga_id,
                step_id=step_name,
                error=classify_error(comp_error),
                context_snapshot=context.data.copy(),
            ))
```

### Error Recovery Flow Diagram

```
Step Execution with Full Error Recovery:

┌─────────────────┐
│  Execute Step   │
└────────┬────────┘
         │
    ┌────┴────┐
    │Success? │──Yes──► Store result, continue
    └────┬────┘
         │ No
         ▼
┌─────────────────┐
│ Classify Error  │
└────────┬────────┘
         │
    ┌────┴────────────┐
    │                 │
    ▼                 ▼
┌─────────┐     ┌──────────┐
│Transient│     │Permanent │
└────┬────┘     └────┬─────┘
     │               │
     ▼               ▼
┌─────────────┐ ┌──────────────────┐
│Retry Policy?│ │on_failure = ?    │
└──────┬──────┘ └────────┬─────────┘
       │                 │
  ┌────┴────┐      ┌────┼────────┐
  │         │      │    │        │
  ▼         ▼      ▼    ▼        ▼
Retries   No more  fail continue skip_branch
remain   retries   │    │        │
  │         │      │    │        ▼
  ▼         ▼      ▼    ▼   Skip this step
Backoff   DLQ     Raise  Continue  and all
+ Retry   Queue   error  execution  dependents
  │         │
  └─────────┘
```

---

## Consequences

### Positive Consequences

1. **Intelligent retry**: Distinguishing transient from permanent failures prevents
   wasted retries on errors that will never succeed, reducing latency and resource usage.

2. **Jittered backoff**: Random jitter prevents the thundering herd problem where
   many failed steps retry simultaneously, overwhelming recovering services.

3. **Circuit breaker**: Prevents cascading failures by stopping retries to services
   that are consistently failing, giving them time to recover.

4. **Dead letter queue**: Permanently failed steps are captured with full context,
   enabling post-mortem analysis and manual retry without data loss.

5. **Saga compensation**: Automatic rollback of completed steps ensures data
   consistency even when workflows fail partway through.

6. **Configurable policies**: Per-step retry policies allow fine-tuning based on
   the reliability characteristics of each step's dependencies.

7. **Error classification**: Structured error types enable targeted alerting,
   metrics, and dashboards for different failure modes.

8. **Graceful degradation**: The `continue` and `skip_branch` failure modes allow
   workflows to complete partially, maximizing value delivery even with failures.

9. **Retry budgets**: Global retry limits prevent infinite retry loops that could
   exhaust resources or incur excessive costs.

10. **Observability**: Every error classification, retry, and compensation action
    is logged and emitted as an event, providing full visibility into recovery.

### Negative Consequences

1. **Increased complexity**: Four-layer error recovery adds significant complexity
    compared to simple retry logic, requiring more code to maintain and test.

2. **Classification overhead**: Error classification adds latency to every failed
    step execution, though this is negligible compared to the failure itself.

3. **Dead letter queue growth**: Without proper cleanup, the DLQ can grow unbounded,
    consuming memory. Requires periodic archival or external storage.

4. **Compensation failures**: If a compensation function itself fails, the system
    enters an inconsistent state that requires manual intervention.

5. **Jitter unpredictability**: Random jitter makes execution timing non-deterministic,
    which can complicate testing and performance analysis.

6. **Circuit breaker state**: Circuit breaker state is in-memory and lost on restart,
    potentially allowing retries to a still-failing service after recovery.

7. **Retry budget exhaustion**: A burst of failures can exhaust the retry budget,
    causing subsequent transient failures to be treated as permanent.

### Mitigations

| Risk | Mitigation | Status |
|------|-----------|--------|
| Complexity | Comprehensive tests, clear documentation | In Progress |
| DLQ growth | External storage backend, TTL-based cleanup | Planned |
| Compensation failures | Compensation retry, alerting, manual review | Planned |
| Jitter unpredictability | Seeded random for testing | Planned |
| Circuit breaker state | Persistent circuit breaker state | Future |
| Retry budget exhaustion | Per-step budgets, adaptive limits | Planned |

---

## Implementation Details

### Circuit Breaker Implementation

```python
import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for preventing cascading failures.

    State transitions:
        CLOSED → OPEN: When failure count exceeds threshold
        OPEN → HALF_OPEN: After recovery timeout
        HALF_OPEN → CLOSED: On successful request
        HALF_OPEN → OPEN: On failed request
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.half_open_calls = 0

    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False

        # HALF_OPEN
        return self.half_open_calls < self.half_open_max_calls

    def record_success(self):
        """Record a successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
        self.success_count += 1

    def record_failure(self):
        """Record a failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

### Structured Error Reporting

```python
@dataclass
class ErrorReport:
    """Structured error report for observability."""
    execution_id: str
    step_id: str
    error_type: ErrorType
    message: str
    stack_trace: str | None = None
    retry_count: int = 0
    total_retry_time: float = 0.0
    context_snapshot: dict | None = None
    timestamp: datetime = None
    resolved: bool = False


def create_error_report(
    execution: WorkflowExecution,
    step_id: str,
    classified: ClassifiedError,
    retry_count: int = 0,
    total_retry_time: float = 0.0,
) -> ErrorReport:
    """Create a structured error report for a failed step."""
    import traceback

    return ErrorReport(
        execution_id=execution.execution_id,
        step_id=step_id,
        error_type=classified.error_type,
        message=classified.message,
        stack_trace=traceback.format_exception(type(classified.original_error),
                                                classified.original_error,
                                                classified.original_error.__traceback__),
        retry_count=retry_count,
        total_retry_time=total_retry_time,
        context_snapshot=execution.context.copy(),
        timestamp=datetime.utcnow(),
    )
```

---

## Alternatives Considered

### Alternative 1: Simple Retry Only

Retry all failures with fixed backoff.

**Pros:**
- Simplest implementation
- Handles most transient failures
- Low overhead

**Cons:**
- Wastes time retrying permanent failures
- No protection against cascading failures
- No visibility into failure patterns

**Verdict:** Rejected. Insufficient for production workloads.

### Alternative 2: All-or-Nothing Compensation

Rollback entire workflow on any failure.

**Pros:**
- Guaranteed consistency
- Simple mental model
- No partial state

**Cons:**
- Wasteful for non-critical failures
- No graceful degradation
- Expensive compensation for long workflows

**Verdict:** Rejected. Too rigid for diverse workflow requirements.

### Alternative 3: External Error Handler

Delegate error handling to an external service.

**Pros:**
- Centralized error management
- Cross-workflow error correlation
- Advanced analytics

**Cons:**
- External dependency
- Network latency for error handling
- Single point of failure

**Verdict:** Rejected as primary approach, but external integration planned for future.

---

## References

- [ADR-001: Workflow Execution Model](./ADR-001-workflow-model.md)
- [ADR-002: DAG Scheduler Design](./ADR-002-dag-scheduler.md)
- [SOTA: Error Recovery](../research/WORKFLOW_ENGINES_SOTA.md#14-error-recovery-and-resilience)
- `src/pheno_workflow/patterns/saga.py` — Saga compensation implementation
- `src/pheno_workflow/orchestrator.py:428-516` — Current retry logic
- Nygard, M. "Release It!" — Circuit breaker pattern
- Bulkhead pattern — Isolating failures in distributed systems

---

*End of ADR-003*
