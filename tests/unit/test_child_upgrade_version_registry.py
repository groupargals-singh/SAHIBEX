from core.brain.child_upgrade_version_registry import (
    ChildUpgradeVersionRegistry,
    IntegrityDecision,
    VersionState,
)


def register_valid(
    registry: ChildUpgradeVersionRegistry,
):
    return registry.register_upgrade(
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


def test_valid_version_record() -> None:
    registry = ChildUpgradeVersionRegistry()

    result = register_valid(registry)

    assert result.decision == IntegrityDecision.VALID
    assert result.record.version_before == "1.0"
    assert result.record.version_after == "1.1"
    assert result.record.integrity_before == "hash-before"
    assert result.record.integrity_after == "hash-after"
    assert result.record.immutable is True


def test_matching_integrity_is_valid() -> None:
    registry = ChildUpgradeVersionRegistry()

    result = register_valid(registry)

    check = registry.verify_integrity(
        result.record.record_id,
        current_version="1.1",
        current_integrity="hash-after",
    )

    assert check.decision == IntegrityDecision.VALID


def test_integrity_mismatch_is_invalid() -> None:
    registry = ChildUpgradeVersionRegistry()

    result = register_valid(registry)

    check = registry.verify_integrity(
        result.record.record_id,
        current_version="1.1",
        current_integrity="tampered-hash",
    )

    assert check.decision == IntegrityDecision.INVALID


def test_same_version_is_blocked() -> None:
    registry = ChildUpgradeVersionRegistry()

    result = registry.register_upgrade(
        child_brain_id="child-001",
        transaction_id="upgrade-002",
        proposal_id="proposal-002",
        version_before="1.0",
        version_after="1.0",
        integrity_before="hash-a",
        integrity_after="hash-b",
        parent_version="1.0",
        lineage_id="lineage-002",
        state=VersionState.VERIFIED,
        audit_reference="audit-002",
    )

    assert result.decision == IntegrityDecision.BLOCK


def test_same_integrity_is_blocked() -> None:
    registry = ChildUpgradeVersionRegistry()

    result = registry.register_upgrade(
        child_brain_id="child-001",
        transaction_id="upgrade-003",
        proposal_id="proposal-003",
        version_before="1.0",
        version_after="1.1",
        integrity_before="same-hash",
        integrity_after="same-hash",
        parent_version="1.0",
        lineage_id="lineage-003",
        state=VersionState.VERIFIED,
        audit_reference="audit-003",
    )

    assert result.decision == IntegrityDecision.BLOCK


def test_unknown_version_is_not_trusted() -> None:
    registry = ChildUpgradeVersionRegistry()

    assert registry.unknown_version_is_trusted() is False
    assert registry.integrity_mismatch_is_trusted() is False


def test_security_boundaries() -> None:
    registry = ChildUpgradeVersionRegistry()

    assert registry.registry_read_grants_authority() is False
    assert registry.can_modify_soul() is False
    assert registry.can_modify_constitution() is False
    assert registry.can_escalate_authority() is False
    assert registry.executes_upgrade() is False
    assert registry.creates_real_child() is False
    assert registry.activates_real_child() is False


if __name__ == "__main__":
    test_valid_version_record()
    test_matching_integrity_is_valid()
    test_integrity_mismatch_is_invalid()
    test_same_version_is_blocked()
    test_same_integrity_is_blocked()
    test_unknown_version_is_not_trusted()
    test_security_boundaries()

    print("SAHIBEX CHILD UPGRADE VERSION & INTEGRITY TEST: PASS")
