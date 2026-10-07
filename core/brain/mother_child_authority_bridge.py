from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AuthorityRequestType(str, Enum):
    PROTECTED_ACTION = "protected_action"
    FINANCIAL_ACTION = "financial_action"
    SELF_IMPROVEMENT = "self_improvement"
    CHILD_CREATION = "child_creation"
    CONSTITUTIONAL_CHANGE = "constitutional_change"
    SOUL_CHANGE = "soul_change"


class AuthorityDecision(str, Enum):
    REQUIRE_MOTHER = "require_mother"
    REQUIRE_HUMAN = "require_human"
    APPROVED = "approved"
    DENIED = "denied"


@dataclass(frozen=True)
class ChildAuthorityRequest:
    request_id: str
    child_brain_id: str
    request_type: AuthorityRequestType
    purpose: str


@dataclass(frozen=True)
class AuthorityResult:
    allowed: bool
    decision: AuthorityDecision
    reason: str


class MotherChildAuthorityBridge:
    VERSION = "1.0"

    HUMAN_ONLY_REQUESTS = {
        AuthorityRequestType.FINANCIAL_ACTION,
        AuthorityRequestType.CONSTITUTIONAL_CHANGE,
        AuthorityRequestType.SOUL_CHANGE,
        AuthorityRequestType.CHILD_CREATION,
    }

    def evaluate(
        self,
        request: ChildAuthorityRequest,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> AuthorityResult:

        if not request.request_id:
            return AuthorityResult(
                False,
                AuthorityDecision.DENIED,
                "authority request identity is required",
            )

        if not request.child_brain_id:
            return AuthorityResult(
                False,
                AuthorityDecision.DENIED,
                "child brain identity is required",
            )

        if not request.purpose:
            return AuthorityResult(
                False,
                AuthorityDecision.DENIED,
                "request purpose is required",
            )

        if request.request_type in self.HUMAN_ONLY_REQUESTS:
            if not human_approved:
                return AuthorityResult(
                    False,
                    AuthorityDecision.REQUIRE_HUMAN,
                    "human approval required",
                )

            return AuthorityResult(
                True,
                AuthorityDecision.APPROVED,
                "human-approved authority request",
            )

        if not mother_approved:
            return AuthorityResult(
                False,
                AuthorityDecision.REQUIRE_MOTHER,
                "mother approval required",
            )

        return AuthorityResult(
            True,
            AuthorityDecision.APPROVED,
            "mother-approved authority request",
        )

    def can_child_self_authorize(self) -> bool:
        return False

    def can_child_grant_authority(self) -> bool:
        return False

    def can_mother_bypass_human(self) -> bool:
        return False

    def can_external_model_authorize(self) -> bool:
        return False

    def can_tool_authorize(self) -> bool:
        return False

    def can_override_rejection(self) -> bool:
        return False

    def can_execute_action(self) -> bool:
        return False

    def requires_mother_for_protected(self) -> bool:
        return True

    def requires_human_for_sensitive(self) -> bool:
        return True

    def fails_closed(self) -> bool:
        return True
