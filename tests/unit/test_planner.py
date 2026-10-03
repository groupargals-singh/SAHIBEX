from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.orchestrator.planner import (
    MasterPlanner,
    PlanStep,
)
from core.orchestrator.task_state import (
    TaskPriority,
    TaskStatus,
)


def main() -> None:
    print("=" * 60)
    print("SAHIBEX MASTER PLANNER TEST")
    print("=" * 60)

    planner = MasterPlanner()

    plan = planner.create_plan(
        title="Build SAHIBEX website",
        description=(
            "Create, test and deploy a website."
        ),
        steps=[
            PlanStep(
                title="Understand requirements",
                description=(
                    "Analyze website requirements."
                ),
                priority=TaskPriority.HIGH,
            ),
            PlanStep(
                title="Create website code",
                description=(
                    "Generate the required code."
                ),
                priority=TaskPriority.HIGH,
            ),
            PlanStep(
                title="Run verification tests",
                description=(
                    "Verify generated website."
                ),
                priority=TaskPriority.HIGH,
            ),
            PlanStep(
                title="Deploy website",
                description=(
                    "Deploy the verified website."
                ),
                priority=TaskPriority.CRITICAL,
                requires_approval=True,
            ),
        ],
    )

    assert plan.success is True
    print("[PASS] plan creation")

    assert len(plan.tasks) == 4
    print("[PASS] task decomposition")

    task_1 = plan.tasks[0]
    task_2 = plan.tasks[1]
    task_3 = plan.tasks[2]
    task_4 = plan.tasks[3]

    assert task_1.dependencies == []
    print("[PASS] root task has no dependency")

    assert task_2.dependencies == [
        task_1.task_id
    ]

    assert task_3.dependencies == [
        task_2.task_id
    ]

    assert task_4.dependencies == [
        task_3.task_id
    ]

    print("[PASS] sequential dependencies")

    assert (
        task_4.requires_approval is True
    )

    assert (
        task_4.priority
        == TaskPriority.CRITICAL
    )

    print(
        "[PASS] protected critical task "
        "requires approval"
    )

    ready = planner.next_tasks(
        plan.goal.goal_id
    )

    assert len(ready) == 1
    assert ready[0].task_id == task_1.task_id

    print("[PASS] planner returns first ready task")

    task_1.mark_ready()
    task_1.mark_running()
    task_1.complete(
        "Requirements analyzed."
    )

    ready = planner.next_tasks(
        plan.goal.goal_id
    )

    assert len(ready) == 1
    assert ready[0].task_id == task_2.task_id

    print("[PASS] planner unlocks dependent task")

    summary = planner.summary(
        plan.goal.goal_id
    )

    assert summary["task_count"] == 4
    assert summary["completed"] == 1
    assert summary["failed"] == 0
    assert summary["complete"] is False

    print("[PASS] planner summary")

    parallel_plan = planner.create_parallel_plan(
        title="Research AI technologies",
        description="Independent research tasks.",
        steps=[
            PlanStep(
                title="Research models",
                description="Study AI models.",
            ),
            PlanStep(
                title="Research tools",
                description="Study AI tools.",
            ),
            PlanStep(
                title="Research security",
                description="Study AI security.",
            ),
        ],
    )

    assert parallel_plan.success is True
    assert len(parallel_plan.tasks) == 3

    for task in parallel_plan.tasks:
        assert task.dependencies == []

    print("[PASS] parallel planning")

    print("=" * 60)
    print("SAHIBEX MASTER PLANNER TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
