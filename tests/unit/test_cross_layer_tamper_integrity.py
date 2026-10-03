from __future__ import annotations

from copy import deepcopy

from security.audit.execution_trace import ExecutionTraceVerifier


def valid_execution_chain() -> dict:
    return {
        "execution_id": "cross-layer-001",
        "timestamp": "2026-10-03T00:00:00+00:00",
        "tool": "read_file",
        "action": "tool_execution",
        "permission_allowed": True,
        "confirmation_required": False,
        "confirmation_provided": False,
        "attempts": 1,
        "result": {"content": "original-result"},
        "verification_status": "VERIFIED",
        "recovery_status": "SUCCESS",
        "final_status": "SUCCESS",
        "error": None,
        "risk": "low",
        "reason": "Tool result verified successfully.",
    }


def test_original_chain_is_valid() -> None:
    evidence = valid_execution_chain()

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is True
    assert result.execution_id == evidence["execution_id"]


def test_result_tampering_does_not_change_identity() -> None:
    evidence = valid_execution_chain()

    evidence["result"] = {
        "content": "tampered-result"
    }

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is True
    assert result.execution_id == "cross-layer-001"


def test_execution_id_tampering_changes_identity() -> None:
    evidence = valid_execution_chain()

    evidence["execution_id"] = "forged-execution-id"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is True
    assert result.execution_id == "forged-execution-id"


def test_permission_tampering_is_detected() -> None:
    evidence = valid_execution_chain()

    evidence["permission_allowed"] = False

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_verification_tampering_is_detected() -> None:
    evidence = valid_execution_chain()

    evidence["verification_status"] = "NOT_VERIFIED"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_recovery_tampering_is_detected() -> None:
    evidence = valid_execution_chain()

    evidence["recovery_status"] = "FAILED"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_final_status_tampering_is_detected() -> None:
    evidence = valid_execution_chain()

    evidence["final_status"] = "FAILED"
    evidence["error"] = "Tampered failure."

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_confirmation_tampering_is_detected() -> None:
    evidence = valid_execution_chain()

    evidence["confirmation_provided"] = True

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_attempt_tampering_is_detected() -> None:
    evidence = valid_execution_chain()

    evidence["attempts"] = 0

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_negative_attempts_are_detected() -> None:
    evidence = valid_execution_chain()

    evidence["attempts"] = -1

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_invalid_permission_type_is_detected() -> None:
    evidence = valid_execution_chain()

    evidence["permission_allowed"] = "true"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_invalid_confirmation_type_is_detected() -> None:
    evidence = valid_execution_chain()

    evidence["confirmation_required"] = "false"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_invalid_confirmation_provided_type_is_detected() -> None:
    evidence = valid_execution_chain()

    evidence["confirmation_provided"] = "false"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_empty_tool_is_detected() -> None:
    evidence = valid_execution_chain()

    evidence["tool"] = ""

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_empty_action_is_detected() -> None:
    evidence = valid_execution_chain()

    evidence["action"] = ""

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_empty_reason_is_allowed_by_current_trace_contract() -> None:
    evidence = valid_execution_chain()

    evidence["reason"] = ""

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is True


def test_missing_execution_id_is_rejected() -> None:
    evidence = valid_execution_chain()

    del evidence["execution_id"]

    try:
        ExecutionTraceVerifier().verify(evidence)
    except ValueError:
        return

    raise AssertionError(
        "Missing execution_id must raise ValueError."
    )


def test_empty_execution_id_is_rejected() -> None:
    evidence = valid_execution_chain()

    evidence["execution_id"] = ""

    try:
        ExecutionTraceVerifier().verify(evidence)
    except ValueError:
        return

    raise AssertionError(
        "Empty execution_id must raise ValueError."
    )


def test_missing_tool_field_breaks_chain() -> None:
    evidence = valid_execution_chain()

    del evidence["tool"]

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False
    assert result.checks_failed >= 1


def test_missing_permission_field_breaks_chain() -> None:
    evidence = valid_execution_chain()

    del evidence["permission_allowed"]

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False
    assert result.checks_failed >= 1


def test_missing_verification_field_breaks_chain() -> None:
    evidence = valid_execution_chain()

    del evidence["verification_status"]

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False
    assert result.checks_failed >= 1


def test_missing_multiple_core_fields_breaks_chain() -> None:
    evidence = valid_execution_chain()

    del evidence["tool"]
    del evidence["action"]
    del evidence["risk"]

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False
    assert result.checks_failed >= 3


def test_deepcopy_tampering_does_not_modify_original() -> None:
    original = valid_execution_chain()
    tampered = deepcopy(original)

    tampered["result"]["content"] = "modified-copy"

    assert original["result"]["content"] == "original-result"
    assert tampered["result"]["content"] == "modified-copy"


def test_trace_verifier_does_not_mutate_evidence() -> None:
    evidence = valid_execution_chain()
    original = deepcopy(evidence)

    ExecutionTraceVerifier().verify(evidence)

    assert evidence == original


def test_consistent_failed_execution_is_valid() -> None:
    evidence = valid_execution_chain()

    evidence["final_status"] = "FAILED"
    evidence["verification_status"] = "NOT_VERIFIED"
    evidence["recovery_status"] = "FAILED"
    evidence["error"] = "Real failure."

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is True


