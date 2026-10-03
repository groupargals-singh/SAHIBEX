from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.orchestrator.task_state import (
    Task,
    TaskPriority,
    TaskStatus,
)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX 6J-1 TASK OBJECT CONTRACT TEST")

    task = Task(
        title="Test SAHIBEX task",
        description="Validate the task contract.",
    )

    # Identity
    check(
        isinstance(task.task_id, str)
        and bool(task.task_id.strip()),
        "task ID exists",
    )

    # Required work definition
    check(
        task.title == "Test SAHIBEX task",
        "task title preserved",
    )

    check(
        task.description == "Validate the task contract.",
        "task description preserved",
    )

    # Default state
    check(
        task.status == TaskStatus.PENDING,
        "default task status",
    )

    check(
        task.priority == TaskPriority.NORMAL,
        "default task priority",
    )

    # Optional task relationships
    check(
        task.parent_task_id is None,
        "default parent task identity",
    )

    check(
        task.dependencies == [],
        "default dependency list",
    )

    # Permission / approval state
    check(
        task.requires_approval is False,
        "default approval requirement",
    )

    # Execution state
    check(
        task.result is None,
        "default result state",
    )

    check(
        task.error is None,
        "default error state",
    )

    # Metadata
    check(
        isinstance(task.metadata, dict),
        "metadata contract",
    )

    check(
        task.metadata == {},
        "default metadata",
    )

    # Timestamp
    check(
        isinstance(task.created_at, str)
        and bool(task.created_at.strip()),
        "created timestamp exists",
    )

    check(
        task.started_at is None,
        "default started timestamp",
    )

    check(
        task.completed_at is None,
        "default completed timestamp",
    )

    # Lifecycle: pending -> ready
    task.mark_ready()

    check(
        task.status == TaskStatus.READY,
        "pending to ready transition",
    )

    # Lifecycle: ready -> running
    task.mark_running()

    check(
        task.status == TaskStatus.RUNNING,
        "ready to running transition",
    )

    check(
        task.started_at is not None,
        "running timestamp created",
    )

    # Lifecycle: running -> completed
    task.complete(
        "Task completed successfully."
    )

    check(
        task.status == TaskStatus.COMPLETED,
        "running to completed transition",
    )

    check(
        task.result == "Task completed successfully.",
        "task result preserved",
    )

    check(
        task.completed_at is not None,
        "completed timestamp created",
    )

    # Independent task contract
    failed_task = Task(
        title="Failure test",
    )

    failed_task.fail(
        "Expected test failure."
    )

    check(
        failed_task.status == TaskStatus.FAILED,
        "task failure state",
    )

    check(
        failed_task.error == "Expected test failure.",
        "task failure reason preserved",
    )

    cancelled_task = Task(
        title="Cancellation test",
    )

    cancelled_task.cancel(
        "Cancelled by test."
    )

    check(
        cancelled_task.status == TaskStatus.CANCELLED,
        "task cancellation state",
    )

    check(
        cancelled_task.error == "Cancelled by test.",
        "task cancellation reason preserved",
    )

    approval_task = Task(
        title="Protected task",
        requires_approval=True,
        priority=TaskPriority.CRITICAL,
    )

    check(
        approval_task.requires_approval is True,
        "protected task approval requirement",
    )

    check(
        approval_task.priority == TaskPriority.CRITICAL,
        "critical task priority",
    )

    approval_task.mark_waiting_approval()

    check(
        approval_task.status == TaskStatus.WAITING_APPROVAL,
        "waiting approval state",
    )

    blocked_task = Task(
        title="Blocked task",
    )

    blocked_task.mark_blocked(
        "Dependency is not complete."
    )

    check(
        blocked_task.status == TaskStatus.BLOCKED,
        "blocked task state",
    )

    check(
        blocked_task.error == "Dependency is not complete.",
        "blocked task reason preserved",
    )

    # Dependency contract
    dependency_task = Task(
        title="Dependent task",
        dependencies=["task-001", "task-002"],
        parent_task_id="parent-001",
    )

    check(
        dependency_task.dependencies
        == ["task-001", "task-002"],
        "task dependencies preserved",
    )

    check(
        dependency_task.parent_task_id == "parent-001",
        "parent task identity preserved",
    )

    print(
        "SAHIBEX 6J-1 TASK OBJECT CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
