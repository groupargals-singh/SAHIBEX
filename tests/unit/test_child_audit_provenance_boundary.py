from core.brain.child_audit_provenance_boundary import (
    AuditActor,
    AuditDecision,
    AuditOperation,
    ChildAuditProvenanceBoundary,
)


def main() -> None:
    boundary = ChildAuditProvenanceBoundary

    # Valid audit recording.
    for operation in boundary.RECORD_OPERATIONS:
        result = boundary.decide(
            AuditActor.CHILD_BRAIN,
            operation,
            provenance_valid=True,
            immutable_record=True,
        )

        assert result.allowed
        assert result.decision == AuditDecision.ALLOW_RECORD
        assert result.provenance_required
        assert result.immutable_required
        assert not result.authority_granted

    # Invalid provenance blocks audit.
    result = boundary.decide(
        AuditActor.CHILD_BRAIN,
        AuditOperation.RECORD_ACTION,
        provenance_valid=False,
        immutable_record=True,
    )

    assert not result.allowed
    assert result.decision == AuditDecision.DENY

    # Mutable records are rejected.
    result = boundary.decide(
        AuditActor.CHILD_BRAIN,
        AuditOperation.RECORD_ACTION,
        provenance_valid=True,
        immutable_record=False,
    )

    assert not result.allowed
    assert result.decision == AuditDecision.DENY

    # Reading audit does not grant authority.
    result = boundary.decide(
        AuditActor.CHILD_BRAIN,
        AuditOperation.READ_AUDIT,
    )

    assert result.allowed
    assert result.decision == AuditDecision.ALLOW_READ
    assert not result.authority_granted

    # Unauthorized tampering is denied.
    for operation in boundary.DESTRUCTIVE_OPERATIONS:
        result = boundary.decide(
            AuditActor.CHILD_BRAIN,
            operation,
            provenance_valid=True,
            authority_approved=False,
        )

        assert not result.allowed
        assert result.decision == AuditDecision.DENY
        assert not result.authority_granted

    # External actors cannot become audit authority.
    for actor in boundary.EXTERNAL_ACTORS:
        result = boundary.decide(
            actor,
            AuditOperation.MODIFY_AUDIT,
            provenance_valid=True,
            authority_approved=True,
        )

        assert not result.allowed
        assert result.decision == AuditDecision.DENY

    # Authorized audit administration.
    result = boundary.decide(
        AuditActor.SAHIBEX_MOTHER,
        AuditOperation.MODIFY_AUDIT,
        authority_approved=True,
        provenance_valid=True,
    )

    assert result.allowed
    assert result.decision == AuditDecision.REQUIRE_AUTHORITY
    assert result.authority_granted

    # Constitutional guarantees.
    assert boundary.every_record_requires_provenance()
    assert boundary.every_record_requires_immutable_storage()
    assert boundary.actor_identity_is_required()
    assert boundary.source_origin_is_required()
    assert boundary.authority_context_is_required()
    assert boundary.verification_context_is_required()
    assert boundary.timestamp_context_is_required()

    assert not boundary.audit_can_grant_authority()
    assert not boundary.external_actor_can_be_audit_authority()
    assert not boundary.audit_tampering_without_authority_is_allowed()
    assert not boundary.hidden_event_is_valid()
    assert not boundary.fabricated_event_is_valid()
    assert not boundary.invalid_provenance_can_be_committed()

    assert boundary.missing_provenance_fails_closed()
    assert boundary.audit_failure_blocks_commit()

    assert not boundary.creates_child_brain()
    assert not boundary.activates_child_brain()
    assert not boundary.executes_actions()

    print("SAHIBEX CHILD AUDIT & PROVENANCE BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
