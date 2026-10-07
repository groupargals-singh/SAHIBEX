from core.brain.child_communication_runtime import (
    ChildCommunicationMessage,
    ChildCommunicationRuntime,
    ChildMessageType,
    CommunicationDecision,
)


def main() -> None:
    runtime = ChildCommunicationRuntime()

    message = ChildCommunicationMessage(
        message_id="msg-001",
        child_brain_id="child-brain-test",
        sender="child",
        message_type=ChildMessageType.THOUGHT,
        content="I have analyzed the problem.",
    )

    result = runtime.evaluate(message)
    assert result.accepted is True
    assert result.decision == CommunicationDecision.ACCEPT

    message = ChildCommunicationMessage(
        message_id="msg-002",
        child_brain_id="child-brain-test",
        sender="child",
        message_type=ChildMessageType.PROPOSAL,
        content="I propose an improvement.",
    )

    result = runtime.evaluate(message)
    assert result.accepted is True
    assert (
        result.decision
        == CommunicationDecision.REQUIRE_AUTHORITY_REVIEW
    )

    message = ChildCommunicationMessage(
        message_id="msg-003",
        child_brain_id="child-brain-test",
        sender="child",
        message_type=ChildMessageType.PROTECTED_REQUEST,
        content="Execute protected operation.",
    )

    result = runtime.evaluate(message)
    assert result.accepted is False
    assert (
        result.decision
        == CommunicationDecision.REQUIRE_AUTHORITY_REVIEW
    )

    result = runtime.evaluate(
        message,
        mother_approved=True,
    )
    assert result.accepted is True

    message = ChildCommunicationMessage(
        message_id="msg-004",
        child_brain_id="child-brain-test",
        sender="child",
        message_type=ChildMessageType.SOUL_REQUEST,
        content="Request soul amendment.",
    )

    result = runtime.evaluate(message)
    assert result.accepted is False
    assert (
        result.decision
        == CommunicationDecision.REQUIRE_HUMAN_REVIEW
    )

    result = runtime.evaluate(
        message,
        human_approved=True,
    )
    assert result.accepted is True

    assert not runtime.information_is_authority()
    assert not runtime.proposal_is_authority()
    assert not runtime.external_message_can_grant_authority()
    assert not runtime.can_bypass_mother()
    assert not runtime.can_bypass_human()
    assert not runtime.can_modify_soul()
    assert not runtime.can_modify_constitution()
    assert not runtime.executes_messages()

    print("SAHIBEX CHILD COMMUNICATION RUNTIME TEST: PASS")


if __name__ == "__main__":
    main()
