from dataclasses import dataclass
from typing import Any

from core.brain.intent import IntentResult
from core.brain.action_classifier import ActionClassifier
from core.brain.permission_gateway import PermissionGateway
from core.policies.approval import (
    ActionType,
    PermissionEngine,
    PermissionDecision,
)
from verification.verifier import (
    VerificationEngine,
    VerificationResult,
)


@dataclass(frozen=True)
class RouteResult:
    action: ActionType
    decision: PermissionDecision
    action_confidence: float
    verification: VerificationResult
    metadata: dict[str, Any]


class CommandRouter:
    """
    Central routing layer.

    Intent
       ↓
    Action Classification
       ↓
    Permission
       ↓
    Verification
       ↓
    Route Result

    No actual execution happens here.
    """

    INTENT_DEFAULT_ACTIONS = {
        "system_status": ActionType.RESPOND,
        "search": ActionType.RESEARCH,
        "create": ActionType.CREATE,
        "explain": ActionType.RESPOND,
        "code": ActionType.CREATE,
        "file_operation": ActionType.READ_FILE,
        "general_request": ActionType.RESPOND,
        "empty": ActionType.RESPOND,
    }

    def __init__(self) -> None:
        self.permission_engine = PermissionEngine()
        self.permission_gateway = PermissionGateway(
            permission_engine=self.permission_engine,
        )
        self.action_classifier = ActionClassifier()
        self.verifier = VerificationEngine()

    def route(
        self,
        text: str,
        intent_result: IntentResult,
    ) -> RouteResult:

        classified = self.action_classifier.classify(text)

        action = classified.action

        if action == ActionType.RESPOND:
            action = self.INTENT_DEFAULT_ACTIONS.get(
                intent_result.intent,
                ActionType.RESPOND,
            )

        decision = self.permission_gateway.check(action)

        verification = self.verifier.verify(
            intent=intent_result.intent,
            intent_confidence=intent_result.confidence,
            action=action,
            action_confidence=classified.confidence,
            risk=decision.risk,
            permission_allowed=decision.allowed,
            confirmation_required=(
                decision.requires_confirmation
            ),
        )

        # Verification failure creates a safety hold.
        if not verification.verified:
            decision = PermissionDecision(
                allowed=False,
                requires_confirmation=True,
                risk=decision.risk,
                reason=(
                    "Verification failed. "
                    "Action placed on safety hold."
                ),
            )

        return RouteResult(
            action=action,
            decision=decision,
            action_confidence=classified.confidence,
            verification=verification,
            metadata={
                "intent": intent_result.intent,
                "intent_confidence": (
                    intent_result.confidence
                ),
                "action_reason": classified.reason,
                "router": "command_router_v3",
            },
        )
