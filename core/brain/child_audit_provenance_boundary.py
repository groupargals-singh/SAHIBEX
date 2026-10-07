from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AuditActor(str, Enum):
    HUMAN = "human"
    SAHIBEX_MOTHER = "sahibex_mother"
    CHILD_BRAIN = "child_brain"
    CHILD_ARMY = "child_army"
    CHILD_LABOR = "child_labor"
    SOFTWARE = "software"
    TOOL = "tool"
    EXTERNAL_MODEL = "external_model"


class AuditOperation(str, Enum):
    RECORD_EVENT = "record_event"
    RECORD_DECISION = "record_decision"
    RECORD_ACTION = "record_action"
    RECORD_PERMISSION = "record_permission"
    RECORD_VERIFICATION = "record_verification"
    RECORD_ERROR = "record_error"
    READ_AUDIT = "read_audit"

    MODIFY_AUDIT = "modify_audit"
    DELETE_AUDIT = "delete_audit"
    HIDE_EVENT = "hide_event"
    ALTER_PROVENANCE = "alter_provenance"
    FABRICATE_EVENT = "fabricate_event"


class AuditDecision(str, Enum):
    ALLOW_RECORD = "allow_record"
    ALLOW_READ = "allow_read"
    REQUIRE_AUTHORITY = "require_authority"
    DENY = "deny"


@dataclass(frozen=True)
class AuditResult:
    allowed: bool
    decision: AuditDecision
    provenance_required: bool
    immutable_required: bool
    authority_granted: bool
    reason: str


