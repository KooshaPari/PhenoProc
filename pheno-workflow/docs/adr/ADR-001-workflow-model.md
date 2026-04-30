# ADR-001: Workflow Execution Model

**Document ID:** PHENOTYPE_PHENOWORKFLOW_ADR_001  
**Status:** Accepted  
**Last Updated:** 2026-04-03  
**Author:** Phenotype Architecture Team  
**Supersedes:** N/A  
**Related:** ADR-002 (DAG Scheduler), ADR-003 (Error Recovery)

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

The Phenotype ecosystem requires a workflow execution model that can handle:

- **Complex business processes** spanning multiple services and systems
- **Long-running operations** that may take minutes to days (e.g., human approvals)
- **Distributed transactions** requiring atomic-like guarantees across service boundaries
- **Fault tolerance** with automatic recovery from transient failures
- **Developer ergonomics** that feel natural in Python

The core challenge is designing an execution model that balances simplicity for common
cases with the power needed for complex, production-grade workflows.

### Forces

| Force | Description | Tension |
|-------|-------------|---------|
| Simplicity | Developers should understand the model easily | vs. power for complex cases |
| Performance | Low overhead for simple workflows | vs. durability guarantees |
| Flexibility | Support multiple workflow patterns | vs. focused, opinionated design |
| Testability | Easy to test workflows in isolation | vs. integration with real backends |
| Durability | Survive process crashes and restarts | vs. in-memory simplicity |

### Current State

The existing implementation in `pheno-workflow` provides three distinct execution models:

1. **`WorkflowOrchestrator`** (`orchestrator.py`): DAG-based with wave execution
2. **`WorkflowEngine`** (`core/engine.py`): Class-based decorator workflows
3. **`WorkflowEngine`** (`patterns/workflow.py`): Simple sequential workflow

This multiplicity creates confusion and inconsistency. A unified execution model
is needed that provides a single, coherent API while supporting all required patterns.

### Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | Support DAG-based workflow definitions | Must |
| R2 | Support sequential and parallel step execution | Must |
| R3 | Support conditional branching | Must |
| R4 | Support retry with configurable policies | Must |
| R5 | Support timeout per step and per workflow | Must |
| R6 | Support event emission on state changes | Must |
| R7 | Support pluggable execution backends | Should |
| R8 | Support human-in-the-loop workflows | Should |
| R9 | Support saga pattern for compensation | Must |
| R10 | Support workflow state persistence | Should |

---

## Decision

### Chosen Approach: Unified Multi-Model Execution with Pluggable Backends

We adopt a **unified execution model** that provides three complementary workflow
definition styles, all backed by a single execution engine with pluggable backends:

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Execution Model                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Definition Layer (Multiple Styles):                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │  DAG-Based   │ │  Decorator   │ │  Programmatic│       │
│  │  (Orchestr.) │ │  (@workflow) │ │  (Builder)   │       │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘       │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          │                                 │
│  ┌───────────────────────┴───────────────────────────┐    │
│  │              Execution Engine                      │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐          │    │
│  │  │  DAG     │ │  State   │ │  Saga    │          │    │
│  │  │  Executor│ │  Machine │ │  Executor│          │    │
│  │  └──────────┘ └──────────┘ └──────────┘          │    │
│  └───────────────────────┬───────────────────────────┘    │
│                          │                                 │
│  ┌───────────────────────┴───────────────────────────┐    │
│  │              Backend Abstraction                   │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐          │    │
│  │  │  In-     │ │  Redis/  │ │Temporal  │          │    │
│  │  │  Memory  │ │  Postgres│ │ (Future) │          │    │
│  │  └──────────┘ └──────────┘ └──────────┘          │    │
│  └───────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Core Execution Model

The execution model is defined by these principles:

1. **Workflows are DAGs**: Every workflow is fundamentally a directed acyclic graph
2. **Steps are the unit of execution**: Each node in the DAG is a step with a handler
3. **Wave-based parallelism**: Independent steps execute in parallel waves
4. **Context is shared**: A mutable context dictionary flows through all steps
5. **Events are emitted**: Every state change produces an event
6. **Backends are pluggable**: The same workflow definition runs on any backend

