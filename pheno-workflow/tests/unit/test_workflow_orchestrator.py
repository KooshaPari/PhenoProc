"""
Comprehensive tests for workflow orchestration.

Tests cover:
- Basic workflow execution
- Sequential and parallel steps
- Conditional branching
- Error handling and retries
- State tracking and persistence
- Event emission
- Workflow triggers
- Cycle detection
"""

import asyncio
from datetime import datetime

import pytest

pytest_plugins = ("pytest_asyncio",)

from pheno_workflow.orchestrator import (
    StepStatus,
    TriggerType,
    WorkflowDefinition,
    WorkflowOrchestrator,
    WorkflowStatus,
    WorkflowStep,
    WorkflowTrigger,
    build_parallel_workflow,
    build_simple_workflow,
)

# Test fixtures and helpers


@pytest.fixture
def orchestrator():
    """Create a fresh orchestrator instance."""
    return WorkflowOrchestrator()


def simple_handler(context: dict) -> str:
    """Simple synchronous handler."""
    return f"processed: {context.get('input', 'default')}"


async def async_handler(context: dict) -> str:
    """Simple async handler."""
    await asyncio.sleep(0.01)
    return f"async processed: {context.get('input', 'default')}"


def failing_handler(context: dict) -> str:
    """Handler that always fails."""
    raise ValueError("Intentional failure")


def conditional_true(context: dict) -> bool:
    """Condition that returns true."""
    return context.get("condition", True)


def conditional_false(context: dict) -> bool:
    """Condition that returns false."""
    return False


# Basic workflow execution tests


@pytest.mark.asyncio
async def test_simple_sequential_workflow(orchestrator):
    """Test basic sequential workflow execution."""
    workflow = build_simple_workflow(
        "test_workflow",
        [
            ("step1", simple_handler),
            ("step2", simple_handler),
            ("step3", simple_handler),
        ],
    )

    orchestrator.register_workflow(workflow)
    execution = await orchestrator.execute_workflow(
        workflow.workflow_id,
        context={"input": "test"},
    )

    assert execution.status == WorkflowStatus.COMPLETED
    assert len(execution.step_results) == 3
    assert all(r.status == StepStatus.COMPLETED for r in execution.step_results.values())
    assert execution.started_at is not None
    assert execution.completed_at is not None


@pytest.mark.asyncio
async def test_async_handler_workflow(orchestrator):
    """Test workflow with async handlers."""
    workflow = WorkflowDefinition(workflow_id="async_workflow", name="Async Test")
    workflow.add_step(WorkflowStep(step_id="async_step1", handler=async_handler))
    workflow.add_step(
        WorkflowStep(
            step_id="async_step2",
            handler=async_handler,
            dependencies=["async_step1"],
        ),
    )

    orchestrator.register_workflow(workflow)
    execution = await orchestrator.execute_workflow(
        workflow.workflow_id,
        context={"input": "async_test"},
    )

    assert execution.status == WorkflowStatus.COMPLETED
    assert execution.step_results["async_step1"].status == StepStatus.COMPLETED
    assert execution.step_results["async_step2"].status == StepStatus.COMPLETED


# Parallel execution tests


@pytest.mark.asyncio
async def test_parallel_workflow(orchestrator):
    """Test parallel step execution."""
    workflow = build_parallel_workflow(
        "parallel_test",
        [
            ("parallel1", async_handler),
            ("parallel2", async_handler),
            ("parallel3", async_handler),
        ],
    )

    orchestrator.register_workflow(workflow)
    start_time = datetime.utcnow()
    execution = await orchestrator.execute_workflow(workflow.workflow_id)
    end_time = datetime.utcnow()

    assert execution.status == WorkflowStatus.COMPLETED
    assert len(execution.step_results) == 3

    # Verify they ran in parallel (should be faster than sequential)
    duration = (end_time - start_time).total_seconds()
    # 3 steps * 0.01s each = 0.03s sequential, but parallel should be ~0.01s
    assert duration < 0.1  # Allow some overhead


