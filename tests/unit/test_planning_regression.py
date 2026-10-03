from core.orchestrator.task_state import (
    Task,
    TaskManager,
    TaskPriority,
    TaskStatus,
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
    print("SAHIBEX 6J-11 FULL PLANNING REGRESSION TEST")

    # ==================================================
    # 6J-1 TASK OBJECT CONTRACT
    # ==================================================

    task = Task(
        title="Regression task",
        description="Planning regression task",
    )

    check(
        task.task_id,
        "task has identity",
    )

    check(
        task.title == "Regression task",
        "task title is preserved",
    )

    check(
        task.description == "Planning regression task",
        "task description is preserved",
    )

    check(
        task.status == TaskStatus.PENDING,
        "task starts pending",
    )

    check(
        task.priority == TaskPriority.NORMAL,
        "task starts with normal priority",
    )

    # ==================================================
    # 6J-2 TASK REGISTRY
    # ==================================================

    manager = TaskManager()

    goal = manager.create_goal(
        title="Planning regression goal",
        description="Full 6J regression",
    )

    registered_task = manager.create_task(
        goal_id=goal.goal_id,
        title="Registered task",
        priority=TaskPriority.HIGH,
    )

    check(
        manager.get_task(registered_task.task_id)
        is registered_task,
        "task registry preserves task identity",
    )

    check(
        manager.get_goal(goal.goal_id) is goal,
        "goal registry preserves goal identity",
    )

    check(
        len(goal.tasks) == 1,
        "goal contains registered task",
    )

    # ==================================================
    # 6J-3 TASK PERSISTENCE CONTRACT
    # ==================================================

    check(
        registered_task.task_id in manager.tasks,
        "task remains registered in manager",
    )

    check(
        goal.goal_id in manager.goals,
        "goal remains registered in manager",
    )

    # ==================================================
    # 6J-4 DEPENDENCIES
    # ==================================================

    dependency_task = manager.create_task(
        goal_id=goal.goal_id,
        title="Dependency task",
        priority=TaskPriority.NORMAL,
    )

    dependent_task = manager.create_task(
        goal_id=goal.goal_id,
        title="Dependent task",
        priority=TaskPriority.NORMAL,
        dependencies=[dependency_task.task_id],
    )

    ready = manager.ready_tasks(goal.goal_id)

    check(
        dependency_task in ready,
        "dependency task is initially ready",
    )

    check(
        dependent_task not in ready,
        "dependent task waits for dependency",
    )

    dependency_task.mark_ready()
    dependency_task.mark_running()
    dependency_task.complete(
        result={"dependency": True}
    )

    ready = manager.ready_tasks(goal.goal_id)

    check(
        dependent_task in ready,
        "dependent task becomes ready after dependency completion",
    )

    # ==================================================
    # 6J-5 PRIORITY & SCHEDULING
    # ==================================================

    low_task = manager.create_task(
        goal_id=goal.goal_id,
        title="Low priority",
        priority=TaskPriority.LOW,
    )

    critical_task = manager.create_task(
        goal_id=goal.goal_id,
        title="Critical priority",
        priority=TaskPriority.CRITICAL,
    )

    high_task = manager.create_task(
        goal_id=goal.goal_id,
        title="High priority",
        priority=TaskPriority.HIGH,
    )

    ready = manager.ready_tasks(goal.goal_id)

    ready_ids = [item.task_id for item in ready]

    check(
        critical_task.task_id in ready_ids,
        "critical task is schedulable",
    )

    check(
        high_task.task_id in ready_ids,
        "high task is schedulable",
    )

    check(
        low_task.task_id in ready_ids,
        "low task is schedulable",
    )

    critical_index = ready_ids.index(
        critical_task.task_id
    )
    high_index = ready_ids.index(
        high_task.task_id
    )
    low_index = ready_ids.index(
        low_task.task_id
    )

    check(
        critical_index < high_index < low_index,
        "ready tasks are ordered by priority",
    )

    # ==================================================
    # 6J-6 PLAN OBJECT & REGISTRY
    # ==================================================

    plan = Plan(
        title="Regression plan",
        description="Full planning regression",
        goal_id=goal.goal_id,
        task_ids=[
            registered_task.task_id,
            dependency_task.task_id,
            dependent_task.task_id,
        ],
    )

    registry = PlanRegistry()

    registry.register(plan)

    check(
        registry.get(plan.plan_id) is plan,
        "plan registry preserves plan identity",
    )

    check(
        registry.count() == 1,
        "plan registry contains one plan",
    )

    # ==================================================
    # 6J-7 PLAN EXECUTION STATE
    # ==================================================

    plan.mark_ready()

    check(
        plan.status == PlanStatus.READY,
        "plan becomes ready",
    )

    plan.mark_running()

    check(
        plan.status == PlanStatus.RUNNING,
        "plan becomes running",
    )

    check(
        plan.started_at is not None,
        "plan records start timestamp",
    )

    plan.mark_waiting_approval()

    check(
        plan.status == PlanStatus.WAITING_APPROVAL,
        "plan can wait for approval",
    )

    plan.mark_running()

    check(
        plan.status == PlanStatus.RUNNING,
        "plan resumes after approval",
    )

    plan.mark_blocked(
        "Regression blocking test"
    )

    check(
        plan.status == PlanStatus.BLOCKED,
        "plan can become blocked",
    )

    check(
        plan.error == "Regression blocking test",
        "plan preserves blocking reason",
    )

    plan.mark_running()

    check(
        plan.status == PlanStatus.RUNNING,
        "blocked plan can resume",
    )

    # ==================================================
    # 6J-8 FAILURE / RETRY / RECOVERY
    # ==================================================

    recovery_plan = Plan(
        title="Recovery plan",
        description="Retry regression",
    )

    recovery_plan.mark_ready()
    recovery_plan.mark_running()
    recovery_plan.fail("Regression failure")

    check(
        recovery_plan.status == PlanStatus.FAILED,
        "failed plan enters failed state",
    )

    check(
        recovery_plan.error == "Regression failure",
        "plan preserves failure reason",
    )

    recovery_plan.retry()

    check(
        recovery_plan.status == PlanStatus.READY,
        "failed plan recovers to ready",
    )

    check(
        recovery_plan.retry_count == 1,
        "plan retry count increments",
    )

    recovery_task = Task(
        title="Recovery task",
    )

    recovery_task.mark_ready()
    recovery_task.mark_running()
    recovery_task.fail("Task failure")

    check(
        recovery_task.status == TaskStatus.FAILED,
        "failed task enters failed state",
    )

    recovery_task.retry()

    check(
        recovery_task.status == TaskStatus.READY,
        "failed task recovers to ready",
    )

    check(
        recovery_task.retry_count == 1,
        "task retry count increments",
    )

    # ==================================================
    # 6J-9 MEMORY / KNOWLEDGE INTEGRATION
    # ==================================================

    registered_task.add_memory_reference(
        "memory-regression"
    )

    registered_task.add_knowledge_reference(
        "knowledge-regression"
    )

    check(
        registered_task.memory_ids
        == ["memory-regression"],
        "task preserves memory reference",
    )

    check(
        registered_task.knowledge_ids
        == ["knowledge-regression"],
        "task preserves knowledge reference",
    )

    plan.add_memory_reference(
        "plan-memory-regression"
    )

    plan.add_knowledge_reference(
        "plan-knowledge-regression"
    )

    check(
        plan.memory_ids
        == ["plan-memory-regression"],
        "plan preserves memory reference",
    )

    check(
        plan.knowledge_ids
        == ["plan-knowledge-regression"],
        "plan preserves knowledge reference",
    )

    # ==================================================
    # 6J-10 PLANNING INTELLIGENCE INTEGRATION
    # ==================================================

    integration_manager = TaskManager()

    integration_planner = MasterPlanner(
        integration_manager
    )

    integration_result = (
        integration_planner.create_plan(
            title="Integrated regression plan",
            description="6J-10 integration regression",
            steps=[
                PlanStep(
                    title="Step 1",
                    description="First step",
                    priority=TaskPriority.NORMAL,
                ),
                PlanStep(
                    title="Step 2",
                    description="Second step",
                    priority=TaskPriority.HIGH,
                ),
                PlanStep(
                    title="Step 3",
                    description="Third step",
                    priority=TaskPriority.CRITICAL,
                ),
            ],
        )
    )

    check(
        integration_result.success,
        "master planner creates integrated regression plan",
    )

    integration_goal = integration_result.goal
    integration_tasks = integration_result.tasks

    check(
        len(integration_tasks) == 3,
        "integrated regression plan contains three tasks",
    )

    first = integration_tasks[0]
    second = integration_tasks[1]
    third = integration_tasks[2]

    check(
        second.dependencies == [first.task_id],
        "integration dependency chain is preserved",
    )

    check(
        third.dependencies == [second.task_id],
        "integration dependency chain reaches final task",
    )

    first.mark_ready()
    first.mark_running()
    first.complete(
        result={"stage": 1}
    )

    ready = integration_planner.next_tasks(
        integration_goal.goal_id
    )

    check(
        len(ready) == 1
        and ready[0].task_id == second.task_id,
        "integration scheduler unlocks second task",
    )

    second.mark_ready()
    second.mark_running()
    second.complete(
        result={"stage": 2}
    )

    ready = integration_planner.next_tasks(
        integration_goal.goal_id
    )

    check(
        len(ready) == 1
        and ready[0].task_id == third.task_id,
        "integration scheduler unlocks final task",
    )

    third.mark_ready()
    third.mark_running()
    third.complete(
        result={"stage": 3}
    )

    check(
        integration_goal.is_complete(),
        "integrated goal reaches completion",
    )

    integration_summary = (
        integration_planner.summary(
            integration_goal.goal_id
        )
    )

    check(
        integration_summary["complete"] is True,
        "integrated planner reports completed goal",
    )

    check(
        integration_summary["completed"] == 3,
        "integrated planner reports three completed tasks",
    )

    # ==================================================
    # FINAL REGRESSION INTEGRITY
    # ==================================================

    check(
        plan.goal_id == goal.goal_id,
        "final plan-to-goal identity remains intact",
    )

    check(
        len(plan.task_ids) == 3,
        "final plan retains task identities",
    )

    check(
        registry.get(plan.plan_id) is plan,
        "final registry lookup remains stable",
    )

    plan.complete(
        result={
            "regression": True,
            "status": "complete",
        }
    )

    check(
        plan.status == PlanStatus.COMPLETED,
        "final regression plan completes",
    )

    check(
        plan.result["regression"] is True,
        "final regression result is preserved",
    )

    print(
        "SAHIBEX 6J-11 FULL PLANNING REGRESSION TEST: PASS"
    )


if __name__ == "__main__":
    main()
