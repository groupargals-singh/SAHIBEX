from __future__ import annotations

from dataclasses import dataclass

from core.policies.constitution import (
    ActionClass,
    ActionDecision,
    AuthorityLevel,
    SahibexConstitution,
)


@dataclass(frozen=True)
class HumanApprovalDecision:
    action: ActionClass
    allowed: bool
    requires_confirmation: bool
    authority: AuthorityLevel
    decision: ActionDecision
    reason: str


class HumanApprovalGateway:
    """
    Root human-approval gateway for protected SAHIBEX actions.

    This gateway delegates authority decisions to SahibexConstitution.
    It does not modify the constitution and cannot override user authority.
    """

    def __init__(
        self,
        constitution: SahibexConstitution | None = None,
    ) -> None:
        self.constitution = constitution or SahibexConstitution()

    def check(
        self,
        action: ActionClass,
        *,
        user_confirmation: bool = False,
    ) -> HumanApprovalDecision:
        if not isinstance(action, ActionClass):
            raise TypeError("action must be an ActionClass.")

        decision = self.constitution.decide(
            action,
            user_confirmation=user_confirmation,
        )

        return HumanApprovalDecision(
            action=action,
            allowed=decision.decision == ActionDecision.ALLOW,
            requires_confirmation=(
                decision.decision == ActionDecision.REQUIRE_CONFIRMATION
            ),
            authority=decision.authority,
            decision=decision.decision,
            reason=decision.reason,
        )

    def require(
        self,
        action: ActionClass,
        *,
        user_confirmation: bool = False,
    ) -> HumanApprovalDecision:
        result = self.check(
            action,
            user_confirmation=user_confirmation,
        )

        if not result.allowed:
            if result.requires_confirmation:
                raise PermissionError(
                    f"User approval required for action: {action.value}"
                )

            raise PermissionError(
                f"Action denied: {action.value}"
            )

        return result
