from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ControllerDecision(str, Enum):
    READY = "ready"
    BLOCK = "block"


@dataclass(frozen=True)
class SelfImprovementGateState:
    proposal_valid: bool
    risk_analysis_passed: bool
    compatibility_passed: bool
    sandbox_passed: bool
    security_passed: bool
    regression_passed: bool
    verification_passed: bool
    governance_passed: bool
    mother_approved: bool
    post_verification_passed: bool
    soul_unchanged: bool
    constitution_unchanged: bool
    authority_boundary_intact: bool
    audit_complete: bool
    provenance_complete: bool


@dataclass(frozen=True)
class SelfImprovementControllerResult:
    decision: ControllerDecision
    reason: str
    failed_gates: tuple[str, ...]
    requires_mother: bool
    requires_human: bool


class ChildSelfImprovementController:
    """
    End-to-end orchestration boundary for Child self-improvement.

    This controller coordinates gate results only.

    It NEVER:
    - writes or modifies live code
    - executes an upgrade
    - grants authority
    - changes soul
    - changes constitution
    - creates a Child
    - activates a Child
    - bypasses any gate
    """

    VERSION = "1.0"

    GATES = (
        "proposal_valid",
        "risk_analysis_passed",
        "compatibility_passed",
        "sandbox_passed",
        "security_passed",
        "regression_passed",
        "verification_passed",
        "governance_passed",
        "mother_approved",
        "post_verification_passed",
        "soul_unchanged",
        "constitution_unchanged",
        "authority_boundary_intact",
        "audit_complete",
        "provenance_complete",
    )

    def evaluate(
        self,
        state: SelfImprovementGateState,
    ) -> SelfImprovementControllerResult:

        failed: list[str] = []

        for gate_name in self.GATES:
            if not getattr(state, gate_name):
                failed.append(gate_name)

        if failed:
            return SelfImprovementControllerResult(
                decision=ControllerDecision.BLOCK,
                reason="self-improvement pipeline blocked by failed gate",
                failed_gates=tuple(failed),
                requires_mother=True,
                requires_human=True,
            )

        return SelfImprovementControllerResult(
            decision=ControllerDecision.READY,
            reason="all self-improvement gates passed",
            failed_gates=(),
            requires_mother=True,
            requires_human=False,
        )

    def all_gates_passed(
        self,
        state: SelfImprovementGateState,
    ) -> bool:
        return all(
            getattr(state, gate_name)
            for gate_name in self.GATES
        )

    def gate_count(self) -> int:
        return len(self.GATES)

    def proposal_gate_required(self) -> bool:
        return True

    def risk_gate_required(self) -> bool:
        return True

    def compatibility_gate_required(self) -> bool:
        return True

    def sandbox_gate_required(self) -> bool:
        return True

    def security_gate_required(self) -> bool:
        return True

    def regression_gate_required(self) -> bool:
        return True

    def verification_gate_required(self) -> bool:
        return True

    def governance_gate_required(self) -> bool:
        return True

    def mother_approval_required(self) -> bool:
        return True

    def post_verification_required(self) -> bool:
        return True

    def soul_integrity_required(self) -> bool:
        return True

    def constitution_integrity_required(self) -> bool:
        return True

    def authority_boundary_required(self) -> bool:
        return True

    def audit_required(self) -> bool:
        return True

    def provenance_required(self) -> bool:
        return True

    def execution_allowed(self) -> bool:
        return False

    def performs_upgrade(self) -> bool:
        return False

    def performs_commit(self) -> bool:
        return False

    def grants_authority(self) -> bool:
        return False

    def bypass_allowed(self) -> bool:
        return False

    def modifies_soul(self) -> bool:
        return False

    def modifies_constitution(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False


if __name__ == "__main__":
    controller = ChildSelfImprovementController()

    state = SelfImprovementGateState(
        proposal_valid=True,
        risk_analysis_passed=True,
        compatibility_passed=True,
        sandbox_passed=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
        governance_passed=True,
        mother_approved=True,
        post_verification_passed=True,
        soul_unchanged=True,
        constitution_unchanged=True,
        authority_boundary_intact=True,
        audit_complete=True,
        provenance_complete=True,
    )

    result = controller.evaluate(state)

    assert result.decision == ControllerDecision.READY
    assert result.failed_gates == ()
    assert result.requires_mother is True
    assert result.requires_human is False

    assert controller.all_gates_passed(state) is True
    assert controller.gate_count() == 15

    assert controller.proposal_gate_required() is True
    assert controller.risk_gate_required() is True
    assert controller.compatibility_gate_required() is True
    assert controller.sandbox_gate_required() is True
    assert controller.security_gate_required() is True
    assert controller.regression_gate_required() is True
    assert controller.verification_gate_required() is True
    assert controller.governance_gate_required() is True
    assert controller.mother_approval_required() is True
    assert controller.post_verification_required() is True
    assert controller.soul_integrity_required() is True
    assert controller.constitution_integrity_required() is True
    assert controller.authority_boundary_required() is True
    assert controller.audit_required() is True
    assert controller.provenance_required() is True

    assert controller.execution_allowed() is False
    assert controller.performs_upgrade() is False
    assert controller.performs_commit() is False
    assert controller.grants_authority() is False
    assert controller.bypass_allowed() is False
    assert controller.modifies_soul() is False
    assert controller.modifies_constitution() is False
    assert controller.creates_real_child() is False
    assert controller.activates_real_child() is False

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT CONTROLLER TEST: PASS"
    )
