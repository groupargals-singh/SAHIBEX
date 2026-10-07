from core.brain.child_army_manager import (
    ArmyBrainState,
    ChildArmyManager,
)
from core.brain.child_army_runtime import (
    ArmyAction,
    ArmyDecision,
    ChildArmyRuntime,
)
from core.brain.child_labor_manager import (
    ChildLaborManager,
    LaborBrainState,
)
from core.brain.child_labor_runtime import (
    ChildLaborRuntime,
    LaborAction,
    LaborDecision,
)
from core.brain.child_worker_coordinator import (
    ChildWorkerCoordinator,
    WorkerTaskDecision,
    WorkerType,
)


def main() -> None:
    child_id = "child-brain-integration"

    army_runtime = ChildArmyRuntime()
    army_manager = ChildArmyManager()

    labor_runtime = ChildLaborRuntime()
    labor_manager = ChildLaborManager()

    coordinator = ChildWorkerCoordinator()

    # ---------------------------------------------------------
    # 1. ARMY REGISTRATION
    # ---------------------------------------------------------

    result = army_manager.register(
        army_id="army-integration-001",
        child_brain_id=child_id,
        specialization="research",
    )

    assert result.allowed is True

    result = army_manager.transition(
        "army-integration-001",
        ArmyBrainState.READY,
        authority_approved=True,
    )

    assert result.allowed is True

    result = army_manager.transition(
        "army-integration-001",
        ArmyBrainState.ACTIVE,
        authority_approved=True,
    )

    assert result.allowed is True

    # ---------------------------------------------------------
    # 2. ARMY COGNITION
    # ---------------------------------------------------------

    result = army_runtime.evaluate(
        ArmyAction.RESEARCH,
    )

    assert result.allowed is True
    assert result.decision == ArmyDecision.ALLOW_COGNITION

    # ---------------------------------------------------------
    # 3. ARMY PROTECTED ACTION
    # ---------------------------------------------------------

    result = army_runtime.evaluate(
        ArmyAction.EXECUTE,
        child_approved=False,
    )

    assert result.allowed is False

    result = army_runtime.evaluate(
        ArmyAction.EXECUTE,
        child_approved=True,
    )

    assert result.allowed is True

    # ---------------------------------------------------------
    # 4. LABOR REGISTRATION
    # ---------------------------------------------------------

    result = labor_manager.register(
        labor_id="labor-integration-001",
        child_brain_id=child_id,
        specialization="file_operations",
    )

    assert result.allowed is True

    result = labor_manager.transition(
        "labor-integration-001",
        LaborBrainState.READY,
        authority_approved=True,
    )

    assert result.allowed is True

    result = labor_manager.transition(
        "labor-integration-001",
        LaborBrainState.ACTIVE,
        authority_approved=True,
    )

    assert result.allowed is True

    # ---------------------------------------------------------
    # 5. LABOR COGNITION
    # ---------------------------------------------------------

    result = labor_runtime.evaluate(
        LaborAction.PLAN,
    )

    assert result.allowed is True
    assert result.decision == LaborDecision.ALLOW_COGNITION

    # ---------------------------------------------------------
    # 6. LABOR PROTECTED ACTION
    # ---------------------------------------------------------

    result = labor_runtime.evaluate(
        LaborAction.WRITE,
        child_authority_approved=False,
    )

    assert result.allowed is False
    assert result.decision == LaborDecision.REQUIRE_CHILD_AUTHORITY

    result = labor_runtime.evaluate(
        LaborAction.WRITE,
        child_authority_approved=True,
    )

    assert result.allowed is True

    # ---------------------------------------------------------
    # 7. WORKER COORDINATOR — AUTHORITY GATE
    # ---------------------------------------------------------

    result = coordinator.assign_task(
        task_id="worker-task-001",
        worker_id="army-integration-001",
        worker_type=WorkerType.ARMY,
        child_brain_id=child_id,
        description="research market intelligence",
        authority_approved=False,
    )

    assert result.allowed is False
    assert result.decision == WorkerTaskDecision.REQUIRE_AUTHORITY

    # ---------------------------------------------------------
    # 8. AUTHORIZED ARMY TASK
    # ---------------------------------------------------------

    assert army_manager.can_assign_task(
        "army-integration-001",
        authority_approved=True,
    )

    result = coordinator.assign_task(
        task_id="worker-task-001",
        worker_id="army-integration-001",
        worker_type=WorkerType.ARMY,
        child_brain_id=child_id,
        description="research market intelligence",
        authority_approved=True,
    )

    assert result.allowed is True
    assert result.task is not None

    # ---------------------------------------------------------
    # 9. AUTHORIZED LABOR TASK
    # ---------------------------------------------------------

    assert labor_manager.can_assign_task(
        "labor-integration-001",
        authority_approved=True,
    )

    result = coordinator.assign_task(
        task_id="worker-task-002",
        worker_id="labor-integration-001",
        worker_type=WorkerType.LABOR,
        child_brain_id=child_id,
        description="prepare approved file operation",
        authority_approved=True,
    )

    assert result.allowed is True
    assert result.task is not None

    # ---------------------------------------------------------
    # 10. CHILD TASK INVENTORY
    # ---------------------------------------------------------

    tasks = coordinator.list_child_tasks(child_id)

    assert len(tasks) == 2

    assert tasks[0].child_brain_id == child_id
    assert tasks[1].child_brain_id == child_id

    # ---------------------------------------------------------
    # 11. WORKER SECURITY INVARIANTS
    # ---------------------------------------------------------

    assert not coordinator.can_worker_assign_own_task()
    assert not coordinator.can_worker_grant_authority()
    assert not coordinator.can_worker_override_child()
    assert not coordinator.can_worker_override_mother()
    assert not coordinator.can_worker_self_promote()
    assert not coordinator.can_worker_execute_without_authority()
    assert not coordinator.can_worker_modify_constitution()
    assert not coordinator.can_worker_modify_soul()

    assert not army_manager.can_self_create_army()
    assert not army_manager.can_grant_authority()
    assert not army_manager.can_self_promote()
    assert not army_manager.can_override_child()
    assert not army_manager.can_override_mother()
    assert not army_manager.can_execute_tools()
    assert not army_manager.can_modify_constitution()

    assert not labor_manager.can_self_create_labor()
    assert not labor_manager.can_grant_authority()
    assert not labor_manager.can_self_promote()
    assert not labor_manager.can_override_child()
    assert not labor_manager.can_override_mother()
    assert not labor_manager.can_execute_tools()
    assert not labor_manager.can_modify_constitution()

    # ---------------------------------------------------------
    # 12. FINANCIAL ACTION — FULL AUTHORITY CHAIN
    # ---------------------------------------------------------

    result = labor_runtime.evaluate(
        LaborAction.FINANCIAL,
        child_authority_approved=True,
        mother_authority_approved=True,
        human_authority_approved=False,
    )

    assert result.allowed is False
    assert result.decision == LaborDecision.REQUIRE_HUMAN_AUTHORITY

    result = labor_runtime.evaluate(
        LaborAction.FINANCIAL,
        child_authority_approved=True,
        mother_authority_approved=True,
        human_authority_approved=True,
    )

    assert result.allowed is True

    print("SAHIBEX CHILD WORKERS INTEGRATION TEST: PASS")


if __name__ == "__main__":
    main()
