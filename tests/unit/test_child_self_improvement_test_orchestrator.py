from core.brain.child_self_improvement_test_orchestrator import (
    ChildSelfImprovementTestOrchestrator,
    ImprovementGateState,
    OrchestratorDecision,
)


def all_passed_gates() -> ImprovementGateState:
    return ImprovementGateState(
        proposal_valid=True,
        risk_analysis_passed=True,
        compatibility_passed=True,
        sandbox_passed=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
        governance_passed=True,
    )


def test_all_gates_ready_for_mother():
    orchestrator = ChildSelfImprovementTestOrchestrator()

    result = orchestrator.evaluate(all_passed_gates())

    assert result.decision == OrchestratorDecision.READY_FOR_MOTHER
    assert result.failed_gates == ()
    assert result.requires_mother is True
    assert result.requires_human is False


def test_security_failure_blocks():
    orchestrator = ChildSelfImprovementTestOrchestrator()

    gates = ImprovementGateState(
        proposal_valid=True,
        risk_analysis_passed=True,
        compatibility_passed=True,
        sandbox_passed=True,
        security_passed=False,
        regression_passed=True,
        verification_passed=True,
        governance_passed=True,
    )

    result = orchestrator.evaluate(gates)

    assert result.decision == OrchestratorDecision.BLOCKED
    assert "security_passed" in result.failed_gates


def test_regression_failure_blocks():
    orchestrator = ChildSelfImprovementTestOrchestrator()

    gates = ImprovementGateState(
        proposal_valid=True,
        risk_analysis_passed=True,
        compatibility_passed=True,
        sandbox_passed=True,
        security_passed=True,
        regression_passed=False,
        verification_passed=True,
        governance_passed=True,
    )

    result = orchestrator.evaluate(gates)

    assert result.decision == OrchestratorDecision.BLOCKED
    assert "regression_passed" in result.failed_gates


def test_verification_failure_blocks():
    orchestrator = ChildSelfImprovementTestOrchestrator()

    gates = ImprovementGateState(
        proposal_valid=True,
        risk_analysis_passed=True,
        compatibility_passed=True,
        sandbox_passed=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=False,
        governance_passed=True,
    )

    result = orchestrator.evaluate(gates)

    assert result.decision == OrchestratorDecision.BLOCKED
    assert "verification_passed" in result.failed_gates


def test_governance_failure_blocks():
    orchestrator = ChildSelfImprovementTestOrchestrator()

    gates = ImprovementGateState(
        proposal_valid=True,
        risk_analysis_passed=True,
        compatibility_passed=True,
        sandbox_passed=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
        governance_passed=False,
    )

    result = orchestrator.evaluate(gates)

    assert result.decision == OrchestratorDecision.BLOCKED
    assert "governance_passed" in result.failed_gates


def test_multiple_failures_are_reported():
    orchestrator = ChildSelfImprovementTestOrchestrator()

    gates = ImprovementGateState(
        proposal_valid=False,
        risk_analysis_passed=False,
        compatibility_passed=True,
        sandbox_passed=False,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
        governance_passed=True,
    )

    result = orchestrator.evaluate(gates)

    assert result.decision == OrchestratorDecision.BLOCKED
    assert "proposal_valid" in result.failed_gates
    assert "risk_analysis_passed" in result.failed_gates
    assert "sandbox_passed" in result.failed_gates


def test_human_requirement_is_preserved():
    orchestrator = ChildSelfImprovementTestOrchestrator()

    result = orchestrator.evaluate_with_human_requirement(
        all_passed_gates(),
        human_required=True,
    )

    assert result.decision == OrchestratorDecision.READY_FOR_HUMAN
    assert result.requires_mother is True
    assert result.requires_human is True


def test_all_gates_passed():
    orchestrator = ChildSelfImprovementTestOrchestrator()

    assert orchestrator.all_gates_passed(
        all_passed_gates()
    ) is True


def test_orchestrator_never_executes():
    orchestrator = ChildSelfImprovementTestOrchestrator()

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


if __name__ == "__main__":
    test_all_gates_ready_for_mother()
    test_security_failure_blocks()
    test_regression_failure_blocks()
    test_verification_failure_blocks()
    test_governance_failure_blocks()
    test_multiple_failures_are_reported()
    test_human_requirement_is_preserved()
    test_all_gates_passed()
    test_orchestrator_never_executes()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT ORCHESTRATOR TEST: PASS"
    )
