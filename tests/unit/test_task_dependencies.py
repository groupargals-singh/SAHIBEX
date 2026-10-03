from core.orchestrator.task_state import (
    TaskManager,
    TaskStatus,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print("SAHIBEX 6J-4 TASK DEPENDENCIES TEST")

    manager = TaskManager()

    goal = manager.create_goal(
        title="Dependency Planning Goal",
        description="Testing task dependency resolution.",
    )

    # ---------------------------------------------------------
    # Independent task
    # ---------------------------------------------------------

    independent = manager.create_task(
        goal_id=goal.goal_id,
        title="Independent Task",
    )

    # ---------------------------------------------------------
    # Dependency task
    # ---------------------------------------------------------

    dependency_task = manager.create_task(
        goal_id=goal.goal_id,
        title="Dependency Task",
    )

    dependent_task = manager.create_task(
        goal_id=goal.goal_id,
        title="Dependent Task",
        dependencies=[dependency_task.task_id],
    )

    check(
        independent.status == TaskStatus.PENDING,
        "independent task starts pending",
    )

    check(
        dependency_task.status == TaskStatus.PENDING,
        "dependency task starts pending",
    )

    check(
        dependent_task.status == TaskStatus.PENDING,
        "dependent task starts pending",
    )

    check(
        dependent_task.dependencies == [dependency_task.task_id],
        "dependency identity is preserved",
    )

    # ---------------------------------------------------------
    # Initial readiness
    # ---------------------------------------------------------

    ready = manager.ready_tasks(goal.goal_id)

    ready_ids = {
        task.task_id
        for task in ready
    }

    check(
        independent.task_id in ready_ids,
        "independent task is ready",
    )

    check(
        dependency_task.task_id in ready_ids,
        "dependency task is ready",
    )

    check(
        dependent_task.task_id not in ready_ids,
        "dependent task is not ready before dependency completion",
    )

    # ---------------------------------------------------------
    # Complete dependency
    # ---------------------------------------------------------

    dependency_task.mark_ready()
    dependency_task.mark_running()
    dependency_task.complete(
        result="dependency completed",
    )

    check(
        dependency_task.status == TaskStatus.COMPLETED,
        "dependency task reaches completed state",
    )

    ready_after_completion = manager.ready_tasks(goal.goal_id)

    ready_after_completion_ids = {
        task.task_id
        for task in ready_after_completion
    }

    check(
        dependent_task.task_id in ready_after_completion_ids,
        "dependent task becomes ready after dependency completion",
    )

    # ---------------------------------------------------------
    # Multiple dependencies
    # ---------------------------------------------------------

    dependency_two = manager.create_task(
        goal_id=goal.goal_id,
        title="Second Dependency",
    )

    multi_dependent = manager.create_task(
        goal_id=goal.goal_id,
        title="Multi Dependency Task",
        dependencies=[
            dependency_task.task_id,
            dependency_two.task_id,
        ],
    )

    ready_with_second_dependency_pending = manager.ready_tasks(goal.goal_id)

    ready_ids = {
        task.task_id
        for task in ready_with_second_dependency_pending
    }

    check(
        multi_dependent.task_id not in ready_ids,
        "multi-dependent task waits for all dependencies",
    )

    dependency_two.mark_ready()
    dependency_two.mark_running()
    dependency_two.complete(
        result="second dependency completed",
    )

    check(
        dependency_two.status == TaskStatus.COMPLETED,
        "second dependency reaches completed state",
    )

    ready_after_all_dependencies = manager.ready_tasks(goal.goal_id)

    ready_ids = {
        task.task_id
        for task in ready_after_all_dependencies
    }

    check(
        multi_dependent.task_id in ready_ids,
        "multi-dependent task becomes ready after all dependencies complete",
    )

    # ---------------------------------------------------------
    # Failed dependency
    # ---------------------------------------------------------

    failed_dependency = manager.create_task(
        goal_id=goal.goal_id,
        title="Failed Dependency",
    )

    blocked_by_failure = manager.create_task(
        goal_id=goal.goal_id,
        title="Task Waiting On Failed Dependency",
        dependencies=[failed_dependency.task_id],
    )

    failed_dependency.mark_ready()
    failed_dependency.mark_running()
    failed_dependency.fail(
        "dependency failure",
    )

    check(
        failed_dependency.status == TaskStatus.FAILED,
        "failed dependency reaches failed state",
    )

    ready_after_failure = manager.ready_tasks(goal.goal_id)

    ready_ids = {
        task.task_id
        for task in ready_after_failure
    }

    check(
        blocked_by_failure.task_id not in ready_ids,
        "dependent task is not ready when dependency fails",
    )

    # ---------------------------------------------------------
    # Missing dependency
    # ---------------------------------------------------------

    missing_dependency_task = manager.create_task(
        goal_id=goal.goal_id,
        title="Missing Dependency Task",
        dependencies=["missing-task-identity"],
    )

    ready_with_missing_dependency = manager.ready_tasks(goal.goal_id)

    ready_ids = {
        task.task_id
        for task in ready_with_missing_dependency
    }

    check(
        missing_dependency_task.task_id not in ready_ids,
        "task with missing dependency is not ready",
    )

    # ---------------------------------------------------------
    # Dependency ordering
    # ---------------------------------------------------------

    chain_a = manager.create_task(
        goal_id=goal.goal_id,
        title="Chain A",
    )

    chain_b = manager.create_task(
        goal_id=goal.goal_id,
        title="Chain B",
        dependencies=[chain_a.task_id],
    )

    chain_c = manager.create_task(
        goal_id=goal.goal_id,
        title="Chain C",
        dependencies=[chain_b.task_id],
    )

    ready_chain_initial = manager.ready_tasks(goal.goal_id)

    ready_ids = {
        task.task_id
        for task in ready_chain_initial
    }

    check(
        chain_a.task_id in ready_ids,
        "dependency chain starts with first task",
    )

    check(
        chain_b.task_id not in ready_ids,
        "second chain task waits for first",
    )

    check(
        chain_c.task_id not in ready_ids,
        "third chain task waits for second",
    )

    chain_a.mark_ready()
    chain_a.mark_running()
    chain_a.complete(
        result="chain A completed",
    )

    ready_chain_after_a = manager.ready_tasks(goal.goal_id)

    ready_ids = {
        task.task_id
        for task in ready_chain_after_a
    }

    check(
        chain_b.task_id in ready_ids,
        "second chain task becomes ready after first completes",
    )

    check(
        chain_c.task_id not in ready_ids,
        "third chain task still waits for second",
    )

    chain_b.mark_ready()
    chain_b.mark_running()
    chain_b.complete(
        result="chain B completed",
    )

    ready_chain_after_b = manager.ready_tasks(goal.goal_id)

    ready_ids = {
        task.task_id
        for task in ready_chain_after_b
    }

    check(
        chain_c.task_id in ready_ids,
        "third chain task becomes ready after second completes",
    )

    print("SAHIBEX 6J-4 TASK DEPENDENCIES TEST: PASS")


if __name__ == "__main__":
    main()
