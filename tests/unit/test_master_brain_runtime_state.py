from core.brain.master_brain import MasterBrain
from core.brain.mother_runtime_state import MotherRuntimeState


def main() -> None:
    brain = MasterBrain()

    # ---------------------------------------------------------
    # SUCCESSFUL REQUEST
    # ---------------------------------------------------------

    result = brain.process(
        "Explain SAHIBEX architecture."
    )

    assert result.success is True

    state = result.metadata.get(
        "mother_runtime_state"
    )

    assert state is not None
    assert state["state"] == (
        MotherRuntimeState.COMPLETED.value
    )
    assert state["request"] == (
        "Explain SAHIBEX architecture."
    )
    assert state["intent"] == "explain"
    assert state["permission_allowed"] is True

    # ---------------------------------------------------------
    # PROTECTED ACTION WITHOUT CONFIRMATION
    # ---------------------------------------------------------

    blocked = brain.process(
        "delete this file"
    )

    assert blocked.success is True
    blocked_state = brain.runtime_state.snapshot()

    assert blocked_state["state"] == (
        MotherRuntimeState.BLOCKED.value
    )
    assert blocked_state["outcome"] == "blocked"
    assert blocked_state["reason"]

    print(
        "SAHIBEX MASTER BRAIN RUNTIME STATE TEST: PASS"
    )


if __name__ == "__main__":
    main()