@pytest.mark.asyncio
async def test_mixed_parallel_sequential(orchestrator):
    """Test workflow with both parallel and sequential steps."""
    workflow = WorkflowDefinition(workflow_id="mixed", name="Mixed Execution")

    # First wave (parallel)
    workflow.add_step(WorkflowStep(step_id="p1", handler=simple_handler))
    workflow.add_step(WorkflowStep(step_id="p2", handler=simple_handler))

    # Second wave (depends on first wave)
    workflow.add_step(
        WorkflowStep(step_id="seq1", handler=simple_handler, dependencies=["p1", "p2"]),
    )

    # Third wave
    workflow.add_step(WorkflowStep(step_id="final", handler=simple_handler, dependencies=["seq1"]))

    orchestrator.register_workflow(workflow)
    execution = await orchestrator.execute_workflow(workflow.workflow_id)

    assert execution.status == WorkflowStatus.COMPLETED
    assert len(execution.step_results) == 4

    # Verify execution order
    p1_time = execution.step_results["p1"].completed_at
    p2_time = execution.step_results["p2"].completed_at
    seq1_time = execution.step_results["seq1"].started_at
    final_time = execution.step_results["final"].started_at

    # seq1 should start after p1 and p2 complete
    assert seq1_time > p1_time
    assert seq1_time > p2_time
    # final should start after seq1 completes
    assert final_time > execution.step_results["seq1"].completed_at


# Conditional branching tests


@pytest.mark.asyncio
async def test_conditional_step_execution(orchestrator):
    """Test conditional step execution."""
    workflow = WorkflowDefinition(workflow_id="conditional", name="Conditional Test")

    workflow.add_step(WorkflowStep(step_id="always", handler=simple_handler))

    workflow.add_step(
        WorkflowStep(
            step_id="conditional_true",
            handler=simple_handler,
            condition=conditional_true,
            dependencies=["always"],
        ),
    )

    workflow.add_step(
        WorkflowStep(
            step_id="conditional_false",
            handler=simple_handler,
            condition=conditional_false,
            dependencies=["always"],
        ),
    )

    orchestrator.register_workflow(workflow)
    execution = await orchestrator.execute_workflow(
        workflow.workflow_id,
        context={"condition": True},
    )

    assert execution.status == WorkflowStatus.COMPLETED
    assert execution.step_results["always"].status == StepStatus.COMPLETED
    assert execution.step_results["conditional_true"].status == StepStatus.COMPLETED
    assert execution.step_results["conditional_false"].status == StepStatus.SKIPPED


@pytest.mark.asyncio
async def test_async_condition(orchestrator):
    """Test async condition evaluation."""

    async def async_condition(context: dict) -> bool:
        await asyncio.sleep(0.01)
        return context.get("flag", False)

    workflow = WorkflowDefinition(workflow_id="async_cond", name="Async Condition")
    workflow.add_step(
        WorkflowStep(step_id="conditional", handler=simple_handler, condition=async_condition),
    )

    orchestrator.register_workflow(workflow)

    # Test with flag=True
    execution1 = await orchestrator.execute_workflow(
        workflow.workflow_id,
        context={"flag": True},
    )
    assert execution1.step_results["conditional"].status == StepStatus.COMPLETED

    # Test with flag=False
    execution2 = await orchestrator.execute_workflow(
        workflow.workflow_id,
        context={"flag": False},
    )
    assert execution2.step_results["conditional"].status == StepStatus.SKIPPED


# Error handling and retry tests


@pytest.mark.asyncio
async def test_step_retry_on_failure(orchestrator):
    """Test step retry mechanism."""
    call_count = {"count": 0}

    def failing_then_succeeding(context: dict) -> str:
        call_count["count"] += 1
        if call_count["count"] < 3:
            raise ValueError("Not yet")
        return "success"

    workflow = WorkflowDefinition(workflow_id="retry_test", name="Retry Test")
    workflow.add_step(
        WorkflowStep(
            step_id="retry_step",
            handler=failing_then_succeeding,
            retry_policy={"max_retries": 3, "backoff_factor": 1},
        ),
    )

    orchestrator.register_workflow(workflow)
    execution = await orchestrator.execute_workflow(workflow.workflow_id)

    assert execution.status == WorkflowStatus.COMPLETED
    assert execution.step_results["retry_step"].status == StepStatus.COMPLETED
    assert execution.step_results["retry_step"].retry_count == 2  # Failed twice, succeeded third
    assert call_count["count"] == 3


@pytest.mark.asyncio
async def test_step_failure_propagation(orchestrator):
    """Test that step failures propagate correctly."""
    workflow = WorkflowDefinition(workflow_id="fail_test", name="Failure Test")
    workflow.add_step(
        WorkflowStep(
            step_id="failing_step",
            handler=failing_handler,
            retry_policy={"max_retries": 1, "backoff_factor": 1},
        ),
    )

    orchestrator.register_workflow(workflow)

    with pytest.raises(ValueError, match="Intentional failure"):
        await orchestrator.execute_workflow(workflow.workflow_id)


