from core.brain.mother_child_approval_controller import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    MotherChildApprovalController,
)


def main() -> None:
    controller = MotherChildApprovalController()

    # ---------------------------------------------------------
    # 1. Create pending request
    # ---------------------------------------------------------
    request = ApprovalRequest(
        request_id="approval-001",
        child_brain_id="child-brain-001",
        purpose="write verified research result",
        requires_human=False,
    )

    result = controller.create_request(request)

    assert result.allowed is True
    assert result.decision == ApprovalDecision.WAITING
    assert result.record is not None
    assert result.record.status == ApprovalStatus.PENDING
    assert result.record.mother_approved is False

    # ---------------------------------------------------------
    # 2. Mother rejects
    # ---------------------------------------------------------
    result = controller.decide(
        request,
        mother_approved=False,
    )

    assert result.allowed is False
    assert result.decision == ApprovalDecision.REJECTED
    assert result.record is not None
    assert result.record.status == ApprovalStatus.REJECTED

    # ---------------------------------------------------------
    # 3. Mother approves
    # ---------------------------------------------------------
    result = controller.decide(
        request,
        mother_approved=True,
    )

    assert result.allowed is True
    assert result.decision == ApprovalDecision.APPROVED
    assert result.record is not None
    assert result.record.status == ApprovalStatus.APPROVED
    assert result.record.mother_approved is True

    # ---------------------------------------------------------
    # 4. Sensitive request requires Human
    # ---------------------------------------------------------
    sensitive_request = ApprovalRequest(
        request_id="approval-002",
        child_brain_id="child-brain-001",
        purpose="financial operation",
        requires_human=True,
    )

    result = controller.decide(
        sensitive_request,
        mother_approved=True,
        human_approved=False,
    )

    assert result.allowed is False
    assert result.decision == ApprovalDecision.REJECTED
    assert result.record is not None
    assert result.record.mother_approved is True
    assert result.record.human_approved is False

    # ---------------------------------------------------------
    # 5. Sensitive request with both approvals
    # ---------------------------------------------------------
    result = controller.decide(
        sensitive_request,
        mother_approved=True,
        human_approved=True,
    )

    assert result.allowed is True
    assert result.decision == ApprovalDecision.APPROVED
    assert result.record is not None
    assert result.record.status == ApprovalStatus.APPROVED
    assert result.record.mother_approved is True
    assert result.record.human_approved is True

    # ---------------------------------------------------------
    # 6. Missing request identity
    # ---------------------------------------------------------
    invalid_request = ApprovalRequest(
        request_id="",
        child_brain_id="child-brain-001",
        purpose="test",
        requires_human=False,
    )

    result = controller.create_request(invalid_request)

    assert result.allowed is False
    assert result.decision == ApprovalDecision.DENIED

    # ---------------------------------------------------------
    # 7. Missing child identity
    # ---------------------------------------------------------
    invalid_request = ApprovalRequest(
        request_id="approval-003",
        child_brain_id="",
        purpose="test",
        requires_human=False,
    )

    result = controller.create_request(invalid_request)

    assert result.allowed is False

    # ---------------------------------------------------------
    # 8. Missing purpose
    # ---------------------------------------------------------
    invalid_request = ApprovalRequest(
        request_id="approval-004",
        child_brain_id="child-brain-001",
        purpose="",
        requires_human=False,
    )

    result = controller.create_request(invalid_request)

    assert result.allowed is False

    # ---------------------------------------------------------
    # 9. Critical authority boundaries
    # ---------------------------------------------------------
    assert not controller.can_child_approve()
    assert not controller.can_child_reject()
    assert not controller.can_child_self_approve()
    assert not controller.can_override_rejection()
    assert not controller.can_external_model_decide()
    assert not controller.can_tool_decide()
    assert not controller.can_execute_action()

    assert controller.requires_mother_decision()
    assert controller.requires_human_when_sensitive()
    assert controller.fails_closed()

    print("SAHIBEX MOTHER CHILD APPROVAL CONTROLLER TEST: PASS")


if __name__ == "__main__":
    main()
