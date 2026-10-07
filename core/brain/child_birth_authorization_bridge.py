from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BirthAuthorizationDecision(str, Enum):
    REQUIRE_MOTHER = "require_mother"
    REQUIRE_HUMAN = "require_human"
    AUTHORIZED = "authorized"
    DENIED = "denied"


@dataclass(frozen=True)
class BirthAuthorizationRequest:
    proposal_id: str
    child_brain_id: str
    purpose: str


@dataclass(frozen=True)
class BirthAuthorizationResult:
    allowed: bool
    decision: BirthAuthorizationDecision
    reason: str


class ChildBirthAuthorizationBridge:
    VERSION = "1.0"

    def evaluate(
        self,
        request: BirthAuthorizationRequest,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> BirthAuthorizationResult:

        if not request.proposal_id:
            return BirthAuthorizationResult(
                False,
                BirthAuthorizationDecision.DENIED,
                "birth proposal identity is required",
            )

        if not request.child_brain_id:
            return BirthAuthorizationResult(
                False,
                BirthAuthorizationDecision.DENIED,
                "child brain identity is required",
            )

        if not request.purpose:
            return BirthAuthorizationResult(
                False,
                BirthAuthorizationDecision.DENIED,
                "child purpose is required",
            )

        if not mother_approved:
            return BirthAuthorizationResult(
                False,
                BirthAuthorizationDecision.REQUIRE_MOTHER,
                "mother approval required",
            )

        if not human_approved:
            return BirthAuthorizationResult(
                False,
                BirthAuthorizationDecision.REQUIRE_HUMAN,
                "human approval required",
            )

        return BirthAuthorizationResult(
            True,
            BirthAuthorizationDecision.AUTHORIZED,
            "child birth authorization approved",
        )

    def can_child_authorize_birth(self) -> bool:
        return False

    def can_mother_authorize_without_human(self) -> bool:
        return False

    def can_external_model_authorize(self) -> bool:
        return False

    def can_tool_authorize(self) -> bool:
        return False

    def can_self_authorize(self) -> bool:
        return False

    def can_execute_birth(self) -> bool:
        return False

    def requires_mother_approval(self) -> bool:
        return True

    def requires_human_approval(self) -> bool:
        return True