@pytest.mark.asyncio
async def test_step_failure_continue(orchestrator):
    """Test step failure with continue behavior."""
    workflow = WorkflowDefinition(workflow_id="fail_continue", name="Fail Continue")

    workflow.add_step(
        WorkflowStep(
            step_id="failing",
            handler=failing_handler,
            on_failure="continue",
            retry_policy={"max_retries": 0},
        ),
    )

    workflow.add_step(
        WorkflowStep(step_id="after_fail", handler=simple_handler, dependencies=["failing"]),
    )

    orchestrator.register_workflow(workflow)
    execution = await orchestrator.execute_workflow(workflow.workflow_id)

    # Workflow should complete despite step failure
    assert execution.status == WorkflowStatus.COMPLETED
    assert execution.step_results["failing"].status == StepStatus.FAILED
    # after_fail should be skipped because dependency failed
    assert execution.step_results["after_fail"].status == StepStatus.SKIPPED


@pytest.mark.asyncio
async def test_step_timeout(orchestrator):
    """Test step timeout handling."""

    async def slow_handler(context: dict) -> str:
        await asyncio.sleep(2)
        return "too slow"

    workflow = WorkflowDefinition(workflow_id="timeout_test", name="Timeout Test")
    workflow.add_step(
        WorkflowStep(
            step_id="slow_step",
            handler=slow_handler,
            timeout=1,
            retry_policy={"max_retries": 0},
            on_failure="continue",
        ),
    )

    orchestrator.register_workflow(workflow)
    execution = await orchestrator.execute_workflow(workflow.workflow_id)

    assert execution.step_results["slow_step"].status == StepStatus.FAILED
    assert "timed out" in execution.step_results["slow_step"].error


# Workflow validation tests


def test_workflow_cycle_detection():
    """Test that cycles are detected in workflow definitions."""
    workflow = WorkflowDefinition(workflow_id="cycle", name="Cycle Test")

    # Create a cycle: A -> B -> C -> A
    workflow.add_step(WorkflowStep(step_id="A", handler=simple_handler, dependencies=["C"]))
    workflow.add_step(WorkflowStep(step_id="B", handler=simple_handler, dependencies=["A"]))
    workflow.add_step(WorkflowStep(step_id="C", handler=simple_handler, dependencies=["B"]))

    is_valid, errors = workflow.validate()
    assert not is_valid
    assert "cycle" in errors[0].lower()


def test_workflow_invalid_dependency():
    """Test detection of invalid dependencies."""
    workflow = WorkflowDefinition(workflow_id="invalid_dep", name="Invalid Dependency")

    workflow.add_step(
        WorkflowStep(step_id="step1", handler=simple_handler, dependencies=["nonexistent"]),
    )

    is_valid, errors = workflow.validate()
    assert not is_valid
    assert "invalid dependency" in errors[0].lower()


def test_workflow_validation_success():
    """Test successful workflow validation."""
    workflow = WorkflowDefinition(workflow_id="valid", name="Valid Workflow")
    workflow.add_step(WorkflowStep(step_id="step1", handler=simple_handler))
    workflow.add_step(WorkflowStep(step_id="step2", handler=simple_handler, dependencies=["step1"]))

    is_valid, errors = workflow.validate()
    assert is_valid
    assert len(errors) == 0


# State persistence tests


@pytest.mark.asyncio
async def test_state_persistence(orchestrator):
    """Test that execution state is persisted."""
    workflow = build_simple_workflow("persist_test", [("step1", simple_handler)])

    orchestrator.register_workflow(workflow)
    execution = await orchestrator.execute_workflow(workflow.workflow_id)

    # Check that state was persisted
    assert execution.execution_id in orchestrator.state_backend
    persisted = orchestrator.state_backend[execution.execution_id]

    assert persisted["execution_id"] == execution.execution_id
    assert persisted["workflow_id"] == workflow.workflow_id
    assert persisted["status"] == WorkflowStatus.COMPLETED.value
    assert persisted["successful_steps"] == 1
    assert persisted["failed_steps"] == 0


# Event emission tests


@pytest.mark.asyncio
async def test_event_emission(orchestrator):
    """Test that workflow events are emitted."""
    workflow = build_simple_workflow("event_test", [("step1", simple_handler)])

    events_received = []

    def event_handler(execution):
        events_received.append(execution.status)

    orchestrator.on_event("workflow.started", event_handler)
    orchestrator.on_event("workflow.completed", event_handler)

    orchestrator.register_workflow(workflow)
    execution = await orchestrator.execute_workflow(workflow.workflow_id)

    # Check events in execution object
    assert len(execution.events) > 0
    event_types = [e["type"] for e in execution.events]
    assert "workflow.started" in event_types
    assert "workflow.completed" in event_types
    assert "step.started" in event_types
    assert "step.completed" in event_types

    # Check event handlers were called
    assert WorkflowStatus.RUNNING in events_received
    assert WorkflowStatus.COMPLETED in events_received