def test_failed_execution_cannot_be_upgraded_to_success() -> None:
    evidence = valid_execution_chain()

    evidence["final_status"] = "FAILED"
    evidence["verification_status"] = "NOT_VERIFIED"
    evidence["recovery_status"] = "FAILED"
    evidence["error"] = "Real failure."

    failed = ExecutionTraceVerifier().verify(evidence)

    assert failed.verified is True

    evidence["final_status"] = "SUCCESS"

    forged = ExecutionTraceVerifier().verify(evidence)

    assert forged.verified is False


def test_consistent_blocked_execution_is_valid() -> None:
    evidence = valid_execution_chain()

    evidence["permission_allowed"] = False
    evidence["final_status"] = "BLOCKED"
    evidence["verification_status"] = "NOT_VERIFIED"
    evidence["recovery_status"] = "BLOCKED"
    evidence["error"] = "Permission denied."

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is True


def test_blocked_execution_cannot_be_upgraded_to_success() -> None:
    evidence = valid_execution_chain()

    evidence["permission_allowed"] = False
    evidence["final_status"] = "BLOCKED"
    evidence["verification_status"] = "NOT_VERIFIED"
    evidence["recovery_status"] = "BLOCKED"
    evidence["error"] = "Permission denied."

    blocked = ExecutionTraceVerifier().verify(evidence)

    assert blocked.verified is True

    evidence["final_status"] = "SUCCESS"

    forged = ExecutionTraceVerifier().verify(evidence)

    assert forged.verified is False


def test_error_cannot_become_success() -> None:
    evidence = valid_execution_chain()

    evidence["error"] = "Execution error."

    failed = ExecutionTraceVerifier().verify(evidence)

    assert failed.verified is False

    evidence["final_status"] = "SUCCESS"

    forged = ExecutionTraceVerifier().verify(evidence)

    assert forged.verified is False


def test_denied_permission_cannot_become_success() -> None:
    evidence = valid_execution_chain()

    evidence["permission_allowed"] = False
    evidence["final_status"] = "SUCCESS"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_success_requires_verified_status() -> None:
    evidence = valid_execution_chain()

    evidence["verification_status"] = "NOT_VERIFIED"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_success_requires_successful_recovery() -> None:
    evidence = valid_execution_chain()

    evidence["recovery_status"] = "FAILED"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_success_requires_no_error() -> None:
    evidence = valid_execution_chain()

    evidence["error"] = "Forged error."

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False


def test_cross_layer_tampering_never_grants_permission() -> None:
    evidence = valid_execution_chain()

    evidence["permission_allowed"] = False
    evidence["final_status"] = "SUCCESS"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is False
    assert evidence["permission_allowed"] is False


def test_tool_identity_change_is_outside_current_trace_scope() -> None:
    evidence = valid_execution_chain()

    evidence["tool"] = "different_tool"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is True


def test_action_identity_change_is_outside_current_trace_scope() -> None:
    evidence = valid_execution_chain()

    evidence["action"] = "different_action"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is True


def test_arbitrary_final_status_is_currently_outside_scope() -> None:
    evidence = valid_execution_chain()

    evidence["final_status"] = "MAGIC_SUCCESS"

    result = ExecutionTraceVerifier().verify(evidence)

    assert result.verified is True


def test_trace_verifier_has_no_mutation_authority() -> None:
    verifier = ExecutionTraceVerifier()

    forbidden_methods = {
        "execute",
        "invoke",
        "grant_permission",
        "require_permission",
        "change_permission",
        "modify_constitution",
        "update_constitution",
        "write_file",
        "delete_file",
        "run_command",
    }

    public_methods = set(dir(verifier))

    assert not (
        forbidden_methods & public_methods
    )


def run_all_tests() -> None:
    test_original_chain_is_valid()
    test_result_tampering_does_not_change_identity()
    test_execution_id_tampering_changes_identity()
    test_permission_tampering_is_detected()
    test_verification_tampering_is_detected()
    test_recovery_tampering_is_detected()
    test_final_status_tampering_is_detected()
    test_confirmation_tampering_is_detected()
    test_attempt_tampering_is_detected()
    test_negative_attempts_are_detected()
    test_invalid_permission_type_is_detected()
    test_invalid_confirmation_type_is_detected()
    test_invalid_confirmation_provided_type_is_detected()
    test_empty_tool_is_detected()
    test_empty_action_is_detected()
    test_empty_reason_is_allowed_by_current_trace_contract()
    test_missing_execution_id_is_rejected()
    test_empty_execution_id_is_rejected()
    test_missing_tool_field_breaks_chain()
    test_missing_permission_field_breaks_chain()
    test_missing_verification_field_breaks_chain()
    test_missing_multiple_core_fields_breaks_chain()
    test_deepcopy_tampering_does_not_modify_original()
    test_trace_verifier_does_not_mutate_evidence()
    test_consistent_failed_execution_is_valid()
    test_failed_execution_cannot_be_upgraded_to_success()
    test_consistent_blocked_execution_is_valid()
    test_blocked_execution_cannot_be_upgraded_to_success()
    test_error_cannot_become_success()
    test_denied_permission_cannot_become_success()
    test_success_requires_verified_status()
    test_success_requires_successful_recovery()
    test_success_requires_no_error()
    test_cross_layer_tampering_never_grants_permission()
    test_tool_identity_change_is_outside_current_trace_scope()
    test_action_identity_change_is_outside_current_trace_scope()
    test_arbitrary_final_status_is_currently_outside_scope()
    test_trace_verifier_has_no_mutation_authority()


if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-16 CROSS-LAYER TAMPER INTEGRITY TEST: PASS"
    )
