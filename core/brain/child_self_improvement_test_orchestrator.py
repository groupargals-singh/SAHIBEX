from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OrchestratorDecision(str, Enum):
    READY_FOR_MOTHER = "ready_for_mother"
    READY_FOR_HUMAN = "ready_for_human"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ImprovementGateState:
    proposal_valid: bool
    risk_analysis_passed: bool
    compatibility_passed: bool
    sandbox_passed: bool
    security_passed: bool
    regression_passed: bool
    verification_passed: bool
    governance_passed: bool


@dataclass(frozen=True)
class OrchestratorResult:
    decision: OrchestratorDecision
    reason: str
    failed_gates: tuple[str, ...]
    requires_mother: bool
    requires_human: bool


class ChildSelfImprovementTestOrchestrator:
    """
    Pre-upgrade gate orchestrator.

    This layer:
    - consolidates improvement safety gates
    - checks that every required gate passed
    - identifies missing/failed gates
    - determines Mother/Human review requirement

    This layer NEVER:
    - executes upgrades
    - modifies code
    - modifies soul
    - modifies constitution
    - grants authority
    - creates or activates children
    """

    VERSION = "1.0"

    REQUIRED_GATES = (
        "proposal_valid",
        "risk_analysis_passed",
        "compatibility_passed",
        "sandbox_passed",
        "security_passed",
        "regression_passed",
        "verification_passed",
        "governance_passed",
    )

    def evaluate(
        self,
        gates: ImprovementGateState,
    ) -> OrchestratorResult:

        failed: list[str] = []

        for gate_name in self.REQUIRED_GATES:
            if not getattr(gates, gate_name):
                failed.append(gate_name)

        if failed:
            return OrchestratorResult(
                decision=OrchestratorDecision.BLOCKED,
                reason="one or more required improvement gates failed",
                failed_gates=tuple(failed),
                requires_mother=True,
                requires_human=True,
            )

        return OrchestratorResult(
            decision=OrchestratorDecision.READY_FOR_MOTHER,
            reason="all pre-upgrade gates passed; Mother approval is required",
            failed_gates=(),
            requires_mother=True,
            requires_human=False,
        )

    def evaluate_with_human_requirement(
        self,
        gates: ImprovementGateState,
        human_required: bool,
    ) -> OrchestratorResult:

        result = self.evaluate(gates)

        if result.decision == OrchestratorDecision.BLOCKED:
            return result

        if human_required:
            return OrchestratorResult(
                decision=OrchestratorDecision.READY_FOR_HUMAN,
                reason="all gates passed; Human approval is required",
                failed_gates=(),
                requires_mother=True,
                requires_human=True,
            )

        return result

    def all_gates_passed(
        self,
        gates: ImprovementGateState,
    ) -> bool:
        return all(
            getattr(gates, gate_name)
            for gate_name in self.REQUIRED_GATES
        )

    def execution_allowed(self) -> bool:
        return False

    def upgrade_execution_allowed(self) -> bool:
        return False

    def mother_approval_granted(self) -> bool:
        return False

    def human_approval_granted(self) -> bool:
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
    orchestrator = ChildSelfImprovementTestOrchestrator()

    gates = ImprovementGateState(
        proposal_valid=True,
        risk_analysis_passed=True,
        compatibility_passed=True,
        sandbox_passed=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
        governance_passed=True,
    )

    result = orchestrator.evaluate(gates)

    assert result.decision == OrchestratorDecision.READY_FOR_MOTHER
    assert result.failed_gates == ()
    assert result.requires_mother is True
    assert result.requires_human is False

    assert orchestrator.all_gates_passed(gates) is True
    assert orchestrator.execution_allowed() is False
    assert orchestrator.upgrade_execution_allowed() is False
    assert orchestrator.mother_approval_granted() is False
    assert orchestrator.human_approval_granted() is False
    assert orchestrator.grants_authority() is False
    assert orchestrator.bypass_allowed() is False
    assert orchestrator.modifies_soul() is False
    assert orchestrator.modifies_constitution() is False
    assert orchestrator.creates_real_child() is False
    assert orchestrator.activates_real_child() is False

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT ORCHESTRATOR TEST: PASS"
    )
