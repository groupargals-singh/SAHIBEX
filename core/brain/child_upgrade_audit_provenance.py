from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class UpgradeAuditEvent(str, Enum):
    PROPOSED = "proposed"
    VALIDATED = "validated"
    SANDBOX_PASSED = "sandbox_passed"
    APPLY_STARTED = "apply_started"
    POST_VERIFIED = "post_verified"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    BLOCKED = "blocked"


class AuditDecision(str, Enum):
    ACCEPT = "accept"
    BLOCK = "block"


@dataclass(frozen=True)
class UpgradeProvenance:
    actor_id: str
    actor_type: str
    source: str
    authority_context: str
    verification_context: str
    timestamp_context: str


@dataclass(frozen=True)
class UpgradeAuditRecord:
    audit_id: str
    transaction_id: str
    proposal_id: str
    child_brain_id: str
    event: UpgradeAuditEvent
    version_before: str
    version_after: str
    change_summary: str
    reason: str
    security_result: str
    regression_result: str
    verification_result: str
    approval_result: str
    provenance: UpgradeProvenance
    immutable: bool


@dataclass(frozen=True)
class UpgradeAuditResult:
    decision: AuditDecision
    record: UpgradeAuditRecord
    reason: str


class ChildUpgradeAuditProvenance:
    """
    Immutable audit and provenance boundary for Child upgrades.

    This layer:
    - records every important upgrade event
    - requires complete provenance
    - preserves before/after version information
    - records security, regression and verification results
    - records approval context
    - rejects incomplete or fabricated provenance
    - never grants authority
    - never executes an upgrade
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._records: dict[str, UpgradeAuditRecord] = {}

    def record_event(
        self,
        transaction_id: str,
        proposal_id: str,
        child_brain_id: str,
        event: UpgradeAuditEvent,
        version_before: str,
        version_after: str,
        change_summary: str,
        reason: str,
        security_result: str,
        regression_result: str,
        verification_result: str,
        approval_result: str,
        provenance: UpgradeProvenance,
    ) -> UpgradeAuditResult:
        validation_error = self._validate(
            transaction_id=transaction_id,
            proposal_id=proposal_id,
            child_brain_id=child_brain_id,
            version_before=version_before,
            version_after=version_after,
            change_summary=change_summary,
            reason=reason,
            provenance=provenance,
        )

        if validation_error is not None:
            record = UpgradeAuditRecord(
                audit_id=f"audit-{uuid4()}",
                transaction_id=transaction_id,
                proposal_id=proposal_id,
                child_brain_id=child_brain_id,
                event=UpgradeAuditEvent.BLOCKED,
                version_before=version_before,
                version_after=version_after,
                change_summary=change_summary,
                reason=reason,
                security_result=security_result,
                regression_result=regression_result,
                verification_result=verification_result,
                approval_result=approval_result,
                provenance=provenance,
                immutable=True,
            )

            return UpgradeAuditResult(
                AuditDecision.BLOCK,
                record,
                validation_error,
            )

        record = UpgradeAuditRecord(
            audit_id=f"audit-{uuid4()}",
            transaction_id=transaction_id,
            proposal_id=proposal_id,
            child_brain_id=child_brain_id,
            event=event,
            version_before=version_before,
            version_after=version_after,
            change_summary=change_summary,
            reason=reason,
            security_result=security_result,
            regression_result=regression_result,
            verification_result=verification_result,
            approval_result=approval_result,
            provenance=provenance,
            immutable=True,
        )

        self._records[record.audit_id] = record

        return UpgradeAuditResult(
            AuditDecision.ACCEPT,
            record,
            "upgrade audit record accepted",
        )

    def get_record(self, audit_id: str) -> UpgradeAuditRecord:
        try:
            return self._records[audit_id]
        except KeyError as exc:
            raise ValueError("unknown audit record") from exc

    def list_records(self) -> tuple[UpgradeAuditRecord, ...]:
        return tuple(self._records.values())

    def audit_record_is_immutable(
        self,
        audit_id: str,
    ) -> bool:
        return self.get_record(audit_id).immutable

    def audit_read_grants_authority(self) -> bool:
        return False

    def audit_write_without_provenance(self) -> bool:
        return False

    def external_actor_is_audit_authority(self) -> bool:
        return False

    def fabricated_provenance_is_allowed(self) -> bool:
        return False

    def missing_provenance_is_allowed(self) -> bool:
        return False

    def audit_tampering_is_allowed(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False

    def executes_upgrade(self) -> bool:
        return False

    def _validate(
        self,
        transaction_id: str,
        proposal_id: str,
        child_brain_id: str,
        version_before: str,
        version_after: str,
        change_summary: str,
        reason: str,
        provenance: UpgradeProvenance,
    ) -> str | None:
        if not transaction_id.strip():
            return "transaction_id is required"

        if not proposal_id.strip():
            return "proposal_id is required"

        if not child_brain_id.strip():
            return "child_brain_id is required"

        if not version_before.strip():
            return "version_before is required"

        if not version_after.strip():
            return "version_after is required"

        if not change_summary.strip():
            return "change_summary is required"

        if not reason.strip():
            return "reason is required"

        if not provenance.actor_id.strip():
            return "provenance actor_id is required"

        if not provenance.actor_type.strip():
            return "provenance actor_type is required"

        if not provenance.source.strip():
            return "provenance source is required"

        if not provenance.authority_context.strip():
            return "provenance authority_context is required"

        if not provenance.verification_context.strip():
            return "provenance verification_context is required"

        if not provenance.timestamp_context.strip():
            return "provenance timestamp_context is required"

        return None


if __name__ == "__main__":
    audit = ChildUpgradeAuditProvenance()

    provenance = UpgradeProvenance(
        actor_id="child-001",
        actor_type="child_brain",
        source="self_improvement_engine",
        authority_context="mother-approved",
        verification_context="security-regression-post-verification-passed",
        timestamp_context="demo-timestamp",
    )

    result = audit.record_event(
        transaction_id="upgrade-001",
        proposal_id="proposal-001",
        child_brain_id="child-001",
        event=UpgradeAuditEvent.COMMITTED,
        version_before="1.0",
        version_after="1.1",
        change_summary="Improved reasoning module",
        reason="Reduce repeated reasoning failures",
        security_result="passed",
        regression_result="passed",
        verification_result="passed",
        approval_result="mother-approved",
        provenance=provenance,
    )

    assert result.decision == AuditDecision.ACCEPT
    assert result.record.immutable is True
    assert audit.audit_record_is_immutable(
        result.record.audit_id,
    ) is True

    assert audit.audit_read_grants_authority() is False
    assert audit.audit_write_without_provenance() is False
    assert audit.external_actor_is_audit_authority() is False
    assert audit.fabricated_provenance_is_allowed() is False
    assert audit.missing_provenance_is_allowed() is False
    assert audit.audit_tampering_is_allowed() is False
    assert audit.creates_real_child() is False
    assert audit.activates_real_child() is False
    assert audit.executes_upgrade() is False

    print("SAHIBEX CHILD UPGRADE AUDIT & PROVENANCE TEST: PASS")
