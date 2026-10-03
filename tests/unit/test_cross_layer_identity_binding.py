from __future__ import annotations

from copy import deepcopy

from security.audit.execution_trace import ExecutionTraceVerifier


def make_execution(
    execution_id: str,
    *,
    tool: str = "read_file",
    action: str = "tool_execution",
    result: object | None = None,
    permission_allowed: bool = True,
    confirmation_required: bool = False,
    confirmation_provided: bool = False,
    verification_status: str = "VERIFIED",
    recovery_status: str = "SUCCESS",
    final_status: str = "SUCCESS",
    error: str | None = None,
) -> dict:
    if result is None:
        result = {
            "content": f"result-for-{execution_id}"
        }

    return {
        "execution_id": execution_id,
        "timestamp": "2026-10-03T00:00:00+00:00",
        "tool": tool,
        "action": action,
        "permission_allowed": permission_allowed,
        "confirmation_required": confirmation_required,
        "confirmation_provided": confirmation_provided,
        "attempts": 1,
        "result": result,
        "verification_status": verification_status,
        "recovery_status": recovery_status,
        "final_status": final_status,
        "error": error,
        "risk": "low",
        "reason": "Execution identity binding test.",
    }


def make_audit_record(
    evidence: dict,
) -> dict:
    return {
        "execution_id": evidence["execution_id"],
        "tool": evidence["tool"],
        "action": evidence["action"],
        "permission": (
            "allowed"
            if evidence["permission_allowed"]
            else "blocked"
        ),
        "risk": evidence["risk"],
        "reason": evidence["reason"],
    }


def verify_trace(
    evidence: dict,
):
    return ExecutionTraceVerifier().verify(evidence)


def assert_identity_match(
    evidence: dict,
    audit: dict,
) -> None:
    assert evidence["execution_id"] == audit["execution_id"]


def test_matching_execution_identity_is_valid() -> None:
    evidence = make_execution("execution-A")
    audit = make_audit_record(evidence)

    assert_identity_match(evidence, audit)

    trace = verify_trace(evidence)

    assert trace.verified is True
    assert trace.execution_id == audit["execution_id"]


def test_different_execution_ids_are_detected() -> None:
    evidence = make_execution("execution-A")
    audit = make_audit_record(
        make_execution("execution-B")
    )

    assert evidence["execution_id"] != audit["execution_id"]


def test_execution_a_cannot_bind_to_audit_b() -> None:
    evidence_a = make_execution("execution-A")
    audit_b = make_audit_record(
        make_execution("execution-B")
    )

    assert (
        evidence_a["execution_id"]
        != audit_b["execution_id"]
    )


def test_execution_b_cannot_bind_to_audit_a() -> None:
    evidence_b = make_execution("execution-B")
    audit_a = make_audit_record(
        make_execution("execution-A")
    )

    assert (
        evidence_b["execution_id"]
        != audit_a["execution_id"]
    )


def test_matching_identity_survives_deepcopy() -> None:
    evidence = make_execution("execution-A")
    audit = make_audit_record(evidence)

    copied_evidence = deepcopy(evidence)
    copied_audit = deepcopy(audit)

    assert_identity_match(
        copied_evidence,
        copied_audit,
    )


def test_tampered_audit_identity_breaks_binding() -> None:
    evidence = make_execution("execution-A")
    audit = make_audit_record(evidence)

    audit["execution_id"] = "execution-B"

    assert (
        evidence["execution_id"]
        != audit["execution_id"]
    )


def test_tampered_evidence_identity_breaks_binding() -> None:
    evidence = make_execution("execution-A")
    audit = make_audit_record(evidence)

    evidence["execution_id"] = "execution-B"

    assert (
        evidence["execution_id"]
        != audit["execution_id"]
    )


def test_trace_identity_matches_evidence_identity() -> None:
    evidence = make_execution("execution-A")

    trace = verify_trace(evidence)

    assert trace.execution_id == evidence["execution_id"]


def test_trace_identity_matches_audit_identity() -> None:
    evidence = make_execution("execution-A")
    audit = make_audit_record(evidence)

    trace = verify_trace(evidence)

    assert trace.execution_id == audit["execution_id"]


def test_three_layer_identity_matches() -> None:
    evidence = make_execution("execution-A")
    audit = make_audit_record(evidence)
    trace = verify_trace(evidence)

    assert evidence["execution_id"] == audit["execution_id"]
    assert evidence["execution_id"] == trace.execution_id
    assert audit["execution_id"] == trace.execution_id


def test_three_layer_identity_mismatch_is_detected() -> None:
    evidence = make_execution("execution-A")
    audit = make_audit_record(evidence)

    audit["execution_id"] = "execution-B"

    trace = verify_trace(evidence)

    assert trace.verified is True
    assert evidence["execution_id"] != audit["execution_id"]
    assert trace.execution_id != audit["execution_id"]


def test_tool_binding_matches_between_evidence_and_audit() -> None:
    evidence = make_execution(
        "execution-A",
        tool="read_file",
    )
    audit = make_audit_record(evidence)

    assert evidence["tool"] == audit["tool"]


def test_tool_binding_mismatch_is_detectable() -> None:
    evidence = make_execution(
        "execution-A",
        tool="read_file",
    )
    audit = make_audit_record(evidence)

    audit["tool"] = "different_tool"

    assert evidence["tool"] != audit["tool"]


