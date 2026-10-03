from core.orchestrator.task_state import (
    TaskManager,
    TaskStatus,
    TaskPriority,
)
from core.orchestrator.planner import (
    MasterPlanner,
    Plan,
    PlanRegistry,
    PlanStatus,
    PlanStep,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print(
        "SAHIBEX 6J-10 PLANNING INTELLIGENCE INTEGRATION TEST"
    )

    manager = TaskManager()
    planner = MasterPlanner(manager)
    registry = PlanRegistry()

    # 1. Create integrated plan

    result = planner.create_plan(
        title="Integrated planning test",
        description="6J-10 planning intelligence integration",
        steps=[
            PlanStep(
                title="Research",
                description="Perform research",
                priority=TaskPriority.NORMAL,
            ),
            PlanStep(
                title="Verify",
                description="Verify research",
                priority=TaskPriority.HIGH,
            ),
            PlanStep(
                title="Finalize",
                description="Finalize result",
                priority=TaskPriority.CRITICAL,
            ),
        ],
    )

    check(
        result.success,
        "master planner creates integrated plan",
    )

    goal = result.goal
    tasks = result.tasks

    check(
        len(tasks) == 3,
        "integrated plan contains expected tasks",
    )

    first_task = tasks[0]
    second_task = tasks[1]
    third_task = tasks[2]

    # 2. Dependency intelligence

    check(
        second_task.dependencies == [first_task.task_id],
        "second task depends on first task",
    )

    check(
        third_task.dependencies == [second_task.task_id],
        "third task depends on second task",
    )

    ready = planner.next_tasks(goal.goal_id)

    check(
        len(ready) == 1,
        "only first task is initially ready",
    )

    check(
        ready[0].task_id == first_task.task_id,
        "first task is initially schedulable",
    )

    # 3. Memory / knowledge integration

    first_task.add_memory_reference("memory-6j10")
    first_task.add_knowledge_reference("knowledge-6j10")

    check(
        first_task.memory_ids == ["memory-6j10"],
        "task preserves memory reference",
    )

    check(
        first_task.knowledge_ids == ["knowledge-6j10"],
        "task preserves knowledge reference",
    )

    # 4. Execute first task

    first_task.mark_ready()
    first_task.mark_running()

    check(
        first_task.status == TaskStatus.RUNNING,
        "first task enters running state",
    )

    first_task.complete(
        result={
            "stage": "research",
            "success": True,
        }
    )

    check(
        first_task.status == TaskStatus.COMPLETED,
        "first task completes successfully",
    )

    check(
        first_task.result["success"] is True,
        "first task result is preserved",
    )

    # 5. Dependency unlock

    ready = planner.next_tasks(goal.goal_id)

    check(
        len(ready) == 1,
        "second task becomes ready after dependency completion",
    )

    check(
        ready[0].task_id == second_task.task_id,
        "second task is unlocked by dependency completion",
    )

    # 6. Approval-aware execution

    second_task.mark_ready()
    second_task.mark_running()

    check(
        second_task.status == TaskStatus.RUNNING,
        "second task enters running state before approval",
    )

    second_task.mark_waiting_approval()

    check(
        second_task.status == TaskStatus.WAITING_APPROVAL,
        "second task can wait for approval",
    )

    # Current Task lifecycle requires READY before RUNNING.
    # Approval release is therefore represented by returning
    # the task to READY before resuming execution.

    second_task.status = TaskStatus.READY
    second_task.mark_running()

    check(
        second_task.status == TaskStatus.RUNNING,
        "approved task resumes running",
    )

    second_task.complete(
        result={
            "stage": "verification",
            "verified": True,
        }
    )

    check(
        second_task.status == TaskStatus.COMPLETED,
        "second task completes after approval",
    )

    # 7. Final dependency unlock

    ready = planner.next_tasks(goal.goal_id)

    check(
        len(ready) == 1,
        "third task becomes ready after second completion",
    )

    check(
        ready[0].task_id == third_task.task_id,
        "third task is unlocked correctly",
    )

    # 8. Final task execution

    third_task.mark_ready()
    third_task.mark_running()

    third_task.complete(
        result={
            "stage": "finalize",
            "success": True,
        }
    )

    check(
        third_task.status == TaskStatus.COMPLETED,
        "third task completes successfully",
    )

    # 9. Goal completion

    check(
        goal.is_complete(),
        "goal is complete after all tasks finish",
    )

    summary = planner.summary(goal.goal_id)

    check(
        summary["complete"] is True,
        "planner summary reports completed goal",
    )

    check(
        summary["completed"] == 3,
        "planner summary reports all completed tasks",
    )

    # 10. Plan object integration

    plan = Plan(
        title="6J-10 Integrated Plan",
        description="Planning intelligence integration",
        goal_id=goal.goal_id,
        task_ids=[
            first_task.task_id,
            second_task.task_id,
            third_task.task_id,
        ],
    )

    plan.add_memory_reference("memory-6j10-plan")
    plan.add_knowledge_reference("knowledge-6j10-plan")

    registry.register(plan)

    check(
        registry.get(plan.plan_id) is plan,
        "plan registry preserves integrated plan",
    )

    check(
        plan.goal_id == goal.goal_id,
        "plan preserves goal identity",
    )

    check(
        plan.task_ids == [
            first_task.task_id,
            second_task.task_id,
            third_task.task_id,
        ],
        "plan preserves task identities",
    )

    check(
        plan.memory_ids == ["memory-6j10-plan"],
        "plan preserves memory reference",
    )

    check(
        plan.knowledge_ids == ["knowledge-6j10-plan"],
        "plan preserves knowledge reference",
    )

    # 11. Plan execution lifecycle

    plan.mark_ready()

    check(
        plan.status == PlanStatus.READY,
        "integrated plan becomes ready",
    )

    plan.mark_running()

    check(
        plan.status == PlanStatus.RUNNING,
        "integrated plan enters running state",
    )

    plan.complete(
        result={
            "goal_id": goal.goal_id,
            "completed_tasks": 3,
        }
    )

    check(
        plan.status == PlanStatus.COMPLETED,
        "integrated plan completes successfully",
    )

    check(
        plan.result["completed_tasks"] == 3,
        "integrated plan preserves final result",
    )

    # 12. Final integrity checks

    check(
        first_task.memory_ids == ["memory-6j10"],
        "task memory reference survives complete workflow",
    )

    check(
        first_task.knowledge_ids == ["knowledge-6j10"],
        "task knowledge reference survives complete workflow",
    )

    check(
        plan.memory_ids == ["memory-6j10-plan"],
        "plan memory reference survives complete workflow",
    )

    check(
        plan.knowledge_ids == ["knowledge-6j10-plan"],
        "plan knowledge reference survives complete workflow",
    )

    check(
        registry.count() == 1,
        "plan registry contains integrated plan",
    )

    print(
        "SAHIBEX 6J-10 PLANNING INTELLIGENCE INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