@pytest.mark.asyncio
async def test_step_events(orchestrator):
    """Test step-level event emission."""
    workflow = WorkflowDefinition(workflow_id="step_events", name="Step Events")
    workflow.add_step(WorkflowStep(step_id="step1", handler=simple_handler))

    orchestrator.register_workflow(workflow)
    execution = await orchestrator.execute_workflow(workflow.workflow_id)

    event_types = [e["type"] for e in execution.events]
    assert "step.started" in event_types
    assert "step.completed" in event_types


# Workflow trigger tests


def test_register_trigger(orchestrator):
    """Test workflow trigger registration."""
    workflow = build_simple_workflow("trigger_test", [("step1", simple_handler)])
    orchestrator.register_workflow(workflow)

    trigger = WorkflowTrigger(
        trigger_type=TriggerType.SCHEDULED,
        workflow_id=workflow.workflow_id,
        schedule="0 0 * * *",  # Daily at midnight
    )

    orchestrator.register_trigger(trigger)
    assert trigger.trigger_id in orchestrator.triggers


def test_register_trigger_invalid_workflow(orchestrator):
    """Test that registering trigger for non-existent workflow fails."""
    trigger = WorkflowTrigger(
        trigger_type=TriggerType.SCHEDULED,
        workflow_id="nonexistent",
        schedule="0 0 * * *",
    )

    with pytest.raises(ValueError, match="not found"):
        orchestrator.register_trigger(trigger)


@pytest.mark.asyncio
async def test_trigger_metadata_in_execution(orchestrator):
    """Test that trigger data is captured in execution."""
    workflow = build_simple_workflow("trigger_meta", [("step1", simple_handler)])
    orchestrator.register_workflow(workflow)

    execution = await orchestrator.execute_workflow(
        workflow.workflow_id,
        trigger_type=TriggerType.EVENT,
        trigger_data={"event_id": "evt_123", "source": "webhook"},
    )

    assert execution.trigger_type == TriggerType.EVENT
    assert execution.trigger_data["event_id"] == "evt_123"
    assert execution.trigger_data["source"] == "webhook"


# Execution management tests


@pytest.mark.asyncio
async def test_get_execution(orchestrator):
    """Test retrieving execution by ID."""
    workflow = build_simple_workflow("get_test", [("step1", simple_handler)])
    orchestrator.register_workflow(workflow)

    execution = await orchestrator.execute_workflow(workflow.workflow_id)
    retrieved = orchestrator.get_execution(execution.execution_id)

    assert retrieved is not None
    assert retrieved.execution_id == execution.execution_id
    assert retrieved.status == WorkflowStatus.COMPLETED


@pytest.mark.asyncio
async def test_list_executions(orchestrator):
    """Test listing executions with filters."""
    workflow1 = build_simple_workflow("list_test1", [("step1", simple_handler)])
    workflow2 = build_simple_workflow("list_test2", [("step1", simple_handler)])

    orchestrator.register_workflow(workflow1)
    orchestrator.register_workflow(workflow2)

    exec1 = await orchestrator.execute_workflow(workflow1.workflow_id)
    exec2 = await orchestrator.execute_workflow(workflow2.workflow_id)

    # List all
    all_executions = orchestrator.list_executions()
    assert len(all_executions) >= 2

    # Filter by workflow
    workflow1_executions = orchestrator.list_executions(workflow_id=workflow1.workflow_id)
    assert len(workflow1_executions) >= 1
    assert all(e.workflow_id == workflow1.workflow_id for e in workflow1_executions)

    # Filter by status
    completed = orchestrator.list_executions(status=WorkflowStatus.COMPLETED)
    assert len(completed) >= 2


@pytest.mark.asyncio
async def test_cancel_execution(orchestrator):
    """Test cancelling a workflow execution."""

    async def long_running(context: dict) -> str:
        await asyncio.sleep(10)
        return "done"

    workflow = WorkflowDefinition(workflow_id="cancel_test", name="Cancel Test")
    workflow.add_step(WorkflowStep(step_id="long_step", handler=long_running))

    orchestrator.register_workflow(workflow)

    # Start execution in background
    execution_task = asyncio.create_task(
        orchestrator.execute_workflow(workflow.workflow_id),
    )

    # Give it a moment to start
    await asyncio.sleep(0.1)

    # Get the execution
    executions = orchestrator.list_executions(workflow_id=workflow.workflow_id)
    execution = executions[-1]  # Get the most recent

    # Cancel it
    await orchestrator.cancel_execution(execution.execution_id)

    # Verify it was cancelled
    assert execution.status == WorkflowStatus.CANCELLED
    assert execution.completed_at is not None

    # Clean up
    execution_task.cancel()
    try:
        await execution_task
    except asyncio.CancelledError:
        pass


