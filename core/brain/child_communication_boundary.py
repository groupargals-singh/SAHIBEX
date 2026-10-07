from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CommunicationActor(str, Enum):
    HUMAN = "human"
    SAHIBEX_MOTHER = "sahibex_mother"
    CHILD_BRAIN = "child_brain"
    CHILD_ARMY = "child_army"
    CHILD_LABOR = "child_labor"
    SOFTWARE = "software"
    TOOL = "tool"
    EXTERNAL_MODEL = "external_model"


class MessageType(str, Enum):
    INFORMATION = "information"
    THOUGHT = "thought"
    RESEARCH_RESULT = "research_result"
    PROPOSAL = "proposal"
    REQUEST = "request"
    COMMAND = "command"
    PERMISSION = "permission"
    AUTHORITY_GRANT = "authority_grant"
    CONSTITUTIONAL_CHANGE = "constitutional_change"
    SOUL_CHANGE = "soul_change"


class CommunicationDecision(str, Enum):
    ACCEPT_INFORMATION = "accept_information"
    ACCEPT_PROPOSAL = "accept_proposal"
    REQUIRE_AUTHORITY_CHECK = "require_authority_check"
    DENY = "deny"


@dataclass(frozen=True)
class CommunicationResult:
    accepted: bool
    decision: CommunicationDecision
    authority_granted: bool
    permission_granted: bool
    reason: str


class ChildCommunicationBoundary:
    """
    Communication boundary for a future Child Brain.

    Communication is never authority by itself.
    Messages must pass authority and security boundaries
    before protected actions can occur.
    """

    VERSION = "1.0"

    TRUSTED_INFORMATION_ACTORS = {
        CommunicationActor.HUMAN,
        CommunicationActor.SAHIBEX_MOTHER,
        CommunicationActor.CHILD_BRAIN,
        CommunicationActor.CHILD_ARMY,
        CommunicationActor.CHILD_LABOR,
    }

    UNTRUSTED_AUTHORITY_ACTORS = {
        CommunicationActor.SOFTWARE,
        CommunicationActor.TOOL,
        CommunicationActor.EXTERNAL_MODEL,
    }

    INFORMATION_MESSAGES = {
        MessageType.INFORMATION,
        MessageType.THOUGHT,
        MessageType.RESEARCH_RESULT,
    }

    PROPOSAL_MESSAGES = {
        MessageType.PROPOSAL,
        MessageType.REQUEST,
    }

    PROTECTED_MESSAGES = {
        MessageType.COMMAND,
        MessageType.PERMISSION,
        MessageType.AUTHORITY_GRANT,
        MessageType.CONSTITUTIONAL_CHANGE,
        MessageType.SOUL_CHANGE,
    }

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @classmethod
    def receive(
        cls,
        sender: CommunicationActor,
        message_type: MessageType,
    ) -> CommunicationResult:

        # External tools/models/software cannot become authority
        # merely by sending a message.
        if sender in cls.UNTRUSTED_AUTHORITY_ACTORS:
            if message_type in cls.INFORMATION_MESSAGES:
                return CommunicationResult(
                    accepted=True,
                    decision=CommunicationDecision.ACCEPT_INFORMATION,
                    authority_granted=False,
                    permission_granted=False,
                    reason="external_information_has_no_authority",
                )

            return CommunicationResult(
                accepted=False,
                decision=CommunicationDecision.DENY,
                authority_granted=False,
                permission_granted=False,
                reason="untrusted_actor_cannot_grant_authority",
            )

        # Information is accepted as information, never as authority.
        if message_type in cls.INFORMATION_MESSAGES:
            return CommunicationResult(
                accepted=True,
                decision=CommunicationDecision.ACCEPT_INFORMATION,
                authority_granted=False,
                permission_granted=False,
                reason="information_does_not_grant_authority",
            )

        # Proposals/requests can enter the decision pipeline.
        if message_type in cls.PROPOSAL_MESSAGES:
            return CommunicationResult(
                accepted=True,
                decision=CommunicationDecision.ACCEPT_PROPOSAL,
                authority_granted=False,
                permission_granted=False,
                reason="proposal_requires_authority_review",
            )

        # Protected messages require a separate authority check.
        if message_type in cls.PROTECTED_MESSAGES:
            return CommunicationResult(
                accepted=True,
                decision=CommunicationDecision.REQUIRE_AUTHORITY_CHECK,
                authority_granted=False,
                permission_granted=False,
                reason="communication_is_not_authority",
            )

        # Unknown state fails closed.
        return CommunicationResult(
            accepted=False,
            decision=CommunicationDecision.DENY,
            authority_granted=False,
            permission_granted=False,
            reason="unknown_message_state_fails_closed",
        )

    @classmethod
    def communication_grants_authority(cls) -> bool:
        return False

    @classmethod
    def communication_grants_permission(cls) -> bool:
        return False

    @classmethod
    def child_can_command_mother(cls) -> bool:
        return False

    @classmethod
    def child_can_override_mother_through_message(cls) -> bool:
        return False

    @classmethod
    def child_can_override_human_through_message(cls) -> bool:
        return False

    @classmethod
    def army_can_override_child(cls) -> bool:
        return False

    @classmethod
    def labor_can_override_child(cls) -> bool:
        return False

    @classmethod
    def external_model_can_be_authority(cls) -> bool:
        return False

    @classmethod
    def tool_can_be_authority(cls) -> bool:
        return False

    @classmethod
    def software_can_be_authority(cls) -> bool:
        return False

    @classmethod
    def unknown_state_fails_closed(cls) -> bool:
        return True

    @classmethod
    def protected_message_requires_authority_check(cls) -> bool:
        return True

    @classmethod
    def communication_is_separate_from_authority(cls) -> bool:
        return True

    @classmethod
    def executes_commands(cls) -> bool:
        return False


