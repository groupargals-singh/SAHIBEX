from core.brain.child_worker_coordinator import (
    ChildWorkerCoordinator,
    WorkerType,
    WorkerTaskDecision,
)


def main() -> None:
    coordinator = ChildWorkerCoordinator()

    result = coordinator.assign_task(
        task_id="task-test-001",
        worker_id="army-test-001",
        worker_type=WorkerType.ARMY,
        child_brain_id="child-brain-test",
        description="research task",
        authority_approved=False,
    )

    assert result.allowed is False
    assert result.decision == WorkerTaskDecision.REQUIRE_AUTHORITY

    result = coordinator.assign_task(
        task_id="task-test-001",
        worker_id="army-test-001",
        worker_type=WorkerType.ARMY,
        child_brain_id="child-brain-test",
        description="research task",
        authority_approved=True,
    )

    assert result.allowed is True
    assert result.task is not None
    assert result.task.worker_type == WorkerType.ARMY

    result = coordinator.assign_task(
        task_id="task-test-001",
        worker_id="army-test-001",
        worker_type=WorkerType.ARMY,
        child_brain_id="child-brain-test",
        description="duplicate task",
        authority_approved=True,
    )

    assert result.allowed is False

    result = coordinator.assign_task(
        task_id="task-test-002",
        worker_id="labor-test-001",
        worker_type=WorkerType.LABOR,
        child_brain_id="child-brain-test",
        description="file operation",
        authority_approved=True,
    )

    assert result.allowed is True
    assert result.task is not None
    assert result.task.worker_type == WorkerType.LABOR

    tasks = coordinator.list_child_tasks(
        "child-brain-test"
    )

    assert len(tasks) == 2

    assert coordinator.get_task("task-test-001") is not None
    assert coordinator.get_task("unknown-task") is None

    assert not coordinator.can_worker_assign_own_task()
    assert not coordinator.can_worker_grant_authority()
    assert not coordinator.can_worker_override_child()
    assert not coordinator.can_worker_override_mother()
    assert not coordinator.can_worker_self_promote()
    assert not coordinator.can_worker_execute_without_authority()
    assert not coordinator.can_worker_modify_constitution()
    assert not coordinator.can_worker_modify_soul()

    print("SAHIBEX CHILD WORKER COORDINATOR TEST: PASS")


if __name__ == "__main__":
    main()
