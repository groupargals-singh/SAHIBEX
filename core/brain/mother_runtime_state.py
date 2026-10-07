from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from datetime import datetime, timezone


class MotherRuntimeState(str, Enum):
    IDLE = "idle"
    RECEIVING = "receiving"
    UNDERSTANDING = "understanding"
    AUTHORIZING = "authorizing"
    VERIFYING = "verifying"
    CONTEXTUALIZING = "contextualizing"
    REASONING = "reasoning"
    EXECUTING = "executing"
    PLANNING = "planning"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class MotherBrainState:
    """
    Runtime state for one Mother Brain request.

    This state records lifecycle only.
    It grants no authority and cannot bypass
    Constitution, Permission, or Verification.
    """

    state: MotherRuntimeState = MotherRuntimeState.IDLE
    request: str = ""
    intent: str = ""
    action: str = ""
    risk: str = ""
    permission_allowed: bool = False
    confirmation_required: bool = False
    verification_status: str = ""
    active_operation: str = ""
    outcome: str = ""
    reason: str = ""
    started_at: str | None = None
    updated_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def begin(self, request: str) -> None:
        if not isinstance(request, str) or not request.strip():
            raise ValueError("request must be a non-empty string")

        timestamp = self._timestamp()

        self.request = request.strip()
        self.state = MotherRuntimeState.RECEIVING
        self.started_at = timestamp
        self.updated_at = timestamp
        self.outcome = ""
        self.reason = ""
        self.active_operation = ""

    def transition(self, state: MotherRuntimeState) -> None:
        if not isinstance(state, MotherRuntimeState):
            raise TypeError("state must be MotherRuntimeState")

        self.state = state
        self.updated_at = self._timestamp()

    def set_request_context(
        self,
        *,
        intent: str,
        action: str,
        risk: str,
    ) -> None:
        self.intent = intent
        self.action = action
        self.risk = risk
        self.updated_at = self._timestamp()

    def set_authority(
        self,
        *,
        permission_allowed: bool,
        confirmation_required: bool,
    ) -> None:
        self.permission_allowed = permission_allowed
        self.confirmation_required = confirmation_required
        self.updated_at = self._timestamp()

    def set_verification(self, status: str) -> None:
        self.verification_status = status
        self.updated_at = self._timestamp()

    def set_operation(self, operation: str) -> None:
        self.active_operation = operation
        self.updated_at = self._timestamp()

    def complete(self, outcome: str = "completed") -> None:
        self.state = MotherRuntimeState.COMPLETED
        self.outcome = outcome
        self.reason = ""
        self.active_operation = ""
        self.updated_at = self._timestamp()

    def block(self, reason: str) -> None:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("block reason must be non-empty")

        self.state = MotherRuntimeState.BLOCKED
        self.reason = reason
        self.outcome = "blocked"
        self.active_operation = ""
        self.updated_at = self._timestamp()

    def fail(self, reason: str) -> None:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("failure reason must be non-empty")

        self.state = MotherRuntimeState.FAILED
        self.reason = reason
        self.outcome = "failed"
        self.active_operation = ""
        self.updated_at = self._timestamp()

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "request": self.request,
            "intent": self.intent,
            "action": self.action,
            "risk": self.risk,
            "permission_allowed": self.permission_allowed,
            "confirmation_required": self.confirmation_required,
            "verification_status": self.verification_status,
            "active_operation": self.active_operation,
            "outcome": self.outcome,
            "reason": self.reason,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }
