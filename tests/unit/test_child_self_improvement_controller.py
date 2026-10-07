from core.brain.child_self_improvement_controller import (
    ChildSelfImprovementController,
    ControllerDecision,
    SelfImprovementGateState,
)


def all_gates_passed() -> SelfImprovementGateState:
    return SelfImprovementGateState(
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


def test_all_gates_ready():
    controller = ChildSelfImprovementController()

    result = controller.evaluate(all_gates_passed())

    assert result.decision == ControllerDecision.READY
    assert result.failed_gates == ()
    assert result.requires_mother is True
    assert result.requires_human is False


def test_any_failed_gate_blocks():
    controller = ChildSelfImprovementController()

    state = SelfImprovementGateState(
        proposal_valid=True,
        risk_analysis_passed=True,
        compatibility_passed=True,
        sandbox_passed=True,
        security_passed=False,
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

    assert result.decision == ControllerDecision.BLOCK
    assert "security_passed" in result.failed_gates
    assert result.requires_mother is True
    assert result.requires_human is True


def test_multiple_failed_gates_are_reported():
    controller = ChildSelfImprovementController()

    state = SelfImprovementGateState(
        proposal_valid=False,
        risk_analysis_passed=False,
        compatibility_passed=True,
        sandbox_passed=True,
        security_passed=False,
        regression_passed=True,
        verification_passed=True,
        governance_passed=False,
        mother_approved=False,
        post_verification_passed=True,
        soul_unchanged=True,
        constitution_unchanged=False,
        authority_boundary_intact=False,
        audit_complete=True,
        provenance_complete=False,
    )

    result = controller.evaluate(state)

    assert result.decision == ControllerDecision.BLOCK

    assert "proposal_valid" in result.failed_gates
    assert "risk_analysis_passed" in result.failed_gates
    assert "security_passed" in result.failed_gates
    assert "governance_passed" in result.failed_gates
    assert "mother_approved" in result.failed_gates
    assert "constitution_unchanged" in result.failed_gates
    assert "authority_boundary_intact" in result.failed_gates
    assert "provenance_complete" in result.failed_gates


def test_all_gates_passed_helper():
    controller = ChildSelfImprovementController()

    assert controller.all_gates_passed(all_gates_passed()) is True


def test_gate_count():
    controller = ChildSelfImprovementController()

    assert controller.gate_count() == 15


def test_pipeline_requirements():
    controller = ChildSelfImprovementController()

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


def test_controller_cannot_execute():
    controller = ChildSelfImprovementController()

    assert controller.execution_allowed() is False
    assert controller.performs_upgrade() is False
    assert controller.performs_commit() is False


def test_controller_cannot_escalate_authority():
    controller = ChildSelfImprovementController()

    assert controller.grants_authority() is False
    assert controller.bypass_allowed() is False


def test_controller_cannot_modify_soul_or_constitution():
    controller = ChildSelfImprovementController()

    assert controller.modifies_soul() is False
    assert controller.modifies_constitution() is False


def test_controller_cannot_create_or_activate_child():
    controller = ChildSelfImprovementController()

    assert controller.creates_real_child() is False
    assert controller.activates_real_child() is False


if __name__ == "__main__":
    test_all_gates_ready()
    test_any_failed_gate_blocks()
    test_multiple_failed_gates_are_reported()
    test_all_gates_passed_helper()
    test_gate_count()
    test_pipeline_requirements()
    test_controller_cannot_execute()
    test_controller_cannot_escalate_authority()
    test_controller_cannot_modify_soul_or_constitution()
    test_controller_cannot_create_or_activate_child()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT CONTROLLER TEST: PASS"
    )
