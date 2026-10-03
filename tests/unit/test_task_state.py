from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.orchestrator.task_state import (
    TaskManager,
    TaskPriority,
    TaskStatus,
)


def main() -> None:
    print("=" * 60)
    print("SAHIBEX TASK STATE TEST")
    print("=" * 60)

    manager = TaskManager()

    goal = manager.create_goal(
        "Build SAHIBEX website",
        "Create and verify the website.",
    )

    assert goal.title == "Build SAHIBEX website"
    print("[PASS] goal creation")

    task_1 = manager.create_task(
        goal.goal_id,
        "Create project structure",
        priority=TaskPriority.HIGH,
    )

    task_2 = manager.create_task(
        goal.goal_id,
        "Generate website code",
        dependencies=[task_1.task_id],
    )

    task_3 = manager.create_task(
        goal.goal_id,
        "Deploy website",
        dependencies=[task_2.task_id],
        requires_approval=True,
    )

    assert task_1.status == TaskStatus.PENDING
    print("[PASS] task creation")

    ready = manager.ready_tasks(goal.goal_id)

    assert len(ready) == 1
    assert ready[0].task_id == task_1.task_id

    print("[PASS] dependency-aware ready task")

    task_1.mark_ready()

    assert task_1.status == TaskStatus.READY

    task_1.mark_running()

    assert task_1.status == TaskStatus.RUNNING

    task_1.complete(
        "Project structure created."
    )

    assert task_1.status == TaskStatus.COMPLETED

    print("[PASS] task lifecycle")

    ready = manager.ready_tasks(goal.goal_id)

    assert len(ready) == 1
    assert ready[0].task_id == task_2.task_id

    print("[PASS] dependency unlock")

    task_2.mark_ready()
    task_2.mark_running()
    task_2.complete(
        "Website code generated."
    )

    ready = manager.ready_tasks(goal.goal_id)

    assert len(ready) == 1
    assert ready[0].task_id == task_3.task_id

    print("[PASS] multi-level dependency chain")

    assert task_3.requires_approval is True
    print("[PASS] protected task marked for approval")

    summary = manager.goal_summary(
        goal.goal_id
    )

    assert summary["task_count"] == 3
    assert summary["completed"] == 2
    assert summary["failed"] == 0
    assert summary["complete"] is False

    print("[PASS] goal summary")

    manager.cancel_goal(
        goal.goal_id,
        "Test cancellation.",
    )

    assert task_3.status == TaskStatus.CANCELLED

    print("[PASS] goal cancellation")

    print("=" * 60)
    print("SAHIBEX TASK STATE TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