### Execution Flow

```
Workflow Execution Flow:

┌─────────────┐
│  Register   │
│  Workflow   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  Validate   │────►│  Build DAG  │
│  (cycles,   │     │  + Topo     │
│   deps)     │     │  Sort       │
└─────────────┘     └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Execute    │
                    │  Waves      │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Step    │ │  Step    │ │  Step    │
        │  Exec    │ │  Exec    │ │  Exec    │
        │  + Retry │ │  + Retry │ │  + Retry │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             └────────────┼────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Aggregate  │
                   │  Results    │
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Persist    │
                   │  State      │
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Emit       │
                   │  Events     │
                   └─────────────┘
```

### Step Execution Contract

Every step follows this contract:

```python
# Step execution contract
async def execute_step(step: WorkflowStep, context: dict) -> StepResult:
    """
    Execute a single step with the following guarantees:

    1. Context is passed by reference (mutable)
    2. Step output is stored in context under step_{id}_output
    3. Events are emitted for each state transition
    4. Retries follow the step's retry policy
    5. Timeouts are enforced per step
    6. Failures follow the step's on_failure behavior

    Returns:
        StepResult with status, output, and timing information
    """
```

### State Transitions

```
Workflow State Machine:

                ┌─────────┐
                │ PENDING │
                └────┬────┘
                     │ execute()
                     ▼
                ┌─────────┐
           ┌───►│ RUNNING │◄───┐
           │    └────┬────┘    │
           │         │         │
     pause()│    complete()    │ resume()
           │         │         │
           │         ▼         │
           │    ┌─────────┐    │
           │    │COMPLETED│    │
           │    └─────────┘    │
           │                   │
           │    ┌─────────┐    │
           ├───►│ FAILED  │    │
           │    └─────────┘    │
           │                   │
           │    ┌─────────┐    │
           ├───►│PAUSED   │    │
           │    └─────────┘    │
           │                   │
           │    ┌─────────┐    │
           └───►│CANCELLED│    │
                └─────────┘
```

### Python Implementation

