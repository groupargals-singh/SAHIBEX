from core.brain.child_upgrade_audit_provenance import (
    AuditDecision,
    ChildUpgradeAuditProvenance,
    UpgradeAuditEvent,
    UpgradeProvenance,
)


def valid_provenance() -> UpgradeProvenance:
    return UpgradeProvenance(
        actor_id="child-001",
        actor_type="child_brain",
        source="self_improvement_engine",
        authority_context="mother-approved",
        verification_context="all-verification-passed",
        timestamp_context="test-time",
    )


def record_valid_event(
    audit: ChildUpgradeAuditProvenance,
):
    return audit.record_event(
        transaction_id="upgrade-001",
        proposal_id="proposal-001",
        child_brain_id="child-001",
        event=UpgradeAuditEvent.COMMITTED,
        version_before="1.0",
        version_after="1.1",
        change_summary="Reasoning improvement",
        reason="Improve reasoning consistency",
        security_result="passed",
        regression_result="passed",
        verification_result="passed",
        approval_result="mother-approved",
        provenance=valid_provenance(),
    )


def test_valid_audit_record() -> None:
    audit = ChildUpgradeAuditProvenance()

    result = record_valid_event(audit)

    assert result.decision == AuditDecision.ACCEPT
    assert result.record.immutable is True
    assert result.record.version_before == "1.0"
    assert result.record.version_after == "1.1"


def test_missing_provenance_is_blocked() -> None:
    audit = ChildUpgradeAuditProvenance()

    provenance = UpgradeProvenance(
        actor_id="",
        actor_type="child_brain",
        source="engine",
        authority_context="approved",
        verification_context="passed",
        timestamp_context="time",
    )

    result = audit.record_event(
        transaction_id="upgrade-002",
        proposal_id="proposal-002",
        child_brain_id="child-002",
        event=UpgradeAuditEvent.PROPOSED,
        version_before="1.0",
        version_after="1.1",
        change_summary="Test",
        reason="Test reason",
        security_result="unknown",
        regression_result="unknown",
        verification_result="unknown",
        approval_result="pending",
        provenance=provenance,
    )

    assert result.decision == AuditDecision.BLOCK
    assert result.record.event == UpgradeAuditEvent.BLOCKED


def test_empty_change_summary_is_blocked() -> None:
    audit = ChildUpgradeAuditProvenance()

    provenance = valid_provenance()

    result = audit.record_event(
        transaction_id="upgrade-003",
        proposal_id="proposal-003",
        child_brain_id="child-003",
        event=UpgradeAuditEvent.VALIDATED,
        version_before="1.0",
        version_after="1.1",
        change_summary="",
        reason="Test reason",
        security_result="passed",
        regression_result="passed",
        verification_result="passed",
        approval_result="approved",
        provenance=provenance,
    )

    assert result.decision == AuditDecision.BLOCK


def test_records_are_immutable() -> None:
    audit = ChildUpgradeAuditProvenance()

    result = record_valid_event(audit)

    audit_id = result.record.audit_id

    assert audit.audit_record_is_immutable(audit_id) is True
    assert audit.get_record(audit_id).immutable is True


def test_audit_does_not_grant_authority() -> None:
    audit = ChildUpgradeAuditProvenance()

    assert audit.audit_read_grants_authority() is False
    assert audit.external_actor_is_audit_authority() is False
    assert audit.fabricated_provenance_is_allowed() is False
    assert audit.audit_tampering_is_allowed() is False


def test_audit_layer_does_not_execute() -> None:
    audit = ChildUpgradeAuditProvenance()

    assert audit.creates_real_child() is False
    assert audit.activates_real_child() is False
    assert audit.executes_upgrade() is False


if __name__ == "__main__":
    test_valid_audit_record()
    test_missing_provenance_is_blocked()
    test_empty_change_summary_is_blocked()
    test_records_are_immutable()
    test_audit_does_not_grant_authority()
    test_audit_layer_does_not_execute()

    print("SAHIBEX CHILD UPGRADE AUDIT & PROVENANCE TEST: PASS")
