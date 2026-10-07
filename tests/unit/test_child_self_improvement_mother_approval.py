from core.brain.child_self_improvement_mother_approval import (
    ChildSelfImprovementMotherApproval,
    MotherApprovalDecision,
)


def make_request(
    mother: ChildSelfImprovementMotherApproval,
    security=True,
    regression=True,
    verification=True,
):
    return mother.create_request(
        proposal_id="proposal-001",
        child_brain_id="child-001",
        proposal_summary="Improve reasoning module",
        risk_summary="Low capability risk",
        security_result=security,
        regression_result=regression,
        verification_result=verification,
        authority_impact="No authority increase",
        requested_by="child-001",
    )


def test_mother_approval():
    mother = ChildSelfImprovementMotherApproval()

    request = make_request(mother)

    result = mother.review(
        request=request,
        approved=True,
        reason="All checks passed",
        approver_id="sahibex-mother",
    )

    assert result.decision == MotherApprovalDecision.APPROVE
    assert mother.approval_is_valid(result) is True
    assert result.record.audit_required is True
    assert result.record.immutable is True
    assert result.record.execution_granted is False


def test_mother_rejection():
    mother = ChildSelfImprovementMotherApproval()

    request = make_request(mother)

    result = mother.review(
        request=request,
        approved=False,
        reason="Risk is not acceptable",
        approver_id="sahibex-mother",
    )

    assert result.decision == MotherApprovalDecision.REJECT
    assert mother.rejection_blocks_upgrade(result) is True
    assert result.record.execution_granted is False


def test_security_failure_blocks():
    mother = ChildSelfImprovementMotherApproval()

    request = make_request(
        mother,
        security=False,
    )

    result = mother.review(
        request=request,
        approved=True,
        reason="Approve",
        approver_id="sahibex-mother",
    )

    assert result.decision == MotherApprovalDecision.BLOCK
    assert mother.rejection_blocks_upgrade(result) is True


def test_regression_failure_blocks():
    mother = ChildSelfImprovementMotherApproval()

    request = make_request(
        mother,
        regression=False,
    )

    result = mother.review(
        request=request,
        approved=True,
        reason="Approve",
        approver_id="sahibex-mother",
    )

    assert result.decision == MotherApprovalDecision.BLOCK


def test_verification_failure_blocks():
    mother = ChildSelfImprovementMotherApproval()

    request = make_request(
        mother,
        verification=False,
    )

    result = mother.review(
        request=request,
        approved=True,
        reason="Approve",
        approver_id="sahibex-mother",
    )

    assert result.decision == MotherApprovalDecision.BLOCK


def test_mother_cannot_execute_upgrade():
    mother = ChildSelfImprovementMotherApproval()

    assert mother.can_execute_upgrade() is False
    assert mother.grants_execution_authority() is False
    assert mother.grants_permanent_authority() is False


def test_mother_cannot_modify_soul_or_constitution():
    mother = ChildSelfImprovementMotherApproval()

    assert mother.modifies_soul() is False
    assert mother.modifies_constitution() is False


def test_mother_cannot_create_or_activate_child():
    mother = ChildSelfImprovementMotherApproval()

    assert mother.creates_real_child() is False
    assert mother.activates_real_child() is False


def test_mother_cannot_bypass_human_authority():
    mother = ChildSelfImprovementMotherApproval()

    assert mother.can_bypass_human_authority() is False


if __name__ == "__main__":
    test_mother_approval()
    test_mother_rejection()
    test_security_failure_blocks()
    test_regression_failure_blocks()
    test_verification_failure_blocks()
    test_mother_cannot_execute_upgrade()
    test_mother_cannot_modify_soul_or_constitution()
    test_mother_cannot_create_or_activate_child()
    test_mother_cannot_bypass_human_authority()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT MOTHER APPROVAL TEST: PASS"
    )
