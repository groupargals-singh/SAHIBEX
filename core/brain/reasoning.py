from dataclasses import dataclass
from typing import Any

from app.config import settings

from core.brain.intent import IntentEngine
from core.brain.context import ContextManager
from core.orchestrator.dispatcher import CommandRouter
from security.audit.audit_logger import AuditLogger


@dataclass
class ReasoningResult:
    success: bool
    intent: str
    action: str
    response: str
    confidence: float
    action_confidence: float
    requires_confirmation: bool
    metadata: dict[str, Any]


class ReasoningEngine:
    """
    Core reasoning pipeline.

    Intent
       ↓
    Context
       ↓
    Action Classification
       ↓
    Permission
       ↓
    Verification
       ↓
    Audit
       ↓
    Safe Response
    """

    def __init__(self) -> None:
        self.intent_engine = IntentEngine()
        self.context = ContextManager()
        self.router = CommandRouter()

        self.audit = AuditLogger(
            settings.logs_dir
        )

    def analyze(self, user_input: str) -> ReasoningResult:
        text = user_input.strip()

        if not text:
            return ReasoningResult(
                success=False,
                intent="empty",
                action="respond",
                response="No command was provided.",
                confidence=1.0,
                action_confidence=1.0,
                requires_confirmation=False,
                metadata={},
            )

        intent_result = self.intent_engine.detect(text)

        route = self.router.route(
            text=text,
            intent_result=intent_result,
        )

        verification = route.verification

        self.audit.record(
            request=text,
            intent=intent_result.intent,
            intent_confidence=intent_result.confidence,
            action=route.action.value,
            action_confidence=route.action_confidence,
            risk=route.decision.risk.value,
            permission_allowed=route.decision.allowed,
            confirmation_required=(
                route.decision.requires_confirmation
            ),
            reason=(
                route.decision.reason
                + " "
                + verification.status
            ),
        )

        response = self._build_response(
            text=text,
            intent=intent_result.intent,
            action=route.action.value,
            allowed=route.decision.allowed,
            requires_confirmation=(
                route.decision.requires_confirmation
            ),
            verification_status=verification.status,
        )

        self.context.add_turn(
            user=text,
            assistant=response,
            intent=intent_result.intent,
        )

        return ReasoningResult(
            success=True,
            intent=intent_result.intent,
            action=route.action.value,
            response=response,
            confidence=intent_result.confidence,
            action_confidence=route.action_confidence,
            requires_confirmation=(
                route.decision.requires_confirmation
            ),
            metadata={
                "context": self.context.summary(),
                "stage": (
                    "intent_context_action_permission_"
                    "verification_audit"
                ),
                "risk": route.decision.risk.value,
                "permission_allowed": (
                    route.decision.allowed
                ),
                "permission_reason": (
                    route.decision.reason
                ),
                "action_reason": (
                    route.metadata["action_reason"]
                ),
                "verification": verification.status,
                "checks_passed": (
                    verification.checks_passed
                ),
                "checks_failed": (
                    verification.checks_failed
                ),
                "verification_reasons": (
                    verification.reasons
                ),
            },
        )

    def _build_response(
        self,
        text: str,
        intent: str,
        action: str,
        allowed: bool,
        requires_confirmation: bool,
        verification_status: str,
    ) -> str:

        if verification_status != "VERIFIED":
            return (
                f"SAHIBEX placed this request on a "
                f"safety hold because verification failed. "
                f"Detected action: '{action}'."
            )

        if requires_confirmation:
            return (
                f"Request classified as '{intent}'. "
                f"Detected action '{action}'. "
                f"Verification passed, but explicit "
                f"user confirmation is required before "
                f"execution."
            )

        if intent == "system_status":
            return (
                "SAHIBEX foundation is online. "
                "Intent, context, routing, action "
                "classification, permission, verification "
                "and audit systems are active."
            )

        if intent == "search":
            return (
                "Research request detected and verified. "
                "The research execution tool is not "
                "connected yet."
            )

        if intent == "create":
            return (
                "Creation request detected and verified. "
                "The execution agent is not connected yet."
            )

        if intent == "explain":
            return (
                "Explanation request detected and verified. "
                "The reasoning path is active."
            )

        if intent == "code":
            return (
                "Coding request detected and verified. "
                "The coding agent is not connected yet."
            )

        if intent == "file_operation":
            return (
                f"File operation detected and verified. "
                f"Action classified as '{action}'."
            )

        return f"I understood your request: {text}"
