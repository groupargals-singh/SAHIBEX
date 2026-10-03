from __future__ import annotations

from security.audit.execution_trace import (
    ExecutionTraceResult,
    ExecutionTraceVerifier,
)


def valid_success_evidence() -> dict:
    return {
        "execution_id": "execution-001",
        "tool": "read_file",
        "action": "tool_execution",
        "permission_allowed": True,
        "confirmation_required": False,
        "confirmation_provided": False,
        "attempts": 1,
        "result": {"content": "hello"},
        "verification_status": "VERIFIED",
        "recovery_status": "SUCCESS",
        "final_status": "SUCCESS",
        "error": None,
        "risk": "low",
        "reason": "Tool result verified successfully.",
    }


def test_valid_success_trace_is_verified() -> None:
    verifier = ExecutionTraceVerifier()

    result = verifier.verify(
        valid_success_evidence()
    )

    assert isinstance(
        result,
        ExecutionTraceResult,
    )

    assert result.verified is True
    assert result.execution_id == "execution-001"
    assert result.checks_passed > 0
    assert result.checks_failed == 0
    assert result.reasons == ()


def test_missing_execution_id_is_rejected() -> None:
    verifier = ExecutionTraceVerifier()

    evidence = valid_success_evidence()
    evidence["execution_id"] = ""

    try:
        verifier.verify(evidence)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty execution_id must be rejected."
        )


def test_missing_required_field_is_rejected() -> None:
    verifier = ExecutionTraceVerifier()

    evidence = valid_success_evidence()
    del evidence["tool"]

    result = verifier.verify(evidence)

    assert result.verified is False
    assert result.checks_failed > 0
    assert any(
        "tool" in reason
        for reason in result.reasons
    )


def test_success_without_permission_is_rejected() -> None:
    verifier = ExecutionTraceVerifier()

    evidence = valid_success_evidence()
    evidence["permission_allowed"] = False

    result = verifier.verify(evidence)

    assert result.verified is False
    assert any(
        "SUCCESS requires allowed permission" in reason
        for reason in result.reasons
    )


def test_success_without_verification_is_rejected() -> None:
    verifier = ExecutionTraceVerifier()

    evidence = valid_success_evidence()
    evidence["verification_status"] = "NOT_VERIFIED"

    result = verifier.verify(evidence)

    assert result.verified is False
    assert any(
        "SUCCESS requires VERIFIED status" in reason
        for reason in result.reasons
    )


def test_success_with_failed_recovery_is_rejected() -> None:
    verifier = ExecutionTraceVerifier()

    evidence = valid_success_evidence()
    evidence["recovery_status"] = "FAILED"

    result = verifier.verify(evidence)

    assert result.verified is False
    assert any(
        "SUCCESS requires SUCCESS recovery" in reason
        for reason in result.reasons
    )


def test_success_with_error_is_rejected() -> None:
    verifier = ExecutionTraceVerifier()

    evidence = valid_success_evidence()
    evidence["error"] = "Unexpected failure."

    result = verifier.verify(evidence)

    assert result.verified is False
    assert any(
        "SUCCESS cannot contain an error" in reason
        for reason in result.reasons
    )


def test_blocked_trace_requires_denied_permission() -> None:
    verifier = ExecutionTraceVerifier()

    evidence = valid_success_evidence()
    evidence["permission_allowed"] = False
    evidence["verification_status"] = "NOT_VERIFIED"
    evidence["recovery_status"] = "BLOCKED"
    evidence["final_status"] = "BLOCKED"
    evidence["error"] = "Permission required."

    result = verifier.verify(evidence)

    assert result.verified is True
    assert result.execution_id == "execution-001"


def test_blocked_trace_cannot_claim_allowed_permission() -> None:
    verifier = ExecutionTraceVerifier()

    evidence = valid_success_evidence()
    evidence["final_status"] = "BLOCKED"

    result = verifier.verify(evidence)

    assert result.verified is False
    assert any(
        "BLOCKED cannot report allowed permission" in reason
        for reason in result.reasons
    )


def test_failed_trace_cannot_claim_verified() -> None:
    verifier = ExecutionTraceVerifier()

    evidence = valid_success_evidence()
    evidence["verification_status"] = "VERIFIED"
    evidence["final_status"] = "FAILED"
    evidence["recovery_status"] = "FAILED"
    evidence["error"] = "Execution failed."

    result = verifier.verify(evidence)

    assert result.verified is False
    assert any(
        "FAILED cannot report VERIFIED status" in reason
        for reason in result.reasons
    )


def test_confirmation_state_is_consistent() -> None:
    verifier = ExecutionTraceVerifier()

    evidence = valid_success_evidence()
    evidence["confirmation_required"] = False
    evidence["confirmation_provided"] = True

    result = verifier.verify(evidence)

    assert result.verified is False
    assert any(
        "Confirmation provided without" in reason
        for reason in result.reasons
    )


def test_attempt_count_must_be_positive() -> None:
    verifier = ExecutionTraceVerifier()

    evidence = valid_success_evidence()
    evidence["attempts"] = 0

    result = verifier.verify(evidence)

    assert result.verified is False
    assert any(
        "attempts must be greater than zero" in reason
        for reason in result.reasons
    )


def test_trace_verifier_has_no_execution_authority() -> None:
    verifier = ExecutionTraceVerifier()

    forbidden_methods = {
        "execute",
        "invoke",
        "grant_permission",
        "require_permission",
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


def test_different_execution_ids_remain_distinct() -> None:
    verifier = ExecutionTraceVerifier()

    first = valid_success_evidence()

    second = valid_success_evidence()
    second["execution_id"] = "execution-002"

    first_result = verifier.verify(first)
    second_result = verifier.verify(second)

    assert first_result.verified is True
    assert second_result.verified is True

    assert (
        first_result.execution_id
        != second_result.execution_id
    )


def run_all_tests() -> None:
    test_valid_success_trace_is_verified()
    test_missing_execution_id_is_rejected()
    test_missing_required_field_is_rejected()
    test_success_without_permission_is_rejected()
    test_success_without_verification_is_rejected()
    test_success_with_failed_recovery_is_rejected()
    test_success_with_error_is_rejected()
    test_blocked_trace_requires_denied_permission()
    test_blocked_trace_cannot_claim_allowed_permission()
    test_failed_trace_cannot_claim_verified()
    test_confirmation_state_is_consistent()
    test_attempt_count_must_be_positive()
    test_trace_verifier_has_no_execution_authority()
    test_different_execution_ids_remain_distinct()


if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-11 EXECUTION TRACE INTEGRITY TEST: PASS"
    )