def main() -> None:
    boundary = ChildCommunicationBoundary

    # Normal information.
    result = boundary.receive(
        CommunicationActor.CHILD_BRAIN,
        MessageType.INFORMATION,
    )

    assert result.accepted
    assert result.decision == CommunicationDecision.ACCEPT_INFORMATION
    assert not result.authority_granted
    assert not result.permission_granted

    # Research result is information, not authority.
    result = boundary.receive(
        CommunicationActor.CHILD_BRAIN,
        MessageType.RESEARCH_RESULT,
    )

    assert result.accepted
    assert not result.authority_granted

    # Proposal enters review but grants no authority.
    result = boundary.receive(
        CommunicationActor.CHILD_BRAIN,
        MessageType.PROPOSAL,
    )

    assert result.accepted
    assert result.decision == CommunicationDecision.ACCEPT_PROPOSAL
    assert not result.authority_granted
    assert not result.permission_granted

    # Command requires separate authority verification.
    result = boundary.receive(
        CommunicationActor.SAHIBEX_MOTHER,
        MessageType.COMMAND,
    )

    assert result.accepted
    assert (
        result.decision
        == CommunicationDecision.REQUIRE_AUTHORITY_CHECK
    )
    assert not result.permission_granted

    # Permission message itself does not automatically become valid permission.
    result = boundary.receive(
        CommunicationActor.CHILD_BRAIN,
        MessageType.PERMISSION,
    )

    assert result.accepted
    assert (
        result.decision
        == CommunicationDecision.REQUIRE_AUTHORITY_CHECK
    )
    assert not result.permission_granted

    # External model cannot grant authority.
    result = boundary.receive(
        CommunicationActor.EXTERNAL_MODEL,
        MessageType.AUTHORITY_GRANT,
    )

    assert not result.accepted
    assert not result.authority_granted
    assert not result.permission_granted
    assert result.decision == CommunicationDecision.DENY

    # External model may provide information, but not authority.
    result = boundary.receive(
        CommunicationActor.EXTERNAL_MODEL,
        MessageType.INFORMATION,
    )

    assert result.accepted
    assert not result.authority_granted
    assert not result.permission_granted

    # Constitutional change requires authority review.
    result = boundary.receive(
        CommunicationActor.CHILD_BRAIN,
        MessageType.CONSTITUTIONAL_CHANGE,
    )

    assert result.accepted
    assert (
        result.decision
        == CommunicationDecision.REQUIRE_AUTHORITY_CHECK
    )
    assert not result.authority_granted
    assert not result.permission_granted

    # Constitutional guarantees.
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

    # Communication layer never executes commands.
    assert not boundary.executes_commands()

    print("SAHIBEX CHILD COMMUNICATION BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
