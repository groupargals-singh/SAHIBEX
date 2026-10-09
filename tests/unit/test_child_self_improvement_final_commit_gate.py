from core.brain.child_self_improvement_final_commit_gate import (
    ChildSelfImprovementFinalCommitGate,
    FinalCommitDecision,
    FinalCommitGateState,
)
from core.brain.child_self_improvement_audit_integration import (
    AuditEvent,
    AuditIntegrationRequest,
    AuditProvenance,
    ChildSelfImprovementAuditIntegration,
)
from security.audit.child_self_improvement_audit_store import (
    ChildSelfImprovementAuditStore,
)


def all_gates_passed() -> FinalCommitGateState:
    return FinalCommitGateState(
        proposal_valid=True,
        risk_analysis_passed=True,
        compatibility_passed=True,
        sandbox_passed=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
        governance_passed=True,
        mother_approved=True,
        human_approved=True,
        post_verification_passed=True,
        soul_unchanged=True,
        constitution_unchanged=True,
        authority_boundary_intact=True,
        audit_complete=True,
        provenance_complete=True,
    )


def test_all_gates_ready():
    gate = ChildSelfImprovementFinalCommitGate()

    result = gate.evaluate(all_gates_passed())

    assert result.decision == FinalCommitDecision.READY
    assert result.failed_gates == ()
    assert result.requires_mother is True
    assert result.requires_human is False


def test_proposal_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "proposal_valid": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "proposal_valid" in result.failed_gates


def test_risk_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "risk_analysis_passed": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "risk_analysis_passed" in result.failed_gates


def test_compatibility_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "compatibility_passed": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "compatibility_passed" in result.failed_gates


def test_sandbox_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "sandbox_passed": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "sandbox_passed" in result.failed_gates


def test_security_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "security_passed": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "security_passed" in result.failed_gates


def test_regression_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "regression_passed": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "regression_passed" in result.failed_gates


def test_verification_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "verification_passed": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "verification_passed" in result.failed_gates


def test_governance_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "governance_passed": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "governance_passed" in result.failed_gates


def test_mother_approval_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "mother_approved": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "mother_approved" in result.failed_gates


