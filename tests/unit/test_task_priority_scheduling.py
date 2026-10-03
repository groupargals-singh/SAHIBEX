from core.orchestrator.task_state import (
    TaskManager,
    TaskPriority,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print("SAHIBEX 6J-5 TASK PRIORITY & SCHEDULING TEST")

    manager = TaskManager()

    goal = manager.create_goal(
        title="Priority Scheduling Goal",
        description="Testing task priority and deterministic scheduling.",
    )

    # ---------------------------------------------------------
    # Create tasks with all supported priorities
    # ---------------------------------------------------------

    low = manager.create_task(
        goal_id=goal.goal_id,
        title="Low Priority Task",
        priority=TaskPriority.LOW,
    )

    normal = manager.create_task(
        goal_id=goal.goal_id,
        title="Normal Priority Task",
        priority=TaskPriority.NORMAL,
    )

    high = manager.create_task(
        goal_id=goal.goal_id,
        title="High Priority Task",
        priority=TaskPriority.HIGH,
    )

    critical = manager.create_task(
        goal_id=goal.goal_id,
        title="Critical Priority Task",
        priority=TaskPriority.CRITICAL,
    )

    # ---------------------------------------------------------
    # Priority identity
    # ---------------------------------------------------------

    check(
        low.priority == TaskPriority.LOW,
        "low priority is preserved",
    )

    check(
        normal.priority == TaskPriority.NORMAL,
        "normal priority is preserved",
    )

    check(
        high.priority == TaskPriority.HIGH,
        "high priority is preserved",
    )

    check(
        critical.priority == TaskPriority.CRITICAL,
        "critical priority is preserved",
    )

    # ---------------------------------------------------------
    # Ready task collection
    # ---------------------------------------------------------

    ready = manager.ready_tasks(goal.goal_id)

    ready_ids = {
        task.task_id
        for task in ready
    }

    check(
        low.task_id in ready_ids,
        "low priority task is ready",
    )

    check(
        normal.task_id in ready_ids,
        "normal priority task is ready",
    )

    check(
        high.task_id in ready_ids,
        "high priority task is ready",
    )

    check(
        critical.task_id in ready_ids,
        "critical priority task is ready",
    )

    # ---------------------------------------------------------
    # Deterministic ordering check
    # ---------------------------------------------------------

    ready_priorities = [
        task.priority
        for task in ready
    ]

    priority_rank = {
        TaskPriority.CRITICAL: 0,
        TaskPriority.HIGH: 1,
        TaskPriority.NORMAL: 2,
        TaskPriority.LOW: 3,
    }

    expected_order = sorted(
        ready_priorities,
        key=lambda priority: priority_rank[priority],
    )

    check(
        ready_priorities == expected_order,
        "ready tasks are ordered by priority",
    )

    # ---------------------------------------------------------
    # Highest priority is selected first
    # ---------------------------------------------------------

    check(
        ready[0].priority == TaskPriority.CRITICAL,
        "critical priority is scheduled first",
    )

    # ---------------------------------------------------------
    # Dependency-aware priority scheduling
    # ---------------------------------------------------------

    dependency = manager.create_task(
        goal_id=goal.goal_id,
        title="High Priority Dependency",
        priority=TaskPriority.HIGH,
    )

    blocked_critical = manager.create_task(
        goal_id=goal.goal_id,
        title="Blocked Critical Task",
        priority=TaskPriority.CRITICAL,
        dependencies=[dependency.task_id],
    )

    ready_with_blocked_critical = manager.ready_tasks(
        goal.goal_id,
    )

    ready_ids = {
        task.task_id
        for task in ready_with_blocked_critical
    }

    check(
        blocked_critical.task_id not in ready_ids,
        "blocked critical task is not scheduled before dependency",
    )

    check(
        dependency.task_id in ready_ids,
        "ready dependency remains schedulable",
    )

    # ---------------------------------------------------------
    # Complete dependency
    # ---------------------------------------------------------

    dependency.mark_ready()
    dependency.mark_running()
    dependency.complete(
        result="dependency completed",
    )

    ready_after_dependency = manager.ready_tasks(
        goal.goal_id,
    )

    ready_ids = {
        task.task_id
        for task in ready_after_dependency
    }

    check(
        blocked_critical.task_id in ready_ids,
        "critical task becomes schedulable after dependency completion",
    )

    # ---------------------------------------------------------
    # Critical task should now outrank lower priorities
    # ---------------------------------------------------------

    critical_candidates = [
        task
        for task in ready_after_dependency
        if task.task_id != dependency.task_id
    ]

    critical_rank = {
        TaskPriority.CRITICAL: 0,
        TaskPriority.HIGH: 1,
        TaskPriority.NORMAL: 2,
        TaskPriority.LOW: 3,
    }

    ordered_candidates = sorted(
        critical_candidates,
        key=lambda task: critical_rank[task.priority],
    )

    check(
        ordered_candidates[0].priority == TaskPriority.CRITICAL,
        "critical ready task outranks lower priority ready tasks",
    )

    print("SAHIBEX 6J-5 TASK PRIORITY & SCHEDULING TEST: PASS")


if __name__ == "__main__":
    main()