def test_action_binding_matches_between_evidence_and_audit() -> None:
    evidence = make_execution(
        "execution-A",
        action="tool_execution",
    )
    audit = make_audit_record(evidence)

    assert evidence["action"] == audit["action"]


def test_action_binding_mismatch_is_detectable() -> None:
    evidence = make_execution(
        "execution-A",
        action="tool_execution",
    )
    audit = make_audit_record(evidence)

    audit["action"] = "different_action"

    assert evidence["action"] != audit["action"]


def test_permission_binding_matches() -> None:
    evidence = make_execution(
        "execution-A",
        permission_allowed=True,
    )
    audit = make_audit_record(evidence)

    assert audit["permission"] == "allowed"


def test_blocked_permission_binding_matches() -> None:
    evidence = make_execution(
        "execution-A",
        permission_allowed=False,
        verification_status="NOT_VERIFIED",
        recovery_status="BLOCKED",
        final_status="BLOCKED",
        error="Permission denied.",
    )
    audit = make_audit_record(evidence)

    assert audit["permission"] == "blocked"

    trace = verify_trace(evidence)

    assert trace.verified is True


def test_identity_mismatch_cannot_upgrade_blocked_execution() -> None:
    blocked = make_execution(
        "execution-A",
        permission_allowed=False,
        verification_status="NOT_VERIFIED",
        recovery_status="BLOCKED",
        final_status="BLOCKED",
        error="Permission denied.",
    )

    audit_b = make_audit_record(
        make_execution("execution-B")
    )

    blocked_trace = verify_trace(blocked)

    assert blocked_trace.verified is True
    assert (
        blocked["execution_id"]
        != audit_b["execution_id"]
    )


def test_identity_mismatch_cannot_upgrade_failed_execution() -> None:
    failed = make_execution(
        "execution-A",
        verification_status="NOT_VERIFIED",
        recovery_status="FAILED",
        final_status="FAILED",
        error="Execution failed.",
    )

    audit_b = make_audit_record(
        make_execution("execution-B")
    )

    failed_trace = verify_trace(failed)

    assert failed_trace.verified is True
    assert (
        failed["execution_id"]
        != audit_b["execution_id"]
    )


def test_identity_binding_does_not_grant_permission() -> None:
    evidence = make_execution(
        "execution-A",
        permission_allowed=False,
        final_status="SUCCESS",
    )
    audit = make_audit_record(evidence)

    assert_identity_match(evidence, audit)

    trace = verify_trace(evidence)

    assert trace.verified is False
    assert evidence["permission_allowed"] is False


def test_identity_binding_does_not_change_trace() -> None:
    evidence = make_execution("execution-A")
    audit = make_audit_record(evidence)

    original = deepcopy(evidence)

    assert_identity_match(evidence, audit)
    verify_trace(evidence)

    assert evidence == original


def test_empty_audit_identity_breaks_binding() -> None:
    evidence = make_execution("execution-A")
    audit = make_audit_record(evidence)

    audit["execution_id"] = ""

    assert (
        evidence["execution_id"]
        != audit["execution_id"]
    )


def test_empty_evidence_identity_is_rejected() -> None:
    evidence = make_execution("execution-A")
    evidence["execution_id"] = ""

    try:
        verify_trace(evidence)
    except ValueError:
        return

    raise AssertionError(
        "Empty evidence execution_id must raise ValueError."
    )


def test_missing_audit_identity_breaks_binding() -> None:
    evidence = make_execution("execution-A")
    audit = make_audit_record(evidence)

    del audit["execution_id"]

    assert "execution_id" not in audit


def test_identity_binding_has_no_execution_authority() -> None:
    verifier = ExecutionTraceVerifier()

    forbidden_methods = {
        "execute",
        "invoke",
        "run_command",
        "write_file",
        "delete_file",
        "grant_permission",
        "require_permission",
        "change_permission",
        "modify_constitution",
        "update_constitution",
    }

    public_methods = set(dir(verifier))

    assert not (
        forbidden_methods & public_methods
    )


def run_all_tests() -> None:
    test_matching_execution_identity_is_valid()
    test_different_execution_ids_are_detected()
    test_execution_a_cannot_bind_to_audit_b()
    test_execution_b_cannot_bind_to_audit_a()
    test_matching_identity_survives_deepcopy()
    test_tampered_audit_identity_breaks_binding()
    test_tampered_evidence_identity_breaks_binding()
    test_trace_identity_matches_evidence_identity()
    test_trace_identity_matches_audit_identity()
    test_three_layer_identity_matches()
    test_three_layer_identity_mismatch_is_detected()
    test_tool_binding_matches_between_evidence_and_audit()
    test_tool_binding_mismatch_is_detectable()
    test_action_binding_matches_between_evidence_and_audit()
    test_action_binding_mismatch_is_detectable()
    test_permission_binding_matches()
    test_blocked_permission_binding_matches()
    test_identity_mismatch_cannot_upgrade_blocked_execution()
    test_identity_mismatch_cannot_upgrade_failed_execution()
    test_identity_binding_does_not_grant_permission()
    test_identity_binding_does_not_change_trace()
    test_empty_audit_identity_breaks_binding()
    test_empty_evidence_identity_is_rejected()
    test_missing_audit_identity_breaks_binding()
    test_identity_binding_has_no_execution_authority()


if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-18 CROSS-LAYER IDENTITY BINDING TEST: PASS"
    )
