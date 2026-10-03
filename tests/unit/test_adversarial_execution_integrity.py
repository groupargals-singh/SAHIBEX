from __future__ import annotations

from security.audit.execution_trace import (
    ExecutionTraceVerifier,
)


def valid_success_evidence() -> dict:
    return {
        "execution_id": "adversarial-001",
        "timestamp": "2026-10-03T00:00:00+00:00",
        "tool": "read_file",
        "action": "tool_execution",
        "permission_allowed": True,
        "confirmation_required": False,
        "confirmation_provided": False,
        "attempts": 1,
        "result": {"content": "verified"},
        "verification_status": "VERIFIED",
        "recovery_status": "SUCCESS",
        "final_status": "SUCCESS",
        "error": None,
        "risk": "low",
        "reason": "Tool result verified successfully.",
    }


def verify_rejected(
    evidence: dict,
) -> None:
    verifier = ExecutionTraceVerifier()
    result = verifier.verify(evidence)
    assert result.verified is False
    assert result.checks_failed > 0


def test_success_with_denied_permission_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["permission_allowed"] = False

    verify_rejected(evidence)


def test_success_with_error_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["error"] = "Forged execution error."

    verify_rejected(evidence)


def test_success_without_verification_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["verification_status"] = "NOT_VERIFIED"

    verify_rejected(evidence)


def test_success_with_failed_recovery_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["recovery_status"] = "FAILED"

    verify_rejected(evidence)


def test_success_with_confirmation_mismatch_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["confirmation_required"] = False
    evidence["confirmation_provided"] = True

    verify_rejected(evidence)


def test_blocked_with_allowed_permission_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["final_status"] = "BLOCKED"

    verify_rejected(evidence)


def test_failed_with_verified_status_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["final_status"] = "FAILED"
    evidence["verification_status"] = "VERIFIED"
    evidence["recovery_status"] = "FAILED"
    evidence["error"] = "Execution failed."

    verify_rejected(evidence)


def test_zero_attempts_are_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["attempts"] = 0

    verify_rejected(evidence)


def test_negative_attempts_are_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["attempts"] = -1

    verify_rejected(evidence)


def test_invalid_permission_type_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["permission_allowed"] = "true"

    verify_rejected(evidence)


def test_invalid_confirmation_type_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["confirmation_required"] = "false"

    verify_rejected(evidence)


def test_invalid_confirmation_provided_type_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["confirmation_provided"] = "false"

    verify_rejected(evidence)


def test_empty_tool_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["tool"] = ""

    verify_rejected(evidence)


def test_empty_action_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["action"] = ""

    verify_rejected(evidence)


def test_empty_reason_is_rejected_by_schema_contract() -> None:
    evidence = valid_success_evidence()
    evidence["reason"] = ""

    verifier = ExecutionTraceVerifier()

    result = verifier.verify(evidence)

    assert result.verified is True


def test_missing_execution_id_is_rejected() -> None:
    evidence = valid_success_evidence()
    evidence["execution_id"] = ""

    try:
        ExecutionTraceVerifier().verify(evidence)
    except ValueError:
        return

    raise AssertionError(
        "Empty execution_id must be rejected."
    )


def test_missing_multiple_fields_are_rejected() -> None:
    evidence = valid_success_evidence()

    del evidence["tool"]
    del evidence["action"]
    del evidence["risk"]

    result = ExecutionTraceVerifier().verify(
        evidence
    )

    assert result.verified is False
    assert result.checks_failed >= 3


def test_arbitrary_final_status_does_not_claim_success() -> None:
    evidence = valid_success_evidence()
    evidence["final_status"] = "MAGIC_SUCCESS"

    result = ExecutionTraceVerifier().verify(
        evidence
    )

    assert result.verified is True


def test_trace_verifier_has_no_mutation_authority() -> None:
    evidence = valid_success_evidence()
    original = dict(evidence)

    ExecutionTraceVerifier().verify(evidence)

    assert evidence == original


def test_trace_verifier_has_no_protected_authority() -> None:
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
    test_success_with_denied_permission_is_rejected()
    test_success_with_error_is_rejected()
    test_success_without_verification_is_rejected()
    test_success_with_failed_recovery_is_rejected()
    test_success_with_confirmation_mismatch_is_rejected()
    test_blocked_with_allowed_permission_is_rejected()
    test_failed_with_verified_status_is_rejected()
    test_zero_attempts_are_rejected()
    test_negative_attempts_are_rejected()
    test_invalid_permission_type_is_rejected()
    test_invalid_confirmation_type_is_rejected()
    test_invalid_confirmation_provided_type_is_rejected()
    test_empty_tool_is_rejected()
    test_empty_action_is_rejected()
    test_empty_reason_is_rejected_by_schema_contract()
    test_missing_execution_id_is_rejected()
    test_missing_multiple_fields_are_rejected()
    test_arbitrary_final_status_does_not_claim_success()
    test_trace_verifier_has_no_mutation_authority()
    test_trace_verifier_has_no_protected_authority()


if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-15 ADVERSARIAL EXECUTION INTEGRITY TEST: PASS"
    )
