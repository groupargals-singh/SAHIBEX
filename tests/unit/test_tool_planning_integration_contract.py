from __future__ import annotations

from core.orchestrator.planner import (
    MasterPlanner,
    Plan,
    PlanStatus,
    PlanStep,
)
from core.orchestrator.task_state import (
    TaskManager,
    TaskPriority,
    TaskStatus,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # ---------------------------------------------------------
    # 1. Create a real planning goal.
    # ---------------------------------------------------------
    manager = TaskManager()

    goal = manager.create_goal(
        title="Safe tool execution",
        description="Execute tools only through the planned control path.",
    )

    check(
        manager.get_goal(goal.goal_id) is goal,
        "TaskManager must track the created goal.",
    )

    # ---------------------------------------------------------
    # 2. Create a real task through TaskManager.
    # ---------------------------------------------------------
    task = manager.create_task(
        goal_id=goal.goal_id,
        title="Read a project file",
        description="Use an approved read-only tool to inspect a file.",
        priority=TaskPriority.NORMAL,
    )

    check(
        task.status == TaskStatus.PENDING,
        "New task must start in PENDING state.",
    )

    check(
        manager.get_task(task.task_id) is task,
        "TaskManager must track the created task.",
    )

    check(
        goal.get_task(task.task_id) is task,
        "Goal must track the created task.",
    )

    # ---------------------------------------------------------
    # 3. MasterPlanner must integrate with TaskManager.
    # ---------------------------------------------------------
    planner = MasterPlanner(manager)

    check(
        planner is not None,
        "MasterPlanner must be constructible with TaskManager.",
    )

    # ---------------------------------------------------------
    # 4. PlanStep must follow the real production contract.
    # ---------------------------------------------------------
    step = PlanStep(
        title="Read project file",
        description="Invoke an approved read-only tool.",
        priority=TaskPriority.NORMAL,
        requires_approval=False,
    )

    check(
        step.title == "Read project file",
        "PlanStep title must be preserved.",
    )

    check(
        step.description == "Invoke an approved read-only tool.",
        "PlanStep description must be preserved.",
    )

    check(
        step.priority == TaskPriority.NORMAL,
        "PlanStep priority must be preserved.",
    )

    check(
        step.requires_approval is False,
        "Read-only step must not require approval by default.",
    )

    # ---------------------------------------------------------
    # 5. Plan must use the real production structure.
    # ---------------------------------------------------------
    plan = Plan(
        title="Tool integration plan",
        description="Inspect a project file safely.",
        goal_id=goal.goal_id,
        task_ids=[task.task_id],
        metadata={
            "operation": "tool_invocation",
            "tool_query": "read file",
        },
    )

    check(
        plan.title == "Tool integration plan",
        "Plan title must be preserved.",
    )

    check(
        plan.goal_id == goal.goal_id,
        "Plan must reference the goal.",
    )

    check(
        task.task_id in plan.task_ids,
        "Plan must reference the task.",
    )

    check(
        plan.status == PlanStatus.PENDING,
        "New plan must start in PENDING state.",
    )

    check(
        plan.metadata["operation"] == "tool_invocation",
        "Plan must preserve tool operation metadata.",
    )

    check(
        plan.metadata["tool_query"] == "read file",
        "Plan must preserve tool discovery query.",
    )

    # ---------------------------------------------------------
    # 6. Planning lifecycle must work.
    # ---------------------------------------------------------
    plan.mark_ready()

    check(
        plan.status == PlanStatus.READY,
        "Plan must transition PENDING -> READY.",
    )

    plan.mark_running()

    check(
        plan.status == PlanStatus.RUNNING,
        "Plan must transition READY -> RUNNING.",
    )

    # ---------------------------------------------------------
    # 7. Planning layer must not directly execute tools.
    # ---------------------------------------------------------
    check(
        not hasattr(planner, "execute_tool"),
        "MasterPlanner must not directly execute tools.",
    )

    check(
        not hasattr(planner, "invoke_tool"),
        "MasterPlanner must not directly invoke tools.",
    )

    # ---------------------------------------------------------
    # 8. Approval-capable PlanStep must be representable.
    # ---------------------------------------------------------
    protected_step = PlanStep(
        title="Write project file",
        description="Perform a protected write operation.",
        priority=TaskPriority.HIGH,
        requires_approval=True,
    )

    check(
        protected_step.requires_approval is True,
        "Protected step must preserve approval requirement.",
    )

    check(
        protected_step.priority == TaskPriority.HIGH,
        "Protected step priority must be preserved.",
    )

    print("SAHIBEX 6K-9 TOOL-PLANNING INTEGRATION CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