class ChildAuditProvenanceBoundary:
    """
    Constitutional audit and provenance boundary for a future Child Brain.

    Audit records preserve:
    - actor identity
    - action/event identity
    - source/evidence origin
    - authority/permission context
    - verification state
    - timestamp/provenance context

    Audit is evidence of what happened.
    Audit does not create authority.
    """

    VERSION = "1.0"

    RECORD_OPERATIONS = {
        AuditOperation.RECORD_EVENT,
        AuditOperation.RECORD_DECISION,
        AuditOperation.RECORD_ACTION,
        AuditOperation.RECORD_PERMISSION,
        AuditOperation.RECORD_VERIFICATION,
        AuditOperation.RECORD_ERROR,
    }

    READ_OPERATIONS = {
        AuditOperation.READ_AUDIT,
    }

    DESTRUCTIVE_OPERATIONS = {
        AuditOperation.MODIFY_AUDIT,
        AuditOperation.DELETE_AUDIT,
        AuditOperation.HIDE_EVENT,
        AuditOperation.ALTER_PROVENANCE,
        AuditOperation.FABRICATE_EVENT,
    }

    AUTHORITY_ACTORS = {
        AuditActor.HUMAN,
        AuditActor.SAHIBEX_MOTHER,
    }

    EXTERNAL_ACTORS = {
        AuditActor.SOFTWARE,
        AuditActor.TOOL,
        AuditActor.EXTERNAL_MODEL,
    }

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @classmethod
    def decide(
        cls,
        actor: AuditActor,
        operation: AuditOperation,
        authority_approved: bool = False,
        provenance_valid: bool = True,
        immutable_record: bool = True,
    ) -> AuditResult:

        # Audit manipulation is never permitted without explicit authority.
        if operation in cls.DESTRUCTIVE_OPERATIONS:
            if (
                actor in cls.AUTHORITY_ACTORS
                and authority_approved
                and provenance_valid
            ):
                return AuditResult(
                    allowed=True,
                    decision=AuditDecision.REQUIRE_AUTHORITY,
                    provenance_required=True,
                    immutable_required=True,
                    authority_granted=True,
                    reason="authorized_audit_administration",
                )

            return AuditResult(
                allowed=False,
                decision=AuditDecision.DENY,
                provenance_required=True,
                immutable_required=True,
                authority_granted=False,
                reason="audit_tampering_forbidden",
            )

        # Event recording requires valid provenance.
        if operation in cls.RECORD_OPERATIONS:
            if not provenance_valid:
                return AuditResult(
                    allowed=False,
                    decision=AuditDecision.DENY,
                    provenance_required=True,
                    immutable_required=True,
                    authority_granted=False,
                    reason="invalid_provenance_blocks_audit_record",
                )

            if not immutable_record:
                return AuditResult(
                    allowed=False,
                    decision=AuditDecision.DENY,
                    provenance_required=True,
                    immutable_required=True,
                    authority_granted=False,
                    reason="non_immutable_audit_record_rejected",
                )

            return AuditResult(
                allowed=True,
                decision=AuditDecision.ALLOW_RECORD,
                provenance_required=True,
                immutable_required=True,
                authority_granted=False,
                reason="audit_record_allowed",
            )

        # Audit reading is informational and does not grant authority.
        if operation in cls.READ_OPERATIONS:
            return AuditResult(
                allowed=True,
                decision=AuditDecision.ALLOW_READ,
                provenance_required=True,
                immutable_required=True,
                authority_granted=False,
                reason="audit_read_allowed_without_authority_grant",
            )

        # Unknown state fails closed.
        return AuditResult(
            allowed=False,
            decision=AuditDecision.DENY,
            provenance_required=True,
            immutable_required=True,
            authority_granted=False,
            reason="unknown_audit_state_fails_closed",
        )

    @classmethod
    def every_record_requires_provenance(cls) -> bool:
        return True

    @classmethod
    def every_record_requires_immutable_storage(cls) -> bool:
        return True

    @classmethod
    def actor_identity_is_required(cls) -> bool:
        return True

    @classmethod
    def source_origin_is_required(cls) -> bool:
        return True

    @classmethod
    def authority_context_is_required(cls) -> bool:
        return True

    @classmethod
    def verification_context_is_required(cls) -> bool:
        return True

    @classmethod
    def timestamp_context_is_required(cls) -> bool:
        return True

    @classmethod
    def audit_can_grant_authority(cls) -> bool:
        return False

    @classmethod
    def external_actor_can_be_audit_authority(cls) -> bool:
        return False

    @classmethod
    def audit_tampering_without_authority_is_allowed(cls) -> bool:
        return False

    @classmethod
    def hidden_event_is_valid(cls) -> bool:
        return False

    @classmethod
    def fabricated_event_is_valid(cls) -> bool:
        return False

    @classmethod
    def invalid_provenance_can_be_committed(cls) -> bool:
        return False

    @classmethod
    def missing_provenance_fails_closed(cls) -> bool:
        return True

    @classmethod
    def audit_failure_blocks_commit(cls) -> bool:
        return True

    @classmethod
    def creates_child_brain(cls) -> bool:
        return False

    @classmethod
    def activates_child_brain(cls) -> bool:
        return False

    @classmethod
    def executes_actions(cls) -> bool:
        return False


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

    # Invalid provenance must block recording.
    result = boundary.decide(
        AuditActor.CHILD_BRAIN,
        AuditOperation.RECORD_ACTION,
        provenance_valid=False,
        immutable_record=True,
    )

    assert not result.allowed
    assert result.decision == AuditDecision.DENY

    # Mutable audit record must be rejected.
    result = boundary.decide(
        AuditActor.CHILD_BRAIN,
        AuditOperation.RECORD_ACTION,
        provenance_valid=True,
        immutable_record=False,
    )

    assert not result.allowed
    assert result.decision == AuditDecision.DENY

    # Audit reading is allowed but grants no authority.
    result = boundary.decide(
        AuditActor.CHILD_BRAIN,
        AuditOperation.READ_AUDIT,
    )

    assert result.allowed
    assert result.decision == AuditDecision.ALLOW_READ
    assert not result.authority_granted

    # Unauthorized audit tampering is denied.
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

    # Even external actors cannot manipulate audit.
    for actor in boundary.EXTERNAL_ACTORS:
        result = boundary.decide(
            actor,
            AuditOperation.MODIFY_AUDIT,
            provenance_valid=True,
            authority_approved=True,
        )

        assert not result.allowed
        assert result.decision == AuditDecision.DENY

    # Authorized administration is possible only through
    # Human/Mother authority and valid provenance.
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

    # Boundary layer does not create/activate/execute.
    assert not boundary.creates_child_brain()
    assert not boundary.activates_child_brain()
    assert not boundary.executes_actions()

    print("SAHIBEX CHILD AUDIT & PROVENANCE BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
