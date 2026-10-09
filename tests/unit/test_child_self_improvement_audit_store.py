import sqlite3

import pytest

from core.brain.child_self_improvement_audit_integration import (
    AuditEvent,
    AuditIntegrationRequest,
    AuditProvenance,
    AuditDecision,
    ChildSelfImprovementAuditIntegration,
)
from security.audit.child_self_improvement_audit_store import (
    ChildSelfImprovementAuditStore,
)


def request(audit_id: str, *, security_verified: bool = True) -> AuditIntegrationRequest:
    return AuditIntegrationRequest(
        audit_id=audit_id,
        transaction_id=f"tx-{audit_id}",
        proposal_id=f"proposal-{audit_id}",
        child_brain_id="child-test-1",
        event=AuditEvent.UPGRADE_COMMITTED,
        version_before="1.0",
        version_after="1.1",
        change_summary="test-only improvement record",
        security_verified=security_verified,
        verification_passed=True,
        provenance=AuditProvenance(
            actor_id="mother-test",
            actor_type="sahibex_mother",
            source="test",
            authority_context="human_approved_test",
            verification_context="regression_passed",
            timestamp_context="test_run",
        ),
        immutable=True,
    )


def test_audit_events_are_persisted_in_hash_chain(tmp_path):
    store = ChildSelfImprovementAuditStore(tmp_path / "audit.db")
    first = store.append(audit_id="audit-1", payload={"decision": "accept"})
    second = store.append(audit_id="audit-2", payload={"decision": "block"})
    assert first["previous_hash"] == "0" * 64
    assert second["previous_hash"] == first["record_hash"]
    assert store.verify_chain() is True
    assert [event["audit_id"] for event in reversed(store.list_events())] == ["audit-1", "audit-2"]
    store.close()


def test_audit_table_rejects_update_and_delete(tmp_path):
    path = tmp_path / "audit.db"
    store = ChildSelfImprovementAuditStore(path)
    store.append(audit_id="audit-1", payload={"decision": "accept"})
    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        store._connection.execute(
            "UPDATE child_improvement_audit_events SET payload='{}' WHERE audit_id='audit-1'"
        )
    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        store._connection.execute(
            "DELETE FROM child_improvement_audit_events WHERE audit_id='audit-1'"
        )
    store.close()


def test_hash_chain_detects_database_tampering(tmp_path):
    path = tmp_path / "audit.db"
    store = ChildSelfImprovementAuditStore(path)
    store.append(audit_id="audit-1", payload={"decision": "accept"})
    store._connection.execute("DROP TRIGGER child_improvement_audit_no_update")
    store._connection.execute(
        "UPDATE child_improvement_audit_events SET payload=? WHERE audit_id=?",
        ('{"decision":"block"}', "audit-1"),
    )
    store._connection.commit()
    assert store.verify_chain() is False
    store.close()


def test_hash_chain_detects_audit_id_tampering(tmp_path):
    path = tmp_path / "audit-id.db"
    store = ChildSelfImprovementAuditStore(path)
    store.append(audit_id="audit-original", payload={"decision": "accept"})
    store._connection.execute("DROP TRIGGER child_improvement_audit_no_update")
    store._connection.execute(
        "UPDATE child_improvement_audit_events SET audit_id=? WHERE audit_id=?",
        ("audit-renamed", "audit-original"),
    )
    store._connection.commit()
    assert store.verify_chain() is False
    store.close()


def test_integration_persists_both_accepted_and_blocked_decisions(tmp_path):
    store = ChildSelfImprovementAuditStore(tmp_path / "audit.db")
    integration = ChildSelfImprovementAuditIntegration(store=store)

    accepted = integration.record(request("accepted"))
    blocked = integration.record(request("blocked", security_verified=False))

    assert accepted.validation.decision == AuditDecision.ACCEPT
    assert accepted.chain_valid is True
    assert blocked.validation.decision == AuditDecision.BLOCK
    assert blocked.chain_valid is True
    events = {event["audit_id"]: event for event in store.list_events()}
    assert events["blocked"]["payload"]["decision"] == "block"
    assert len(events) == 2
    store.close()


def test_record_requires_persistent_store(tmp_path):
    integration = ChildSelfImprovementAuditIntegration()
    with pytest.raises(RuntimeError, match="persistent_audit_store_not_configured"):
        integration.record(request("no-store"))
