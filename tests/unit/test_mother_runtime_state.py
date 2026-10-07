from core.brain.mother_runtime_state import (
    MotherBrainState,
    MotherRuntimeState,
)


def main() -> None:
    state = MotherBrainState()

    assert state.state == MotherRuntimeState.IDLE

    state.begin("Explain SAHIBEX architecture.")
    assert state.state == MotherRuntimeState.RECEIVING

    state.transition(MotherRuntimeState.UNDERSTANDING)
    assert state.state == MotherRuntimeState.UNDERSTANDING

    state.set_request_context(
        intent="explain",
        action="respond",
        risk="low",
    )

    state.transition(MotherRuntimeState.AUTHORIZING)

    state.set_authority(
        permission_allowed=True,
        confirmation_required=False,
    )

    state.transition(MotherRuntimeState.VERIFYING)

    state.set_verification("VERIFIED")

    state.transition(MotherRuntimeState.CONTEXTUALIZING)
    state.transition(MotherRuntimeState.REASONING)

    state.set_operation("mother_reasoning")

    state.transition(MotherRuntimeState.EXECUTING)
    state.transition(MotherRuntimeState.PLANNING)

    state.complete("request completed")

    snapshot = state.snapshot()

    assert state.state == MotherRuntimeState.COMPLETED
    assert snapshot["state"] == "completed"
    assert snapshot["intent"] == "explain"
    assert snapshot["permission_allowed"] is True
    assert snapshot["verification_status"] == "VERIFIED"

    blocked = MotherBrainState()
    blocked.begin("Delete a file.")
    blocked.block("Explicit approval required.")

    assert blocked.state == MotherRuntimeState.BLOCKED
    assert blocked.snapshot()["outcome"] == "blocked"

    failed = MotherBrainState()
    failed.begin("Run operation.")
    failed.fail("Verification failed.")

    assert failed.state == MotherRuntimeState.FAILED
    assert failed.snapshot()["reason"] == "Verification failed."

    print("SAHIBEX MOTHER RUNTIME STATE TEST: PASS")


if __name__ == "__main__":
    main()
