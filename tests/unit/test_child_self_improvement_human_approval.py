from core.brain.child_self_improvement_human_approval import (
    ChildSelfImprovementHumanApproval,
    HumanApprovalDecision,
)


def make_request(
    human: ChildSelfImprovementHumanApproval,
    mother_approved=True,
    security=True,
    regression=True,
    verification=True,
):
    return human.create_request(
        proposal_id="proposal-001",
        child_brain_id="child-001",
        mother_approval_id="mother-approval-001",
        change_summary="Improve reasoning module",
        risk_summary="Low capability risk",
        security_impact="No security weakening",
        authority_impact="No authority increase",
        security_verified=security,
        regression_verified=regression,
        final_verification_passed=verification,
        mother_approved=mother_approved,
    )


def test_human_approval():
    human = ChildSelfImprovementHumanApproval()

    request = make_request(human)

    result = human.review(
        request=request,
        approved=True,
        reason="Human approved after review",
        approver_id="human-authority",
    )

    assert result.decision == HumanApprovalDecision.APPROVE
    assert human.approval_is_valid(result) is True
    assert result.record.authority_context == "human"
    assert result.record.audit_required is True
    assert result.record.immutable is True
    assert result.record.execution_granted is False


def test_human_rejection():
    human = ChildSelfImprovementHumanApproval()

    request = make_request(human)

    result = human.review(
        request=request,
        approved=False,
        reason="Human rejected the proposal",
        approver_id="human-authority",
    )

    assert result.decision == HumanApprovalDecision.REJECT
    assert human.rejection_blocks_upgrade(result) is True


def test_missing_mother_approval_blocks():
    human = ChildSelfImprovementHumanApproval()

    request = make_request(
        human,
        mother_approved=False,
    )

    result = human.review(
        request=request,
        approved=True,
        reason="Approve",
        approver_id="human-authority",
    )

    assert result.decision == HumanApprovalDecision.BLOCK


def test_security_failure_blocks():
    human = ChildSelfImprovementHumanApproval()

    request = make_request(
        human,
        security=False,
    )

    result = human.review(
        request=request,
        approved=True,
        reason="Approve",
        approver_id="human-authority",
    )

    assert result.decision == HumanApprovalDecision.BLOCK


def test_regression_failure_blocks():
    human = ChildSelfImprovementHumanApproval()

    request = make_request(
        human,
        regression=False,
    )

    result = human.review(
        request=request,
        approved=True,
        reason="Approve",
        approver_id="human-authority",
    )

    assert result.decision == HumanApprovalDecision.BLOCK


def test_verification_failure_blocks():
    human = ChildSelfImprovementHumanApproval()

    request = make_request(
        human,
        verification=False,
    )

    result = human.review(
        request=request,
        approved=True,
        reason="Approve",
        approver_id="human-authority",
    )

    assert result.decision == HumanApprovalDecision.BLOCK


def test_human_is_highest_authority():
    human = ChildSelfImprovementHumanApproval()

    assert human.human_is_highest_authority() is True
    assert human.can_child_bypass_human() is False
    assert human.can_mother_bypass_human() is False


def test_human_cannot_execute_upgrade():
    human = ChildSelfImprovementHumanApproval()

    assert human.can_execute_upgrade() is False
    assert human.grants_execution_authority() is False
    assert human.grants_permanent_ai_authority() is False


def test_human_cannot_modify_soul_or_constitution():
    human = ChildSelfImprovementHumanApproval()

    assert human.modifies_soul() is False
    assert human.modifies_constitution() is False


def test_human_cannot_create_or_activate_child():
    human = ChildSelfImprovementHumanApproval()

    assert human.creates_real_child() is False
    assert human.activates_real_child() is False


if __name__ == "__main__":
    test_human_approval()
    test_human_rejection()
    test_missing_mother_approval_blocks()
    test_security_failure_blocks()
    test_regression_failure_blocks()
    test_verification_failure_blocks()
    test_human_is_highest_authority()
    test_human_cannot_execute_upgrade()
    test_human_cannot_modify_soul_or_constitution()
    test_human_cannot_create_or_activate_child()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT HUMAN APPROVAL TEST: PASS"
    )
