from core.orchestrator.task_state import (
    TaskManager,
    TaskPriority,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"[PASS] {message}")


def main() -> None:
    print("SAHIBEX 6J-2 TASK REGISTRY TEST")

    manager = TaskManager()

    # ---------------------------------------------------------
    # Goal registration
    # ---------------------------------------------------------
    goal = manager.create_goal(
        title="Registry Test Goal",
        description="Testing task registry behavior.",
    )

    check(
        goal.goal_id in manager.goals,
        "goal registered in manager",
    )

    check(
        manager.get_goal(goal.goal_id) is goal,
        "goal lookup returns registered goal",
    )

    # ---------------------------------------------------------
    # Task registration
    # ---------------------------------------------------------
    task = manager.create_task(
        goal_id=goal.goal_id,
        title="Registry Task",
        description="Task registry test task.",
    )

    check(
        task.task_id in manager.tasks,
        "task registered in manager",
    )

    check(
        manager.get_task(task.task_id) is task,
        "task lookup returns registered task",
    )

    check(
        goal.get_task(task.task_id) is task,
        "task associated with correct goal",
    )

    # ---------------------------------------------------------
    # Task identity
    # ---------------------------------------------------------
    second_task = manager.create_task(
        goal_id=goal.goal_id,
        title="Second Registry Task",
        description="Second task.",
        priority=TaskPriority.HIGH,
    )

    check(
        second_task.task_id != task.task_id,
        "registered tasks have unique identities",
    )

    check(
        second_task.task_id in manager.tasks,
        "second task registered",
    )

    check(
        goal.get_task(second_task.task_id) is second_task,
        "second task associated with correct goal",
    )

    # ---------------------------------------------------------
    # Registry enumeration
    # ---------------------------------------------------------
    check(
        len(manager.tasks) == 2,
        "task registry contains expected task count",
    )

    check(
        set(manager.tasks.keys())
        == {task.task_id, second_task.task_id},
        "task registry identities are preserved",
    )

    check(
        len(goal.tasks) == 2,
        "goal contains all registered tasks",
    )

    # ---------------------------------------------------------
    # Unknown lookup behavior
    # ---------------------------------------------------------
    unknown_task_id = "unknown-task-id"

    check(
        manager.get_task(unknown_task_id) is None,
        "unknown task lookup returns None",
    )

    check(
        manager.get_goal("unknown-goal-id") is None,
        "unknown goal lookup returns None",
    )

    # ---------------------------------------------------------
    # Registry isolation
    # ---------------------------------------------------------
    second_manager = TaskManager()

    second_goal = second_manager.create_goal(
        title="Isolated Goal",
    )

    second_manager_task = second_manager.create_task(
        goal_id=second_goal.goal_id,
        title="Isolated Task",
    )

    check(
        second_manager.get_task(second_manager_task.task_id)
        is second_manager_task,
        "second manager registers its own task",
    )

    check(
        manager.get_task(second_manager_task.task_id) is None,
        "task registry is isolated between managers",
    )

    check(
        second_manager.get_task(task.task_id) is None,
        "first manager task is isolated from second manager",
    )

    # ---------------------------------------------------------
    # Registry object identity
    # ---------------------------------------------------------
    check(
        manager.tasks[task.task_id] is task,
        "registry preserves task object identity",
    )

    check(
        manager.goals[goal.goal_id] is goal,
        "registry preserves goal object identity",
    )

    print("SAHIBEX 6J-2 TASK REGISTRY TEST: PASS")


if __name__ == "__main__":
    main()