# Context propagation tests


@pytest.mark.asyncio
async def test_context_propagation(orchestrator):
    """Test that context is propagated through steps."""

    def step1(context: dict) -> str:
        context["step1_data"] = "from step 1"
        return "step1 done"

    def step2(context: dict) -> str:
        # Should have access to step1's output
        assert "step1_data" in context
        assert "step_step1_output" in context
        return "step2 done"

    workflow = WorkflowDefinition(workflow_id="context_test", name="Context Test")
    workflow.add_step(WorkflowStep(step_id="step1", handler=step1))
    workflow.add_step(WorkflowStep(step_id="step2", handler=step2, dependencies=["step1"]))

    orchestrator.register_workflow(workflow)
    execution = await orchestrator.execute_workflow(
        workflow.workflow_id,
        context={"initial": "data"},
    )

    assert execution.status == WorkflowStatus.COMPLETED
    assert execution.context["initial"] == "data"
    assert execution.context["step1_data"] == "from step 1"


# Builder function tests


def test_build_simple_workflow():
    """Test simple workflow builder."""
    workflow = build_simple_workflow(
        "builder_test",
        [("step1", simple_handler), ("step2", simple_handler)],
    )

    assert workflow.name == "builder_test"
    assert len(workflow.steps) == 2
    assert workflow.steps["step2"].dependencies == ["step1"]

    is_valid, _ = workflow.validate()
    assert is_valid


def test_build_parallel_workflow():
    """Test parallel workflow builder."""
    workflow = build_parallel_workflow(
        "parallel_builder",
        [("p1", simple_handler), ("p2", simple_handler), ("p3", simple_handler)],
    )

    assert workflow.name == "parallel_builder"
    assert len(workflow.steps) == 3
    assert all(step.parallel for step in workflow.steps.values())
    assert all(len(step.dependencies) == 0 for step in workflow.steps.values())

    is_valid, _ = workflow.validate()
    assert is_valid


# Integration test: Complex workflow


@pytest.mark.asyncio
async def test_complex_workflow_integration(orchestrator):
    """Test a complex workflow with multiple features."""

    results = []

    async def init_step(context: dict) -> dict:
        results.append("init")
        return {"initialized": True}

    async def process_a(context: dict) -> str:
        await asyncio.sleep(0.01)
        results.append("process_a")
        return "A done"

    async def process_b(context: dict) -> str:
        await asyncio.sleep(0.01)
        results.append("process_b")
        return "B done"

    def aggregate(context: dict) -> str:
        results.append("aggregate")
        return "aggregated"

    def should_notify(context: dict) -> bool:
        return context.get("send_notification", True)

    def notify(context: dict) -> str:
        results.append("notify")
        return "notified"

    # Build complex workflow
    workflow = WorkflowDefinition(workflow_id="complex", name="Complex Workflow")

    # Init step
    workflow.add_step(WorkflowStep(step_id="init", handler=init_step))

    # Parallel processing
    workflow.add_step(
        WorkflowStep(step_id="process_a", handler=process_a, dependencies=["init"]),
    )
    workflow.add_step(
        WorkflowStep(step_id="process_b", handler=process_b, dependencies=["init"]),
    )

    # Aggregation (waits for both parallel steps)
    workflow.add_step(
        WorkflowStep(
            step_id="aggregate",
            handler=aggregate,
            dependencies=["process_a", "process_b"],
        ),
    )

    # Conditional notification
    workflow.add_step(
        WorkflowStep(
            step_id="notify",
            handler=notify,
            dependencies=["aggregate"],
            condition=should_notify,
        ),
    )

    orchestrator.register_workflow(workflow)
    execution = await orchestrator.execute_workflow(
        workflow.workflow_id,
        context={"send_notification": True},
    )

    assert execution.status == WorkflowStatus.COMPLETED
    assert len(execution.step_results) == 5

    # Verify all steps completed
    assert all(r.status in [StepStatus.COMPLETED] for r in execution.step_results.values())

    # Verify execution order
    assert results[0] == "init"
    assert "process_a" in results
    assert "process_b" in results
    assert results[-2] == "aggregate"  # Before notify
    assert results[-1] == "notify"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