The core execution model is implemented as:

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
from uuid import uuid4
from datetime import datetime


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow DAG."""
    step_id: str
    handler: Callable
    dependencies: list[str] = field(default_factory=list)
    condition: Callable[[dict[str, Any]], bool] | None = None
    retry_policy: dict[str, Any] = field(
        default_factory=lambda: {"max_retries": 3, "backoff_factor": 2}
    )
    timeout: int | None = None
    on_failure: str = "fail"  # 'fail', 'continue', 'skip_branch'


@dataclass
class WorkflowDefinition:
    """Defines a workflow as a DAG of steps."""
    workflow_id: str
    name: str
    steps: dict[str, WorkflowStep] = field(default_factory=dict)

    def validate(self) -> tuple[bool, list[str]]:
        """Validate DAG: check for cycles and invalid dependencies."""
        errors = []
        if self._has_cycle():
            errors.append("Workflow contains cycles")
        for step_id, step in self.steps.items():
            for dep in step.dependencies:
                if dep not in self.steps:
                    errors.append(f"Step {step_id} has invalid dependency: {dep}")
        return len(errors) == 0, errors


@dataclass
class WorkflowExecution:
    """Tracks a running or completed workflow instance."""
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    context: dict[str, Any] = field(default_factory=dict)
    step_results: dict[str, StepResult] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
```

### Backend Abstraction

```python
from abc import ABC, abstractmethod


class WorkflowBackend(ABC):
    """Abstract backend for workflow state persistence."""

    @abstractmethod
    async def save_execution(self, execution: WorkflowExecution) -> None:
        """Persist execution state."""

    @abstractmethod
    async def load_execution(self, execution_id: str) -> WorkflowExecution | None:
        """Load execution state."""

    @abstractmethod
    async def list_executions(
        self, workflow_id: str | None = None, status: WorkflowStatus | None = None,
    ) -> list[WorkflowExecution]:
        """List executions with optional filters."""


class InMemoryBackend(WorkflowBackend):
    """In-memory backend for development and testing."""

    def __init__(self):
        self._store: dict[str, WorkflowExecution] = {}

    async def save_execution(self, execution):
        self._store[execution.execution_id] = execution

    async def load_execution(self, execution_id):
        return self._store.get(execution_id)

    async def list_executions(self, workflow_id=None, status=None):
        executions = list(self._store.values())
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        if status:
            executions = [e for e in executions if e.status == status]
        return executions
```

---

## Consequences

### Positive Consequences

1. **Unified API**: Developers learn one execution model that works across all workflow
   styles (DAG, decorator, programmatic), reducing cognitive load and training time.

2. **Pluggable backends**: The same workflow definition can run in-memory for testing
   and on Temporal for production without code changes, enabling gradual migration.

3. **Wave-based parallelism**: Independent steps execute concurrently, maximizing
   throughput without requiring developers to manage concurrency explicitly.

4. **Event-driven architecture**: Every state change produces an event, enabling
   real-time monitoring, alerting, and integration with external systems.

5. **Context propagation**: A shared mutable context simplifies data flow between
   steps, eliminating the need for explicit parameter passing.

6. **Validation at registration**: Workflow definitions are validated (cycle detection,
   dependency checking) before execution, catching errors early.

7. **Flexible failure handling**: Per-step `on_failure` behavior (`fail`, `continue`,
   `skip_branch`) allows fine-grained control over error propagation.

8. **Retry with exponential backoff**: Built-in retry logic with configurable policies
   handles transient failures without application code changes.

9. **Timeout enforcement**: Per-step and per-workflow timeouts prevent resource
   exhaustion from hung operations.

10. **Testability**: The in-memory backend and deterministic execution model make
    workflows easy to test in isolation without external dependencies.

### Negative Consequences

1. **Shared mutable context**: The mutable context dictionary can lead to subtle bugs
    if steps modify context in unexpected ways. Requires discipline and documentation.

2. **No built-in type safety**: Context is `dict[str, Any]`, providing no compile-time
    guarantees about data flowing between steps. Pydantic models can mitigate this.

3. **In-memory state loss**: The default backend loses state on process restart.
    Requires explicit backend configuration for production durability.

4. **Wave execution granularity**: Parallelism is limited to wave boundaries. Steps
    within a wave all start together, which may not be optimal for resource usage.

5. **No built-in step result validation**: Step outputs are stored in context without
    validation. Invalid data can propagate to downstream steps.

6. **Single-process limitation**: The current model assumes single-process execution.
    Distributed execution requires the Temporal backend.

### Mitigations

| Risk | Mitigation | Status |
|------|-----------|--------|
| Mutable context bugs | Document best practices, add context immutability option | Planned |
| No type safety | Support Pydantic models for context validation | Planned |
| State loss | Default to Redis backend in production configs | Planned |
| Wave granularity | Add priority-based scheduling within waves | Future |
| No output validation | Add output schema validation per step | Planned |
| Single-process | Complete Temporal backend integration | In Progress |

---

## Implementation Details

### Wave Execution Algorithm

The wave-based execution algorithm uses Kahn's algorithm for topological sorting:

```python
def _build_execution_plan(self, workflow: WorkflowDefinition) -> list[list[str]]:
    """
    Build execution plan as waves of steps that can run in parallel.

    Algorithm: Kahn's algorithm for topological sort with wave grouping.

    Complexity:
        Time: O(V + E) where V = steps, E = dependencies
        Space: O(V) for in-degree tracking

    Returns:
        List of waves, where each wave is a list of step IDs
        that can execute concurrently.
    """
    # Calculate in-degree for each step
    in_degree = dict.fromkeys(workflow.steps, 0)
    for step in workflow.steps.values():
        for _dep in step.dependencies:
            in_degree[step.step_id] += 1

    waves = []
    remaining = set(workflow.steps.keys())

    while remaining:
        # Find all steps with no remaining dependencies
        wave = [s for s in remaining if in_degree[s] == 0]

        if not wave:
            raise RuntimeError("Circular dependency detected during execution")

        waves.append(wave)

        # Remove wave steps and update in-degrees
        for step_id in wave:
            remaining.remove(step_id)
            for other_step in workflow.steps.values():
                if step_id in other_step.dependencies:
                    in_degree[other_step.step_id] -= 1

    return waves
```

### Step Execution with Retry

```python
async def _execute_step(
    self, step: WorkflowStep, execution: WorkflowExecution,
) -> StepResult:
    """
    Execute a single step with retry logic and timeout enforcement.

    Retry behavior:
        - Max retries from step.retry_policy['max_retries'] (default: 3)
        - Backoff: backoff_factor^attempt seconds (default: 2^attempt)
        - Events emitted: step.started, step.retrying, step.completed, step.failed

    Timeout behavior:
        - If step.timeout is set, asyncio.wait_for enforces it
        - TimeoutError is treated as a failure and retried
    """
    max_retries = step.retry_policy.get("max_retries", 3)
    backoff_factor = step.retry_policy.get("backoff_factor", 2)

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                await asyncio.sleep(backoff_factor ** attempt)

            if step.timeout:
                output = await asyncio.wait_for(
                    self._call_handler(step.handler, execution.context),
                    timeout=step.timeout,
                )
            else:
                output = await self._call_handler(step.handler, execution.context)

            # Store output in context for downstream steps
            execution.context[f"step_{step.step_id}_output"] = output
            return StepResult(
                step_id=step.step_id,
                status=StepStatus.COMPLETED,
                output=output,
            )

        except Exception as e:
            if attempt == max_retries:
                if step.on_failure == "fail":
                    raise
                return StepResult(
                    step_id=step.step_id,
                    status=StepStatus.FAILED,
                    error=str(e),
                )
```

### Event System

```python
class WorkflowExecution:
    def emit_event(self, event_type: str, data: dict | None = None):
        """
        Emit a workflow event.

        Event format:
        {
            "type": "workflow.started" | "step.completed" | ...,
            "timestamp": "2026-04-03T12:00:00.000Z",
            "data": {...}
        }

        Events are appended to the execution's event log and
        trigger registered event handlers asynchronously.
        """
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {},
        }
        self.events.append(event)
```

---

## Alternatives Considered

### Alternative 1: Pure Sequential Execution

Execute steps one at a time in dependency order.

**Pros:**
- Simplest implementation
- Easy to debug and reason about
- No concurrency concerns

**Cons:**
- No parallelism, poor performance for independent steps
- Doesn't leverage modern multi-core systems
- Not suitable for I/O-bound workflows

**Verdict:** Rejected. Parallelism is a core requirement.

### Alternative 2: Full Actor Model

Each step is an independent actor communicating via message passing.

**Pros:**
- Natural distribution across processes/machines
- Excellent fault isolation
- Highly scalable

**Cons:**
- Significant complexity overhead
- Overkill for single-process workflows
- Different mental model from Python's async/await

**Verdict:** Rejected. Too complex for current requirements.

### Alternative 3: State Machine Only

Model everything as state transitions.

**Pros:**
- Formal verification possible
- Clear state transitions
- Well-understood theory

**Cons:**
- Verbose for simple workflows
- Hard to express parallel execution
- Doesn't map well to DAG-based workflows

**Verdict:** Rejected as primary model, but used as a pattern within workflows.

---

## References

- [ADR-002: DAG Scheduler Design](./ADR-002-dag-scheduler.md)
- [ADR-003: Error Recovery Strategy](./ADR-003-error-recovery.md)
- [SOTA: Workflow Engines](../research/WORKFLOW_ENGINES_SOTA.md)
- `src/pheno_workflow/orchestrator.py` — WorkflowOrchestrator implementation
- `src/pheno_workflow/core/engine.py` — WorkflowEngine implementation
- `src/pheno_workflow/core/workflow.py` — Decorator-based workflow definition

---

*End of ADR-001*
