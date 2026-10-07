from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BirthExecutionDecision(str, Enum):
    READY = "ready"
    DENY = "deny"


@dataclass(frozen=True)
class BirthExecutionRequest:
    proposal_id: str
    brain_id: str
    soul_id: str
    constitution_id: str
    memory_namespace: str
    security_identity: str
    audit_identity: str
    parent_brain_id: str
    purpose: str
    mother_approved: bool
    human_approved: bool
    validation_passed: bool
    security_passed: bool
    verification_passed: bool


@dataclass(frozen=True)
class BirthExecutionResult:
    allowed: bool
    decision: BirthExecutionDecision
    reason: str


class ChildBirthExecutionGate:
    VERSION = "1.0"

    def evaluate(
        self,
        request: BirthExecutionRequest,
    ) -> BirthExecutionResult:

        required_values = {
            "proposal_id": request.proposal_id,
            "brain_id": request.brain_id,
            "soul_id": request.soul_id,
            "constitution_id": request.constitution_id,
            "memory_namespace": request.memory_namespace,
            "security_identity": request.security_identity,
            "audit_identity": request.audit_identity,
            "parent_brain_id": request.parent_brain_id,
            "purpose": request.purpose,
        }

        for field_name, value in required_values.items():
            if not value:
                return BirthExecutionResult(
                    False,
                    BirthExecutionDecision.DENY,
                    f"{field_name} is required",
                )

        if not request.validation_passed:
            return BirthExecutionResult(
                False,
                BirthExecutionDecision.DENY,
                "birth validation has not passed",
            )

        if not request.security_passed:
            return BirthExecutionResult(
                False,
                BirthExecutionDecision.DENY,
                "birth security validation has not passed",
            )

        if not request.verification_passed:
            return BirthExecutionResult(
                False,
                BirthExecutionDecision.DENY,
                "birth verification has not passed",
            )

        if not request.mother_approved:
            return BirthExecutionResult(
                False,
                BirthExecutionDecision.DENY,
                "mother approval is required",
            )

        if not request.human_approved:
            return BirthExecutionResult(
                False,
                BirthExecutionDecision.DENY,
                "human approval is required",
            )

        return BirthExecutionResult(
            True,
            BirthExecutionDecision.READY,
            "child birth execution gate passed",
        )

    def can_create_child(self) -> bool:
        return False

    def can_activate_child(self) -> bool:
        return False

    def can_execute_birth(self) -> bool:
        return False

    def can_self_authorize(self) -> bool:
        return False

    def can_bypass_validation(self) -> bool:
        return False

    def can_bypass_security(self) -> bool:
        return False

    def can_bypass_verification(self) -> bool:
        return False

    def can_modify_soul(self) -> bool:
        return False

    def can_modify_constitution(self) -> bool:
        return False

    def requires_mother_approval(self) -> bool:
        return True

    def requires_human_approval(self) -> bool:
        return True

    def requires_validation(self) -> bool:
        return True

    def requires_security(self) -> bool:
        return True

    def requires_verification(self) -> bool:
        return True
