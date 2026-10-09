"""SAHIBEX-owned internal specialist roles (not independent Child Brains).

These role definitions are part of the Mother Brain runtime and do not
instantiate separate identities, independent constitutions, or child births.
The registry is deliberately descriptive: a role is marked executable only
when a real handler is registered by the runtime. It never grants permission.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class InternalBrainRole:
    role_id: str
    purpose: str
    capabilities: tuple[str, ...]
    handler_registered: bool


@dataclass(frozen=True)
class InternalBrainDispatch:
    accepted: bool
    role_id: str
    request: str
    result: Any = None
    reason: str = ""


InternalHandler = Callable[[str, dict[str, Any]], Any]


class InternalBrainTeam:
    """In-process role registry for SAHIBEX's own army/labor specialists."""

    ROLE_PURPOSES = {
        "reading": ("Read and extract source material", ("read", "extract")),
        "research": ("Discover public sources and collect evidence", ("research", "source_check")),
        "learning": ("Consolidate verified learning and feedback", ("learn", "memory")),
        "reasoning": ("Compare options and construct explanations", ("reason", "plan")),
        "coding": ("Create or review code through authorized tools", ("code", "review")),
        "testing": ("Analyze supplied results from tests executed through authorized tooling", ("test_report", "failure_analysis")),
        "verification": ("Check claims, evidence, conflicts and uncertainty", ("verify", "evidence")),
        "memory": ("Retrieve and organize persistent context", ("memory", "retrieve")),
        "security": ("Review boundaries, permissions and suspicious inputs", ("security", "audit")),
        "orchestration": ("Split work into tasks and coordinate specialist results", ("plan", "coordinate")),
    }

    def __init__(self) -> None:
        self._handlers: dict[str, InternalHandler] = {}

    def roles(self) -> tuple[InternalBrainRole, ...]:
        return tuple(
            InternalBrainRole(role_id, purpose, capabilities, role_id in self._handlers)
            for role_id, (purpose, capabilities) in self.ROLE_PURPOSES.items()
        )

    def register_handler(self, role_id: str, handler: InternalHandler) -> None:
        if role_id not in self.ROLE_PURPOSES:
            raise ValueError(f"unknown internal brain role: {role_id}")
        if not callable(handler):
            raise TypeError("internal brain handler must be callable")
        if role_id in self._handlers:
            raise ValueError(f"handler already registered for role: {role_id}")
        self._handlers[role_id] = handler

    def dispatch(
        self,
        role_id: str,
        request: str,
        context: dict[str, Any] | None = None,
        *,
        authorization_passed: bool = False,
        verification_passed: bool = False,
    ) -> InternalBrainDispatch:
        if role_id not in self.ROLE_PURPOSES:
            return InternalBrainDispatch(False, role_id, request, reason="unknown internal role")
        if not isinstance(request, str) or not request.strip():
            return InternalBrainDispatch(False, role_id, str(request), reason="non-empty request required")
        handler = self._handlers.get(role_id)
        if handler is None:
            return InternalBrainDispatch(False, role_id, request, reason="role exists in architecture but has no executable handler registered")
        if not authorization_passed:
            return InternalBrainDispatch(False, role_id, request, reason="upstream authorization is required before handler execution")
        if not verification_passed:
            return InternalBrainDispatch(False, role_id, request, reason="upstream request verification is required before handler execution")
        try:
            result = handler(request, dict(context or {}))
        except Exception as exc:
            return InternalBrainDispatch(False, role_id, request, reason=f"handler failed: {type(exc).__name__}: {exc}")
        return InternalBrainDispatch(True, role_id, request, result=result, reason="handler completed; output still requires task-appropriate verification")

    @staticmethod
    def creates_independent_child_brain() -> bool:
        return False

    @staticmethod
    def grants_permissions() -> bool:
        return False

    @staticmethod
    def can_modify_constitution() -> bool:
        return False

    @staticmethod
    def can_self_birth() -> bool:
        return False
