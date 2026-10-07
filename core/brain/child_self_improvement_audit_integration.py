from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AuditEvent(str, Enum):
    UPGRADE_STARTED = "upgrade_started"
    UPGRADE_VERIFIED = "upgrade_verified"
    UPGRADE_COMMITTED = "upgrade_committed"
    UPGRADE_ROLLED_BACK = "upgrade_rolled_back"
    UPGRADE_BLOCKED = "upgrade_blocked"


class AuditDecision(str, Enum):
    ACCEPT = "accept"
    BLOCK = "block"


@dataclass(frozen=True)
class AuditProvenance:
    actor_id: str
    actor_type: str
    source: str
    authority_context: str
    verification_context: str
    timestamp_context: str


@dataclass(frozen=True)
class AuditIntegrationRequest:
    audit_id: str
    transaction_id: str
    proposal_id: str
    child_brain_id: str
    event: AuditEvent
    version_before: str
    version_after: str
    change_summary: str
    security_verified: bool
    verification_passed: bool
    provenance: AuditProvenance | None
    immutable: bool


@dataclass(frozen=True)
class AuditIntegrationResult:
    decision: AuditDecision
    reason: str
    audit_complete: bool
    provenance_complete: bool


class ChildSelfImprovementAuditIntegration:
    """
    Post-upgrade audit and provenance integration boundary.

    This layer records/validates audit intent only.
    It does not execute upgrades or grant authority.
    """

    VERSION = "1.0"

    def validate(
        self,
        request: AuditIntegrationRequest,
    ) -> AuditIntegrationResult:

        failures: list[str] = []

        required_ids = {
            "audit_id": request.audit_id,
            "transaction_id": request.transaction_id,
            "proposal_id": request.proposal_id,
            "child_brain_id": request.child_brain_id,
            "version_before": request.version_before,
            "version_after": request.version_after,
            "change_summary": request.change_summary,
        }

        for field_name, value in required_ids.items():
            if not value:
                failures.append(f"{field_name} missing")

        if request.version_before == request.version_after:
            failures.append("version did not change")

        if not request.security_verified:
            failures.append("security verification failed")

        if not request.verification_passed:
            failures.append("post-upgrade verification failed")

        if request.provenance is None:
            failures.append("provenance missing")
        else:
            provenance_fields = {
                "actor_id": request.provenance.actor_id,
                "actor_type": request.provenance.actor_type,
                "source": request.provenance.source,
                "authority_context": request.provenance.authority_context,
                "verification_context": (
                    request.provenance.verification_context
                ),
                "timestamp_context": (
                    request.provenance.timestamp_context
                ),
            }

            for field_name, value in provenance_fields.items():
                if not value:
                    failures.append(
                        f"provenance {field_name} missing"
                    )

        if not request.immutable:
            failures.append("audit record is not immutable")

        if failures:
            return AuditIntegrationResult(
                decision=AuditDecision.BLOCK,
                reason="; ".join(failures),
                audit_complete=False,
                provenance_complete=False,
            )

        return AuditIntegrationResult(
            decision=AuditDecision.ACCEPT,
            reason="audit and provenance integration valid",
            audit_complete=True,
            provenance_complete=True,
        )

    def audit_is_immutable(self) -> bool:
        return True

    def provenance_is_required(self) -> bool:
        return True

    def audit_failure_blocks_commit(self) -> bool:
        return True

    def provenance_failure_blocks_commit(self) -> bool:
        return True

    def grants_authority(self) -> bool:
        return False

    def executes_upgrade(self) -> bool:
        return False

    def modifies_soul(self) -> bool:
        return False

    def modifies_constitution(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False


if __name__ == "__main__":
    integration = ChildSelfImprovementAuditIntegration()

    provenance = AuditProvenance(
        actor_id="child-test-actor",
        actor_type="child_brain",
        source="self_improvement",
        authority_context="human_approved",
        verification_context="post_verification_passed",
        timestamp_context="test_timestamp",
    )

    request = AuditIntegrationRequest(
        audit_id="audit-test-001",
        transaction_id="transaction-test-001",
        proposal_id="proposal-test-001",
        child_brain_id="child-test-001",
        event=AuditEvent.UPGRADE_COMMITTED,
        version_before="1.0",
        version_after="1.1",
        change_summary="test capability upgrade",
        security_verified=True,
        verification_passed=True,
        provenance=provenance,
        immutable=True,
    )

    result = integration.validate(request)

    assert result.decision == AuditDecision.ACCEPT
    assert result.audit_complete is True
    assert result.provenance_complete is True

    assert integration.audit_is_immutable() is True
    assert integration.provenance_is_required() is True
    assert integration.audit_failure_blocks_commit() is True
    assert integration.provenance_failure_blocks_commit() is True

    assert integration.grants_authority() is False
    assert integration.executes_upgrade() is False
    assert integration.modifies_soul() is False
    assert integration.modifies_constitution() is False
    assert integration.creates_real_child() is False
    assert integration.activates_real_child() is False

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT AUDIT INTEGRATION TEST: PASS"
    )
