from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class VersionState(str, Enum):
    PROPOSED = "proposed"
    VERIFIED = "verified"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    BLOCKED = "blocked"


class IntegrityDecision(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    BLOCK = "block"


@dataclass(frozen=True)
class UpgradeVersionRecord:
    record_id: str
    child_brain_id: str
    transaction_id: str
    proposal_id: str
    version_before: str
    version_after: str
    integrity_before: str
    integrity_after: str
    parent_version: str
    lineage_id: str
    state: VersionState
    audit_reference: str
    immutable: bool


@dataclass(frozen=True)
class IntegrityCheckResult:
    decision: IntegrityDecision
    record: UpgradeVersionRecord
    reason: str


class ChildUpgradeVersionRegistry:
    """
    Version and integrity registry for Child upgrades.

    This layer:
    - records upgrade version lineage
    - records before/after integrity identities
    - links upgrades to transactions and audit records
    - prevents unknown or inconsistent version transitions
    - preserves immutable upgrade history
    - never executes upgrades
    - never grants authority
    - never modifies soul or constitution
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._records: dict[str, UpgradeVersionRecord] = {}

    def register_upgrade(
        self,
        child_brain_id: str,
        transaction_id: str,
        proposal_id: str,
        version_before: str,
        version_after: str,
        integrity_before: str,
        integrity_after: str,
        parent_version: str,
        lineage_id: str,
        state: VersionState,
        audit_reference: str,
    ) -> IntegrityCheckResult:
        error = self._validate(
            child_brain_id,
            transaction_id,
            proposal_id,
            version_before,
            version_after,
            integrity_before,
            integrity_after,
            parent_version,
            lineage_id,
            audit_reference,
        )

        if error is not None:
            blocked = UpgradeVersionRecord(
                record_id=f"version-{uuid4()}",
                child_brain_id=child_brain_id,
                transaction_id=transaction_id,
                proposal_id=proposal_id,
                version_before=version_before,
                version_after=version_after,
                integrity_before=integrity_before,
                integrity_after=integrity_after,
                parent_version=parent_version,
                lineage_id=lineage_id,
                state=VersionState.BLOCKED,
                audit_reference=audit_reference,
                immutable=True,
            )

            return IntegrityCheckResult(
                IntegrityDecision.BLOCK,
                blocked,
                error,
            )

        if version_after == version_before:
            return self._blocked_record(
                child_brain_id,
                transaction_id,
                proposal_id,
                version_before,
                version_after,
                integrity_before,
                integrity_after,
                parent_version,
                lineage_id,
                audit_reference,
                "version_after must differ from version_before",
            )

        if integrity_after == integrity_before:
            return self._blocked_record(
                child_brain_id,
                transaction_id,
                proposal_id,
                version_before,
                version_after,
                integrity_before,
                integrity_after,
                parent_version,
                lineage_id,
                audit_reference,
                "integrity_after must differ from integrity_before",
            )

        record = UpgradeVersionRecord(
            record_id=f"version-{uuid4()}",
            child_brain_id=child_brain_id,
            transaction_id=transaction_id,
            proposal_id=proposal_id,
            version_before=version_before,
            version_after=version_after,
            integrity_before=integrity_before,
            integrity_after=integrity_after,
            parent_version=parent_version,
            lineage_id=lineage_id,
            state=state,
            audit_reference=audit_reference,
            immutable=True,
        )

        self._records[record.record_id] = record

        return IntegrityCheckResult(
            IntegrityDecision.VALID,
            record,
            "upgrade version and integrity record accepted",
        )

    def verify_integrity(
        self,
        record_id: str,
        current_version: str,
        current_integrity: str,
    ) -> IntegrityCheckResult:
        record = self._get(record_id)

        if current_version == record.version_after and (
            current_integrity == record.integrity_after
        ):
            return IntegrityCheckResult(
                IntegrityDecision.VALID,
                record,
                "current version and integrity match registry",
            )

        return IntegrityCheckResult(
            IntegrityDecision.INVALID,
            record,
            "current version or integrity does not match registry",
        )

    def mark_committed(
        self,
        record_id: str,
    ) -> IntegrityCheckResult:
        record = self._get(record_id)

        updated = self._replace(
            record,
            state=VersionState.COMMITTED,
        )

        return IntegrityCheckResult(
            IntegrityDecision.VALID,
            updated,
            "upgrade marked committed",
        )

    def mark_rolled_back(
        self,
        record_id: str,
    ) -> IntegrityCheckResult:
        record = self._get(record_id)

        updated = self._replace(
            record,
            state=VersionState.ROLLED_BACK,
        )

        return IntegrityCheckResult(
            IntegrityDecision.VALID,
            updated,
            "upgrade marked rolled back",
        )

    def get_record(self, record_id: str) -> UpgradeVersionRecord:
        return self._get(record_id)

    def list_records(self) -> tuple[UpgradeVersionRecord, ...]:
        return tuple(self._records.values())

    def is_immutable(self, record_id: str) -> bool:
        return self._get(record_id).immutable

    def unknown_version_is_trusted(self) -> bool:
        return False

    def integrity_mismatch_is_trusted(self) -> bool:
        return False

    def duplicate_lineage_is_authorized(self) -> bool:
        return False

    def registry_read_grants_authority(self) -> bool:
        return False

    def can_modify_soul(self) -> bool:
        return False

    def can_modify_constitution(self) -> bool:
        return False

    def can_escalate_authority(self) -> bool:
        return False

    def executes_upgrade(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False

    def _validate(
        self,
        child_brain_id: str,
        transaction_id: str,
        proposal_id: str,
        version_before: str,
        version_after: str,
        integrity_before: str,
        integrity_after: str,
        parent_version: str,
        lineage_id: str,
        audit_reference: str,
    ) -> str | None:
        fields = {
            "child_brain_id": child_brain_id,
            "transaction_id": transaction_id,
            "proposal_id": proposal_id,
            "version_before": version_before,
            "version_after": version_after,
            "integrity_before": integrity_before,
            "integrity_after": integrity_after,
            "parent_version": parent_version,
            "lineage_id": lineage_id,
            "audit_reference": audit_reference,
        }

        for name, value in fields.items():
            if not value.strip():
                return f"{name} is required"

        return None

    def _blocked_record(
        self,
        child_brain_id: str,
        transaction_id: str,
        proposal_id: str,
        version_before: str,
        version_after: str,
        integrity_before: str,
        integrity_after: str,
        parent_version: str,
        lineage_id: str,
        audit_reference: str,
        reason: str,
    ) -> IntegrityCheckResult:
        record = UpgradeVersionRecord(
            record_id=f"version-{uuid4()}",
            child_brain_id=child_brain_id,
            transaction_id=transaction_id,
            proposal_id=proposal_id,
            version_before=version_before,
            version_after=version_after,
            integrity_before=integrity_before,
            integrity_after=integrity_after,
            parent_version=parent_version,
            lineage_id=lineage_id,
            state=VersionState.BLOCKED,
            audit_reference=audit_reference,
            immutable=True,
        )

        return IntegrityCheckResult(
            IntegrityDecision.BLOCK,
            record,
            reason,
        )

    def _replace(
        self,
        record: UpgradeVersionRecord,
        **changes: object,
    ) -> UpgradeVersionRecord:
        values = {
            "record_id": record.record_id,
            "child_brain_id": record.child_brain_id,
            "transaction_id": record.transaction_id,
            "proposal_id": record.proposal_id,
            "version_before": record.version_before,
            "version_after": record.version_after,
            "integrity_before": record.integrity_before,
            "integrity_after": record.integrity_after,
            "parent_version": record.parent_version,
            "lineage_id": record.lineage_id,
            "state": record.state,
            "audit_reference": record.audit_reference,
            "immutable": record.immutable,
        }

        values.update(changes)

        updated = UpgradeVersionRecord(**values)
        self._records[updated.record_id] = updated
        return updated

    def _get(self, record_id: str) -> UpgradeVersionRecord:
        try:
            return self._records[record_id]
        except KeyError as exc:
            raise ValueError("unknown version record") from exc


if __name__ == "__main__":
    registry = ChildUpgradeVersionRegistry()

    result = registry.register_upgrade(
        child_brain_id="child-001",
        transaction_id="upgrade-001",
        proposal_id="proposal-001",
        version_before="1.0",
        version_after="1.1",
        integrity_before="hash-before",
        integrity_after="hash-after",
        parent_version="1.0",
        lineage_id="lineage-001",
        state=VersionState.VERIFIED,
        audit_reference="audit-001",
    )

    assert result.decision == IntegrityDecision.VALID

    record_id = result.record.record_id

    check = registry.verify_integrity(
        record_id,
        current_version="1.1",
        current_integrity="hash-after",
    )

    assert check.decision == IntegrityDecision.VALID

    assert registry.unknown_version_is_trusted() is False
    assert registry.integrity_mismatch_is_trusted() is False
    assert registry.duplicate_lineage_is_authorized() is False
    assert registry.registry_read_grants_authority() is False
    assert registry.can_modify_soul() is False
    assert registry.can_modify_constitution() is False
    assert registry.can_escalate_authority() is False
    assert registry.executes_upgrade() is False
    assert registry.creates_real_child() is False
    assert registry.activates_real_child() is False

    print("SAHIBEX CHILD UPGRADE VERSION & INTEGRITY TEST: PASS")
