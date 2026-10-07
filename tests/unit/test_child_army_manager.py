from core.brain.child_army_manager import (
    ArmyBrainState,
    ChildArmyManager,
)


def main() -> None:
    manager = ChildArmyManager()

    result = manager.register(
        army_id="army-test-001",
        child_brain_id="child-brain-test",
        specialization="research",
    )

    assert result.allowed is True
    assert result.record is not None
    assert result.record.state == ArmyBrainState.REGISTERED

    result = manager.register(
        army_id="army-test-001",
        child_brain_id="child-brain-test",
        specialization="research",
    )
    assert result.allowed is False

    result = manager.transition(
        "army-test-001",
        ArmyBrainState.READY,
        authority_approved=False,
    )
    assert result.allowed is False

    result = manager.transition(
        "army-test-001",
        ArmyBrainState.READY,
        authority_approved=True,
    )
    assert result.allowed is True

    result = manager.transition(
        "army-test-001",
        ArmyBrainState.ACTIVE,
        authority_approved=True,
    )
    assert result.allowed is True

    assert manager.can_assign_task(
        "army-test-001",
        authority_approved=True,
    )

    assert not manager.can_assign_task(
        "army-test-001",
        authority_approved=False,
    )

    records = manager.list_child_army(
        "child-brain-test"
    )
    assert len(records) == 1
    assert records[0].army_id == "army-test-001"

    assert not manager.can_self_create_army()
    assert not manager.can_grant_authority()
    assert not manager.can_self_promote()
    assert not manager.can_override_child()
    assert not manager.can_override_mother()
    assert not manager.can_execute_tools()
    assert not manager.can_modify_constitution()

    print("SAHIBEX CHILD ARMY MANAGER TEST: PASS")


if __name__ == "__main__":
    main()
