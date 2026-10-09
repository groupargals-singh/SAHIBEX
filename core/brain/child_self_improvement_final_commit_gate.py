from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from security.audit.child_self_improvement_audit_store import (
    ChildSelfImprovementAuditStore,
)


class FinalCommitDecision(str, Enum):
    READY = "ready"
    BLOCK = "block"


@dataclass(frozen=True)
class FinalCommitGateState:
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
    human_approved: bool = False


@dataclass(frozen=True)
class FinalCommitResult:
    decision: FinalCommitDecision
    reason: str
    failed_gates: tuple[str, ...]
    requires_mother: bool
    requires_human: bool


class ChildSelfImprovementFinalCommitGate:
    """
    Final commit authorization boundary for Child self-improvement.

    This gate combines all required pre-commit conditions.

    It NEVER:
    - executes an upgrade
    - modifies live code
    - grants authority
    - changes soul
    - changes constitution
    - creates a Child
    - activates a Child
    """

    VERSION = "1.1"

    REQUIRED_GATES = (
        "proposal_valid",
        "risk_analysis_passed",
        "compatibility_passed",
        "sandbox_passed",
        "security_passed",
        "regression_passed",
        "verification_passed",
        "governance_passed",
        "mother_approved",
        "human_approved",
        "post_verification_passed",
        "soul_unchanged",
        "constitution_unchanged",
        "authority_boundary_intact",
        "audit_complete",
        "provenance_complete",
    )

    def __init__(
        self,
        *,
        audit_store: ChildSelfImprovementAuditStore | None = None,
    ) -> None:
        if audit_store is not None and not isinstance(
            audit_store, ChildSelfImprovementAuditStore
        ):
            raise TypeError("audit_store must be ChildSelfImprovementAuditStore or None")
        self.audit_store = audit_store

    def evaluate_persisted(
        self,
        state: FinalCommitGateState,
        *,
        audit_id: str,
        expected_child_brain_id: str,
        expected_proposal_id: str,
        expected_version_before: str,
        expected_version_after: str,
    ) -> FinalCommitResult:
        """Require a chain-valid audit bound to this exact child/proposal/version."""
        expected_binding = {
            "child_brain_id": expected_child_brain_id,
            "proposal_id": expected_proposal_id,
            "version_before": expected_version_before,
            "version_after": expected_version_after,
        }
        if any(
            not isinstance(value, str) or not value.strip()
            for value in expected_binding.values()
        ):
            return FinalCommitResult(
                decision=FinalCommitDecision.BLOCK,
                reason="complete audit context binding is required",
                failed_gates=("audit_context_binding",),
                requires_mother=True,
                requires_human=True,
            )
        if self.audit_store is None:
            return FinalCommitResult(
                decision=FinalCommitDecision.BLOCK,
                reason="persistent audit store is not configured",
                failed_gates=("audit_record_persisted", "audit_chain_valid"),
                requires_mother=True,
                requires_human=True,
            )
        if not self.audit_store.verify_chain():
            return FinalCommitResult(
                decision=FinalCommitDecision.BLOCK,
                reason="persistent audit hash chain is invalid",
                failed_gates=("audit_chain_valid",),
                requires_mother=True,
                requires_human=True,
            )
        event = self.audit_store.get_event(audit_id)
        if event is None:
            return FinalCommitResult(
                decision=FinalCommitDecision.BLOCK,
                reason="required persistent audit record is missing",
                failed_gates=("audit_record_persisted",),
                requires_mother=True,
                requires_human=True,
            )
        payload = event.get("payload", {})
        if any(
            payload.get(key) != value
            for key, value in expected_binding.items()
        ):
            return FinalCommitResult(
                decision=FinalCommitDecision.BLOCK,
                reason="persistent audit record does not match requested commit context",
                failed_gates=("audit_context_binding",),
                requires_mother=True,
                requires_human=True,
            )
        if (
            payload.get("decision") != "accept"
            or payload.get("audit_complete") is not True
            or payload.get("provenance_complete") is not True
        ):
            return FinalCommitResult(
                decision=FinalCommitDecision.BLOCK,
                reason="persistent audit decision/provenance is not accepted",
                failed_gates=("audit_complete", "provenance_complete"),
                requires_mother=True,
                requires_human=True,
            )
        return self.evaluate(
            replace(
                state,
                audit_complete=state.audit_complete and payload["audit_complete"],
                provenance_complete=(
                    state.provenance_complete and payload["provenance_complete"]
                ),
            )
        )

    def evaluate(
        self,
        state: FinalCommitGateState,
    ) -> FinalCommitResult:

        failed: list[str] = []

        for gate_name in self.REQUIRED_GATES:
            if not getattr(state, gate_name):
                failed.append(gate_name)

        if failed:
            return FinalCommitResult(
                decision=FinalCommitDecision.BLOCK,
                reason="one or more final commit gates failed",
                failed_gates=tuple(failed),
                requires_mother=True,
                requires_human=True,
            )

        return FinalCommitResult(
            decision=FinalCommitDecision.READY,
            reason="all final commit gates passed",
            failed_gates=(),
            requires_mother=True,
            requires_human=False,
        )

    def all_gates_passed(
        self,
        state: FinalCommitGateState,
    ) -> bool:
        return all(
            getattr(state, gate_name)
            for gate_name in self.REQUIRED_GATES
        )

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
    gate = ChildSelfImprovementFinalCommitGate()

    state = FinalCommitGateState(
        proposal_valid=True,
        risk_analysis_passed=True,
        compatibility_passed=True,
        sandbox_passed=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
        governance_passed=True,
        mother_approved=True,
        human_approved=True,
        post_verification_passed=True,
        soul_unchanged=True,
        constitution_unchanged=True,
        authority_boundary_intact=True,
        audit_complete=True,
        provenance_complete=True,
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.READY
    assert result.failed_gates == ()
    assert result.requires_mother is True
    assert result.requires_human is False

    assert gate.all_gates_passed(state) is True

    assert gate.proposal_gate_required() is True
    assert gate.risk_gate_required() is True
    assert gate.compatibility_gate_required() is True
    assert gate.sandbox_gate_required() is True
    assert gate.security_gate_required() is True
    assert gate.regression_gate_required() is True
    assert gate.verification_gate_required() is True
    assert gate.governance_gate_required() is True
    assert gate.mother_approval_required() is True
    assert gate.post_verification_required() is True
    assert gate.soul_integrity_required() is True
    assert gate.constitution_integrity_required() is True
    assert gate.authority_boundary_required() is True
    assert gate.audit_required() is True
    assert gate.provenance_required() is True

    assert gate.execution_allowed() is False
    assert gate.performs_commit() is False
    assert gate.grants_authority() is False
    assert gate.bypass_allowed() is False
    assert gate.modifies_soul() is False
    assert gate.modifies_constitution() is False
    assert gate.creates_real_child() is False
    assert gate.activates_real_child() is False

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT FINAL COMMIT GATE TEST: PASS"
    )
