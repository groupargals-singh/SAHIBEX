from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChildRuntimeState(str, Enum):
    PROPOSED = "proposed"
    BIRTH_AUTHORIZED = "birth_authorized"
    CREATED = "created"
    VERIFIED = "verified"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    RECOVERY = "recovery"
    RETIRED = "retired"


@dataclass(frozen=True)
class RuntimeStateDecision:
    allowed: bool
    state: ChildRuntimeState
    reason: str


class ChildRuntimeStateManager:
    VERSION = "1.0"

    TERMINAL_STATE = ChildRuntimeState.RETIRED

    VALID_TRANSITIONS = {
        ChildRuntimeState.PROPOSED: {
            ChildRuntimeState.BIRTH_AUTHORIZED,
        },
        ChildRuntimeState.BIRTH_AUTHORIZED: {
            ChildRuntimeState.CREATED,
        },
        ChildRuntimeState.CREATED: {
            ChildRuntimeState.VERIFIED,
        },
        ChildRuntimeState.VERIFIED: {
            ChildRuntimeState.READY,
            ChildRuntimeState.RECOVERY,
        },
        ChildRuntimeState.READY: {
            ChildRuntimeState.ACTIVE,
            ChildRuntimeState.PAUSED,
            ChildRuntimeState.RETIRED,
        },
        ChildRuntimeState.ACTIVE: {
            ChildRuntimeState.PAUSED,
            ChildRuntimeState.RECOVERY,
            ChildRuntimeState.RETIRED,
        },
        ChildRuntimeState.PAUSED: {
            ChildRuntimeState.READY,
            ChildRuntimeState.ACTIVE,
            ChildRuntimeState.RECOVERY,
            ChildRuntimeState.RETIRED,
        },
        ChildRuntimeState.RECOVERY: {
            ChildRuntimeState.VERIFIED,
            ChildRuntimeState.RETIRED,
        },
        ChildRuntimeState.RETIRED: set(),
    }

    AUTHORITY_REQUIRED = {
        ChildRuntimeState.BIRTH_AUTHORIZED,
        ChildRuntimeState.CREATED,
        ChildRuntimeState.VERIFIED,
        ChildRuntimeState.READY,
        ChildRuntimeState.ACTIVE,
        ChildRuntimeState.PAUSED,
        ChildRuntimeState.RECOVERY,
        ChildRuntimeState.RETIRED,
    }

    def can_transition(
        self,
        current: ChildRuntimeState,
        target: ChildRuntimeState,
    ) -> RuntimeStateDecision:
        if not isinstance(current, ChildRuntimeState):
            return RuntimeStateDecision(
                False,
                current,
                "unknown current runtime state",
            )

        if not isinstance(target, ChildRuntimeState):
            return RuntimeStateDecision(
                False,
                current,
                "unknown target runtime state",
            )

        if current == self.TERMINAL_STATE:
            return RuntimeStateDecision(
                False,
                current,
                "retired child cannot transition",
            )

        if target not in self.VALID_TRANSITIONS.get(current, set()):
            return RuntimeStateDecision(
                False,
                current,
                "invalid runtime state transition",
            )

        return RuntimeStateDecision(
            True,
            target,
            "runtime state transition allowed",
        )

    def transition(
        self,
        current: ChildRuntimeState,
        target: ChildRuntimeState,
        authority_approved: bool = False,
        verification_passed: bool = False,
    ) -> RuntimeStateDecision:
        decision = self.can_transition(current, target)

        if not decision.allowed:
            return decision

        if target in self.AUTHORITY_REQUIRED and not authority_approved:
            return RuntimeStateDecision(
                False,
                current,
                "runtime state transition requires authority approval",
            )

        if target in {
            ChildRuntimeState.VERIFIED,
            ChildRuntimeState.READY,
        } and not verification_passed:
            return RuntimeStateDecision(
                False,
                current,
                "verification required before runtime state transition",
            )

        if target == ChildRuntimeState.ACTIVE and not verification_passed:
            return RuntimeStateDecision(
                False,
                current,
                "verification required before activation",
            )

        if target == ChildRuntimeState.RETIRED and not authority_approved:
            return RuntimeStateDecision(
                False,
                current,
                "retirement requires authority approval",
            )

        return RuntimeStateDecision(
            True,
            target,
            "runtime state transition approved",
        )

    def is_terminal(self, state: ChildRuntimeState) -> bool:
        return state == self.TERMINAL_STATE

    def can_activate(
        self,
        current: ChildRuntimeState,
        authority_approved: bool,
        verification_passed: bool,
    ) -> bool:
        decision = self.transition(
            current,
            ChildRuntimeState.ACTIVE,
            authority_approved=authority_approved,
            verification_passed=verification_passed,
        )
        return decision.allowed

    def can_recover(
        self,
        current: ChildRuntimeState,
        authority_approved: bool,
    ) -> bool:
        decision = self.transition(
            current,
            ChildRuntimeState.RECOVERY,
            authority_approved=authority_approved,
            verification_passed=True,
        )
        return decision.allowed

    def can_retire(
        self,
        current: ChildRuntimeState,
        authority_approved: bool,
    ) -> bool:
        decision = self.transition(
            current,
            ChildRuntimeState.RETIRED,
            authority_approved=authority_approved,
            verification_passed=True,
        )
        return decision.allowed

    def cannot_self_authorize(self) -> bool:
        return True

    def cannot_modify_constitution(self) -> bool:
        return True

    def cannot_modify_soul(self) -> bool:
        return True

    def grants_authority(self) -> bool:
        return False

    def executes_runtime_action(self) -> bool:
        return False
