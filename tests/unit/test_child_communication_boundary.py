from core.brain.child_communication_boundary import (
    ChildCommunicationBoundary,
    CommunicationActor,
    CommunicationDecision,
    MessageType,
)


def main() -> None:
    boundary = ChildCommunicationBoundary

    # Information must remain information.
    for message_type in (
        MessageType.INFORMATION,
        MessageType.THOUGHT,
        MessageType.RESEARCH_RESULT,
    ):
        result = boundary.receive(
            CommunicationActor.CHILD_BRAIN,
            message_type,
        )

        assert result.accepted
        assert result.decision == CommunicationDecision.ACCEPT_INFORMATION
        assert not result.authority_granted
        assert not result.permission_granted

    # Proposals/requests require later authority review.
    for message_type in (
        MessageType.PROPOSAL,
        MessageType.REQUEST,
    ):
        result = boundary.receive(
            CommunicationActor.CHILD_BRAIN,
            message_type,
        )

        assert result.accepted
        assert result.decision == CommunicationDecision.ACCEPT_PROPOSAL
        assert not result.authority_granted
        assert not result.permission_granted

    # Protected communication never becomes authority automatically.
    for message_type in (
        MessageType.COMMAND,
        MessageType.PERMISSION,
        MessageType.AUTHORITY_GRANT,
        MessageType.CONSTITUTIONAL_CHANGE,
        MessageType.SOUL_CHANGE,
    ):
        result = boundary.receive(
            CommunicationActor.CHILD_BRAIN,
            message_type,
        )

        assert result.accepted
        assert (
            result.decision
            == CommunicationDecision.REQUIRE_AUTHORITY_CHECK
        )
        assert not result.authority_granted
        assert not result.permission_granted

    # External actors cannot grant authority.
    for actor in (
        CommunicationActor.SOFTWARE,
        CommunicationActor.TOOL,
        CommunicationActor.EXTERNAL_MODEL,
    ):
        result = boundary.receive(
            actor,
            MessageType.AUTHORITY_GRANT,
        )

        assert not result.accepted
        assert result.decision == CommunicationDecision.DENY
        assert not result.authority_granted
        assert not result.permission_granted

    # External information can be received without authority.
    result = boundary.receive(
        CommunicationActor.EXTERNAL_MODEL,
        MessageType.INFORMATION,
    )

    assert result.accepted
    assert not result.authority_granted
    assert not result.permission_granted

    # Core constitutional guarantees.
    assert not boundary.communication_grants_authority()
    assert not boundary.communication_grants_permission()
    assert not boundary.child_can_command_mother()
    assert not boundary.child_can_override_mother_through_message()
    assert not boundary.child_can_override_human_through_message()
    assert not boundary.army_can_override_child()
    assert not boundary.labor_can_override_child()
    assert not boundary.external_model_can_be_authority()
    assert not boundary.tool_can_be_authority()
    assert not boundary.software_can_be_authority()

    assert boundary.unknown_state_fails_closed()
    assert boundary.protected_message_requires_authority_check()
    assert boundary.communication_is_separate_from_authority()
    assert not boundary.executes_commands()

    print("SAHIBEX CHILD COMMUNICATION BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
