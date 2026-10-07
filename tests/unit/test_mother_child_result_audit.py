from core.brain.mother_child_result_audit import (
    AuditProvenance,
    MotherChildResult,
    MotherChildResultAudit,
    ResultAuditOutcome,
    ResultDecision,
    ResultStatus,
)


def main() -> None:
    audit = MotherChildResultAudit()

    result = MotherChildResult(
        request_id="request-001",
        child_brain_id="child-brain-001",
        status=ResultStatus.APPROVED,
        action="write verified research result",
        reason="mother approved protected action",
    )

    provenance = AuditProvenance(
        event_id="event-001",
        actor_id="sahibex-mother",
        source="mother-child-authority-bridge",
        authority_context="mother-approved",
        verification_context="verified",
        timestamp_context="test-timestamp",
    )

    outcome = audit.record(
        result,
        provenance,
    )

    assert isinstance(outcome, ResultAuditOutcome)
    assert outcome.allowed is True
    assert outcome.decision == ResultDecision.RECORDED
    assert outcome.record is not None

    assert outcome.record.result.request_id == "request-001"
    assert (
        outcome.record.result.child_brain_id
        == "child-brain-001"
    )
    assert (
        outcome.record.provenance.actor_id
        == "sahibex-mother"
    )

    # Missing result identity
    invalid_result = MotherChildResult(
        request_id="",
        child_brain_id="child-brain-001",
        status=ResultStatus.REJECTED,
        action="test",
        reason="rejected",
    )

    outcome = audit.record(
        invalid_result,
        provenance,
    )

    assert outcome.allowed is False
    assert outcome.decision == ResultDecision.DENIED

    # Missing provenance
    invalid_provenance = AuditProvenance(
        event_id="",
        actor_id="sahibex-mother",
        source="test",
        authority_context="approved",
        verification_context="verified",
        timestamp_context="test-timestamp",
    )

    outcome = audit.record(
        result,
        invalid_provenance,
    )

    assert outcome.allowed is False
    assert outcome.decision == ResultDecision.DENIED

    # Missing verification context
    invalid_provenance = AuditProvenance(
        event_id="event-002",
        actor_id="sahibex-mother",
        source="test",
        authority_context="approved",
        verification_context="",
        timestamp_context="test-timestamp",
    )

    outcome = audit.record(
        result,
        invalid_provenance,
    )

    assert outcome.allowed is False

    # Critical audit boundaries
    assert not audit.can_audit_grant_authority()
    assert not audit.can_child_modify_record()
    assert not audit.can_external_model_modify_record()
    assert not audit.can_tool_modify_record()
    assert not audit.can_hide_event()
    assert not audit.can_fabricate_event()
    assert not audit.can_execute_action()

    assert audit.requires_provenance()
    assert audit.requires_verification_context()
    assert audit.fails_closed()

    print("SAHIBEX MOTHER CHILD RESULT AUDIT TEST: PASS")


if __name__ == "__main__":
    main()
