from core.brain.child_self_improvement_engine import (
    ChildSelfImprovementEngine,
    ImprovementDecision,
    ImprovementProposalStatus,
    ImprovementTarget,
)


def test_proposal_requires_mother_approval() -> None:
    engine = ChildSelfImprovementEngine()

    proposal = engine.create_proposal(
        child_brain_id="child-001",
        target=ImprovementTarget.CHILD_CODE,
        title="Improve code",
        reason="Detected weakness",
        expected_benefit="Better performance",
        expected_risk="Regression possible",
        security_impact="No authority increase",
        authority_impact="No authority change",
    )

    proposal = engine.record_tests(
        proposal.proposal_id,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    result = engine.request_mother_approval(proposal.proposal_id)

    assert result.decision == ImprovementDecision.WAIT
    assert result.proposal.status == ImprovementProposalStatus.WAITING_MOTHER
    assert engine.can_upgrade_be_executed(proposal.proposal_id) is False


def test_rejected_upgrade_is_blocked() -> None:
    engine = ChildSelfImprovementEngine()

    proposal = engine.create_proposal(
        child_brain_id="child-002",
        target=ImprovementTarget.INTERNAL_ARMY,
        title="Improve army",
        reason="Weak specialist performance",
        expected_benefit="Better specialist performance",
        expected_risk="Unexpected behavior",
        security_impact="No authority increase",
        authority_impact="No authority change",
    )

    engine.record_tests(
        proposal.proposal_id,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    engine.request_mother_approval(proposal.proposal_id)

    result = engine.record_mother_decision(
        proposal.proposal_id,
        approved=False,
    )

    assert result.decision == ImprovementDecision.REJECT
    assert engine.can_upgrade_be_executed(proposal.proposal_id) is False


def test_approved_upgrade_requires_all_gates() -> None:
    engine = ChildSelfImprovementEngine()

    proposal = engine.create_proposal(
        child_brain_id="child-003",
        target=ImprovementTarget.INTERNAL_LABOR,
        title="Improve labor",
        reason="Detected operational weakness",
        expected_benefit="Better execution planning",
        expected_risk="Regression possible",
        security_impact="No authority increase",
        authority_impact="No authority change",
    )

    engine.record_tests(
        proposal.proposal_id,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    engine.request_mother_approval(proposal.proposal_id)

    result = engine.record_mother_decision(
        proposal.proposal_id,
        approved=True,
    )

    assert result.decision == ImprovementDecision.APPROVE
    assert engine.can_upgrade_be_executed(proposal.proposal_id) is True


def test_failed_verification_blocks_approval() -> None:
    engine = ChildSelfImprovementEngine()

    proposal = engine.create_proposal(
        child_brain_id="child-004",
        target=ImprovementTarget.CHILD_REASONING,
        title="Improve reasoning",
        reason="Detected weakness",
        expected_benefit="Better reasoning",
        expected_risk="Unknown regression",
        security_impact="No authority increase",
        authority_impact="No authority change",
    )

    engine.record_tests(
        proposal.proposal_id,
        security_passed=True,
        regression_passed=False,
        verification_passed=True,
    )

    result = engine.request_mother_approval(proposal.proposal_id)

    assert result.decision == ImprovementDecision.BLOCK
    assert engine.can_upgrade_be_executed(proposal.proposal_id) is False


def test_security_invariants() -> None:
    engine = ChildSelfImprovementEngine()

    assert engine.can_child_self_authorize() is False
    assert engine.can_child_bypass_mother() is False
    assert engine.can_external_actor_authorize() is False
    assert engine.can_change_soul() is False
    assert engine.can_change_constitution() is False
    assert engine.upgrade_execution_is_separate() is True
    assert engine.creates_real_child() is False
    assert engine.activates_real_child() is False
    assert engine.executes_upgrade() is False


if __name__ == "__main__":
    test_proposal_requires_mother_approval()
    test_rejected_upgrade_is_blocked()
    test_approved_upgrade_requires_all_gates()
    test_failed_verification_blocks_approval()
    test_security_invariants()

    print("SAHIBEX CHILD SELF-IMPROVEMENT ENGINE TEST: PASS")
