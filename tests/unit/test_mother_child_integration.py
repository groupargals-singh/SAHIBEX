from core.brain.mother_child_command_router import (
    CommandType,
    MotherChildCommand,
    MotherChildCommandRouter,
    CommandRouteDecision,
)

from core.brain.mother_child_authority_bridge import (
    AuthorityRequestType,
    ChildAuthorityRequest,
    MotherChildAuthorityBridge,
    AuthorityDecision,
)

from core.brain.mother_child_approval_controller import (
    ApprovalRequest,
    MotherChildApprovalController,
    ApprovalStatus,
    ApprovalDecision,
)

from core.brain.mother_child_result_audit import (
    AuditProvenance,
    MotherChildResult,
    MotherChildResultAudit,
    ResultStatus,
    ResultDecision,
)


def main() -> None:
    router = MotherChildCommandRouter()
    authority = MotherChildAuthorityBridge()
    approval = MotherChildApprovalController()
    audit = MotherChildResultAudit()

    child_id = "child-brain-integration-001"

    # =========================================================
    # 1. Autonomous cognitive command
    # =========================================================
    cognitive_command = MotherChildCommand(
        command_id="command-001",
        child_brain_id=child_id,
        command_type=CommandType.RESEARCH,
        payload="research AI security",
    )

    route_result = router.route(cognitive_command)

    assert route_result.decision == CommandRouteDecision.ROUTE
    assert route_result.allowed is True

    # =========================================================
    # 2. Protected command requires authority
    # =========================================================
    protected_command = MotherChildCommand(
        command_id="command-002",
        child_brain_id=child_id,
        command_type=CommandType.PROTECTED_REQUEST,
        payload="write verified result",
    )

    route_result = router.route(protected_command)

    assert (
        route_result.decision
        == CommandRouteDecision.REQUIRE_AUTHORITY
    )
    assert route_result.allowed is False

    # =========================================================
    # 3. Authority request
    # =========================================================
    authority_request = ChildAuthorityRequest(
        request_id="authority-001",
        child_brain_id=child_id,
        request_type=AuthorityRequestType.PROTECTED_ACTION,
        purpose="write verified research result",
    )

    authority_result = authority.evaluate(
        authority_request
    )

    assert (
        authority_result.decision
        == AuthorityDecision.REQUIRE_MOTHER
    )

    # =========================================================
    # 4. Create approval request
    # =========================================================
    approval_request = ApprovalRequest(
        request_id="approval-001",
        child_brain_id=child_id,
        purpose="write verified research result",
        requires_human=False,
    )

    approval_create_result = approval.create_request(
        approval_request
    )

    assert approval_create_result.allowed is True
    assert approval_create_result.record is not None
    assert (
        approval_create_result.record.status
        == ApprovalStatus.PENDING
    )

    # =========================================================
    # 5. Mother approval
    # =========================================================
    approval_result = approval.decide(
        approval_request,
        mother_approved=True,
        human_approved=False,
    )

    assert (
        approval_result.decision
        == ApprovalDecision.APPROVED
    )
    assert approval_result.allowed is True

    # =========================================================
    # 6. Result + audit
    # =========================================================
    result = MotherChildResult(
        request_id="approval-001",
        child_brain_id=child_id,
        status=ResultStatus.APPROVED,
        action="write verified research result",
        reason="mother approved protected action",
    )

    provenance = AuditProvenance(
        event_id="audit-001",
        actor_id="sahibex-mother",
        source="mother-child-approval-controller",
        authority_context="mother-approved",
        verification_context="verified",
        timestamp_context="integration-test",
    )

    audit_result = audit.record(
        result,
        provenance,
    )

    assert audit_result.allowed is True
    assert (
        audit_result.decision
        == ResultDecision.RECORDED
    )
    assert audit_result.record is not None

    # =========================================================
    # 7. Sensitive action requires Human approval
    # =========================================================
    sensitive_request = ChildAuthorityRequest(
        request_id="authority-002",
        child_brain_id=child_id,
        request_type=AuthorityRequestType.CONSTITUTIONAL_CHANGE,
        purpose="propose constitutional change",
    )

    sensitive_result = authority.evaluate(
        sensitive_request,
        mother_approved=True,
        human_approved=False,
    )

    assert (
        sensitive_result.decision
        == AuthorityDecision.REQUIRE_HUMAN
    )

    # =========================================================
    # 8. Rejection cannot be bypassed
    # =========================================================
    rejected_request = ApprovalRequest(
        request_id="approval-002",
        child_brain_id=child_id,
        purpose="protected operation",
        requires_human=False,
    )

    rejected_create_result = approval.create_request(
        rejected_request
    )

    assert rejected_create_result.allowed is True
    assert rejected_create_result.record is not None
    assert (
        rejected_create_result.record.status
        == ApprovalStatus.PENDING
    )

    rejected_result = approval.decide(
        rejected_request,
        mother_approved=False,
        human_approved=False,
    )

    assert (
        rejected_result.decision
        == ApprovalDecision.REJECTED
    )
    assert rejected_result.allowed is False

    # =========================================================
    # 9. Security / authority invariants
    # =========================================================
    assert not approval.can_child_approve()
    assert not approval.can_child_reject()
    assert not approval.can_child_self_approve()
    assert not approval.can_override_rejection()

    assert not audit.can_audit_grant_authority()
    assert not audit.can_child_modify_record()
    assert not audit.can_external_model_modify_record()
    assert not audit.can_tool_modify_record()
    assert not audit.can_execute_action()

    # =========================================================
    # 10. Fail-closed invariants
    # =========================================================
    assert approval.fails_closed()
    assert audit.fails_closed()
    assert audit.requires_provenance()
    assert audit.requires_verification_context()

    # =========================================================
    # 11. Version integrity
    # =========================================================
    assert router.VERSION == "1.0"
    assert authority.VERSION == "1.0"
    assert approval.VERSION == "1.0"
    assert audit.VERSION == "1.0"

    print("SAHIBEX MOTHER CHILD INTEGRATION TEST: PASS")


if __name__ == "__main__":
    main()