def test_human_approval_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = FinalCommitGateState(
        **{**all_gates_passed().__dict__, "human_approved": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "human_approved" in result.failed_gates


def test_post_verification_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "post_verification_passed": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "post_verification_passed" in result.failed_gates


def test_soul_change_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "soul_unchanged": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "soul_unchanged" in result.failed_gates


def test_constitution_change_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "constitution_unchanged": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "constitution_unchanged" in result.failed_gates


def test_authority_boundary_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "authority_boundary_intact": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "authority_boundary_intact" in result.failed_gates


def test_audit_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "audit_complete": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "audit_complete" in result.failed_gates


def test_provenance_failure_blocks():
    gate = ChildSelfImprovementFinalCommitGate()
    state = all_gates_passed()
    state = FinalCommitGateState(
        **{**state.__dict__, "provenance_complete": False}
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK
    assert "provenance_complete" in result.failed_gates


def test_multiple_failures_reported():
    gate = ChildSelfImprovementFinalCommitGate()

    state = FinalCommitGateState(
        proposal_valid=False,
        risk_analysis_passed=False,
        compatibility_passed=True,
        sandbox_passed=True,
        security_passed=False,
        regression_passed=True,
        verification_passed=True,
        governance_passed=False,
        mother_approved=False,
        human_approved=True,
        post_verification_passed=True,
        soul_unchanged=True,
        constitution_unchanged=False,
        authority_boundary_intact=False,
        audit_complete=True,
        provenance_complete=False,
    )

    result = gate.evaluate(state)

    assert result.decision == FinalCommitDecision.BLOCK

    assert "proposal_valid" in result.failed_gates
    assert "risk_analysis_passed" in result.failed_gates
    assert "security_passed" in result.failed_gates
    assert "governance_passed" in result.failed_gates
    assert "mother_approved" in result.failed_gates
    assert "constitution_unchanged" in result.failed_gates
    assert "authority_boundary_intact" in result.failed_gates
    assert "provenance_complete" in result.failed_gates


def _persist_audit(store, audit_id: str, *, security_verified: bool = True):
    integration = ChildSelfImprovementAuditIntegration(store=store)
    request = AuditIntegrationRequest(
        audit_id=audit_id,
        transaction_id=f"tx-{audit_id}",
        proposal_id=f"proposal-{audit_id}",
        child_brain_id="child-test-1",
        event=AuditEvent.UPGRADE_VERIFIED,
        version_before="1.0",
        version_after="1.1",
        change_summary="test-only change",
        security_verified=security_verified,
        verification_passed=True,
        provenance=AuditProvenance(
            actor_id="mother-test",
            actor_type="sahibex_mother",
            source="test",
            authority_context="human_approved",
            verification_context="post_verification_passed",
            timestamp_context="test",
        ),
        immutable=True,
    )
    return integration.record(request)


def _binding(audit_id: str) -> dict[str, str]:
    return {
        "expected_child_brain_id": "child-test-1",
        "expected_proposal_id": f"proposal-{audit_id}",
        "expected_version_before": "1.0",
        "expected_version_after": "1.1",
    }


def test_persisted_gate_requires_real_accepted_audit_record(tmp_path):
    store = ChildSelfImprovementAuditStore(tmp_path / "commit-audit.db")
    gate = ChildSelfImprovementFinalCommitGate(audit_store=store)
    state = all_gates_passed()

    missing = gate.evaluate_persisted(state, audit_id="not-recorded", **_binding("not-recorded"))
    assert missing.decision == FinalCommitDecision.BLOCK
    assert "audit_record_persisted" in missing.failed_gates

    _persist_audit(store, "accepted-audit")
    accepted = gate.evaluate_persisted(state, audit_id="accepted-audit", **_binding("accepted-audit"))
    assert accepted.decision == FinalCommitDecision.READY

    mismatched = gate.evaluate_persisted(
        state,
        audit_id="accepted-audit",
        expected_child_brain_id="child-test-1",
        expected_proposal_id="proposal-for-another-change",
        expected_version_before="1.0",
        expected_version_after="1.1",
    )
    assert mismatched.decision == FinalCommitDecision.BLOCK
    assert "audit_context_binding" in mismatched.failed_gates

    _persist_audit(store, "blocked-audit", security_verified=False)
    blocked = gate.evaluate_persisted(state, audit_id="blocked-audit", **_binding("blocked-audit"))
    assert blocked.decision == FinalCommitDecision.BLOCK
    assert "audit_complete" in blocked.failed_gates
    store.close()


def test_persisted_gate_blocks_if_audit_chain_is_tampered(tmp_path):
    store = ChildSelfImprovementAuditStore(tmp_path / "tampered-audit.db")
    _persist_audit(store, "audit-1")
    store._connection.execute("DROP TRIGGER child_improvement_audit_no_update")
    store._connection.execute(
        "UPDATE child_improvement_audit_events SET payload=? WHERE audit_id=?",
        ('{"decision":"accept","audit_complete":true,"provenance_complete":true}', "audit-1"),
    )
    store._connection.commit()

    gate = ChildSelfImprovementFinalCommitGate(audit_store=store)
    result = gate.evaluate_persisted(all_gates_passed(), audit_id="audit-1", **_binding("audit-1"))
    assert result.decision == FinalCommitDecision.BLOCK
    assert "audit_chain_valid" in result.failed_gates
    store.close()


def test_persisted_gate_blocks_without_store(tmp_path):
    gate = ChildSelfImprovementFinalCommitGate()
    result = gate.evaluate_persisted(all_gates_passed(), audit_id="audit-1", **_binding("audit-1"))
    assert result.decision == FinalCommitDecision.BLOCK
    assert "audit_record_persisted" in result.failed_gates


def test_all_gates_passed_helper():
    gate = ChildSelfImprovementFinalCommitGate()

    assert gate.all_gates_passed(all_gates_passed()) is True


def test_gate_invariants():
    gate = ChildSelfImprovementFinalCommitGate()

    assert gate.proposal_gate_required() is True
    assert gate.risk_gate_required() is True
    assert gate.compatibility_gate_required() is True
    assert gate.sandbox_gate_required() is True
    assert gate.security_gate_required() is True
    assert gate.regression_gate_required() is True
    assert gate.verification_gate_required() is True
    assert gate.governance_gate_required() is True
    assert gate.mother_approval_required() is True
    assert gate.post_verification_required() is True
    assert gate.soul_integrity_required() is True
    assert gate.constitution_integrity_required() is True
    assert gate.authority_boundary_required() is True
    assert gate.audit_required() is True
    assert gate.provenance_required() is True

    assert gate.execution_allowed() is False
    assert gate.performs_commit() is False
    assert gate.grants_authority() is False
    assert gate.bypass_allowed() is False
    assert gate.modifies_soul() is False
    assert gate.modifies_constitution() is False
    assert gate.creates_real_child() is False
    assert gate.activates_real_child() is False


if __name__ == "__main__":
    test_all_gates_ready()
    test_proposal_failure_blocks()
    test_risk_failure_blocks()
    test_compatibility_failure_blocks()
    test_sandbox_failure_blocks()
    test_security_failure_blocks()
    test_regression_failure_blocks()
    test_verification_failure_blocks()
    test_governance_failure_blocks()
    test_mother_approval_failure_blocks()
    test_post_verification_failure_blocks()
    test_soul_change_blocks()
    test_constitution_change_blocks()
    test_authority_boundary_failure_blocks()
    test_audit_failure_blocks()
    test_provenance_failure_blocks()
    test_multiple_failures_reported()
    test_all_gates_passed_helper()
    test_gate_invariants()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT FINAL COMMIT GATE TEST: PASS"
    )
