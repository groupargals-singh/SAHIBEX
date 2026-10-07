from core.brain.child_self_improvement_audit_integration import (
    AuditEvent,
    AuditIntegrationRequest,
    AuditProvenance,
    AuditDecision,
    ChildSelfImprovementAuditIntegration,
)


def make_provenance():
    return AuditProvenance(
        actor_id="actor-001",
        actor_type="child_brain",
        source="self_improvement",
        authority_context="human_approved",
        verification_context="verified",
        timestamp_context="timestamp",
    )


def make_request(**overrides):
    values = {
        "audit_id": "audit-001",
        "transaction_id": "transaction-001",
        "proposal_id": "proposal-001",
        "child_brain_id": "child-001",
        "event": AuditEvent.UPGRADE_COMMITTED,
        "version_before": "1.0",
        "version_after": "1.1",
        "change_summary": "test upgrade",
        "security_verified": True,
        "verification_passed": True,
        "provenance": make_provenance(),
        "immutable": True,
    }

    values.update(overrides)
    return AuditIntegrationRequest(**values)


def test_valid_audit():
    integration = ChildSelfImprovementAuditIntegration()

    result = integration.validate(make_request())

    assert result.decision == AuditDecision.ACCEPT
    assert result.audit_complete is True
    assert result.provenance_complete is True


def test_missing_audit_id_blocks():
    integration = ChildSelfImprovementAuditIntegration()

    result = integration.validate(
        make_request(audit_id="")
    )

    assert result.decision == AuditDecision.BLOCK


def test_same_version_blocks():
    integration = ChildSelfImprovementAuditIntegration()

    result = integration.validate(
        make_request(version_after="1.0")
    )

    assert result.decision == AuditDecision.BLOCK


def test_security_failure_blocks():
    integration = ChildSelfImprovementAuditIntegration()

    result = integration.validate(
        make_request(security_verified=False)
    )

    assert result.decision == AuditDecision.BLOCK


def test_verification_failure_blocks():
    integration = ChildSelfImprovementAuditIntegration()

    result = integration.validate(
        make_request(verification_passed=False)
    )

    assert result.decision == AuditDecision.BLOCK


def test_missing_provenance_blocks():
    integration = ChildSelfImprovementAuditIntegration()

    result = integration.validate(
        make_request(provenance=None)
    )

    assert result.decision == AuditDecision.BLOCK


def test_incomplete_provenance_blocks():
    integration = ChildSelfImprovementAuditIntegration()

    provenance = AuditProvenance(
        actor_id="",
        actor_type="child_brain",
        source="self_improvement",
        authority_context="human_approved",
        verification_context="verified",
        timestamp_context="timestamp",
    )

    result = integration.validate(
        make_request(provenance=provenance)
    )

    assert result.decision == AuditDecision.BLOCK


def test_mutable_audit_blocks():
    integration = ChildSelfImprovementAuditIntegration()

    result = integration.validate(
        make_request(immutable=False)
    )

    assert result.decision == AuditDecision.BLOCK


def test_audit_failure_blocks_commit():
    integration = ChildSelfImprovementAuditIntegration()

    assert integration.audit_failure_blocks_commit() is True


def test_provenance_failure_blocks_commit():
    integration = ChildSelfImprovementAuditIntegration()

    assert integration.provenance_failure_blocks_commit() is True


def test_no_authority_grant():
    integration = ChildSelfImprovementAuditIntegration()

    assert integration.grants_authority() is False


def test_no_execution():
    integration = ChildSelfImprovementAuditIntegration()

    assert integration.executes_upgrade() is False


def test_soul_constitution_protected():
    integration = ChildSelfImprovementAuditIntegration()

    assert integration.modifies_soul() is False
    assert integration.modifies_constitution() is False


def test_no_child_creation_or_activation():
    integration = ChildSelfImprovementAuditIntegration()

    assert integration.creates_real_child() is False
    assert integration.activates_real_child() is False


if __name__ == "__main__":
    test_valid_audit()
    test_missing_audit_id_blocks()
    test_same_version_blocks()
    test_security_failure_blocks()
    test_verification_failure_blocks()
    test_missing_provenance_blocks()
    test_incomplete_provenance_blocks()
    test_mutable_audit_blocks()
    test_audit_failure_blocks_commit()
    test_provenance_failure_blocks_commit()
    test_no_authority_grant()
    test_no_execution()
    test_soul_constitution_protected()
    test_no_child_creation_or_activation()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT AUDIT INTEGRATION TEST: PASS"
    )
