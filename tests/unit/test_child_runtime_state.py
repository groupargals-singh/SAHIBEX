from core.brain.child_runtime_state import (
    ChildRuntimeState,
    ChildRuntimeStateManager,
)


def main() -> None:
    manager = ChildRuntimeStateManager()

    decision = manager.transition(
        ChildRuntimeState.PROPOSED,
        ChildRuntimeState.BIRTH_AUTHORIZED,
        authority_approved=True,
        verification_passed=True,
    )
    assert decision.allowed is True
    assert decision.state == ChildRuntimeState.BIRTH_AUTHORIZED

    decision = manager.transition(
        ChildRuntimeState.PROPOSED,
        ChildRuntimeState.ACTIVE,
        authority_approved=True,
        verification_passed=True,
    )
    assert decision.allowed is False

    decision = manager.transition(
        ChildRuntimeState.VERIFIED,
        ChildRuntimeState.READY,
        authority_approved=True,
        verification_passed=False,
    )
    assert decision.allowed is False

    decision = manager.transition(
        ChildRuntimeState.VERIFIED,
        ChildRuntimeState.READY,
        authority_approved=True,
        verification_passed=True,
    )
    assert decision.allowed is True

    assert manager.can_activate(
        ChildRuntimeState.READY,
        authority_approved=True,
        verification_passed=True,
    )

    assert not manager.can_activate(
        ChildRuntimeState.READY,
        authority_approved=False,
        verification_passed=True,
    )

    assert manager.can_recover(
        ChildRuntimeState.ACTIVE,
        authority_approved=True,
    )

    assert manager.can_retire(
        ChildRuntimeState.ACTIVE,
        authority_approved=True,
    )

    assert manager.is_terminal(ChildRuntimeState.RETIRED)

    assert manager.cannot_self_authorize()
    assert manager.cannot_modify_constitution()
    assert manager.cannot_modify_soul()
    assert not manager.grants_authority()
    assert not manager.executes_runtime_action()

    print("SAHIBEX CHILD RUNTIME STATE TEST: PASS")


if __name__ == "__main__":
    main()
