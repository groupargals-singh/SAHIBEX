from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChildMessageType(str, Enum):
    INFORMATION = "information"
    THOUGHT = "thought"
    RESEARCH_RESULT = "research_result"
    PROPOSAL = "proposal"
    AUTHORITY_REQUEST = "authority_request"
    PROTECTED_REQUEST = "protected_request"
    CONSTITUTIONAL_REQUEST = "constitutional_request"
    SOUL_REQUEST = "soul_request"


class CommunicationDecision(str, Enum):
    ACCEPT = "accept"
    REQUIRE_AUTHORITY_REVIEW = "require_authority_review"
    REQUIRE_HUMAN_REVIEW = "require_human_review"
    DENY = "deny"


@dataclass(frozen=True)
class ChildCommunicationMessage:
    message_id: str
    child_brain_id: str
    sender: str
    message_type: ChildMessageType
    content: str


@dataclass(frozen=True)
class CommunicationResult:
    accepted: bool
    decision: CommunicationDecision
    reason: str


class ChildCommunicationRuntime:
    VERSION = "1.0"

    def evaluate(
        self,
        message: ChildCommunicationMessage,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> CommunicationResult:
        if not isinstance(message, ChildCommunicationMessage):
            return CommunicationResult(
                False,
                CommunicationDecision.DENY,
                "invalid communication message",
            )

        if not message.message_id or not message.child_brain_id:
            return CommunicationResult(
                False,
                CommunicationDecision.DENY,
                "message identity is required",
            )

        if not message.content:
            return CommunicationResult(
                False,
                CommunicationDecision.DENY,
                "message content is required",
            )

        if message.message_type in {
            ChildMessageType.INFORMATION,
            ChildMessageType.THOUGHT,
            ChildMessageType.RESEARCH_RESULT,
        }:
            return CommunicationResult(
                True,
                CommunicationDecision.ACCEPT,
                "informational message accepted",
            )

        if message.message_type == ChildMessageType.PROPOSAL:
            return CommunicationResult(
                True,
                CommunicationDecision.REQUIRE_AUTHORITY_REVIEW,
                "proposal accepted for authority review",
            )

        if message.message_type == ChildMessageType.AUTHORITY_REQUEST:
            if not mother_approved:
                return CommunicationResult(
                    False,
                    CommunicationDecision.REQUIRE_AUTHORITY_REVIEW,
                    "mother authority review required",
                )

            return CommunicationResult(
                True,
                CommunicationDecision.REQUIRE_AUTHORITY_REVIEW,
                "mother authority approved",
            )

        if message.message_type == ChildMessageType.PROTECTED_REQUEST:
            if not mother_approved:
                return CommunicationResult(
                    False,
                    CommunicationDecision.REQUIRE_AUTHORITY_REVIEW,
                    "protected request requires mother approval",
                )

            return CommunicationResult(
                True,
                CommunicationDecision.REQUIRE_AUTHORITY_REVIEW,
                "protected request approved by mother",
            )

        if message.message_type in {
            ChildMessageType.CONSTITUTIONAL_REQUEST,
            ChildMessageType.SOUL_REQUEST,
        }:
            if not human_approved:
                return CommunicationResult(
                    False,
                    CommunicationDecision.REQUIRE_HUMAN_REVIEW,
                    "constitutional or soul request requires human authority",
                )

            return CommunicationResult(
                True,
                CommunicationDecision.REQUIRE_HUMAN_REVIEW,
                "human authority approved review",
            )

        return CommunicationResult(
            False,
            CommunicationDecision.DENY,
            "unknown message type",
        )

    def information_is_authority(self) -> bool:
        return False

    def proposal_is_authority(self) -> bool:
        return False

    def external_message_can_grant_authority(self) -> bool:
        return False

    def can_bypass_mother(self) -> bool:
        return False

    def can_bypass_human(self) -> bool:
        return False

    def can_modify_soul(self) -> bool:
        return False

    def can_modify_constitution(self) -> bool:
        return False

    def executes_messages(self) -> bool:
        return False
