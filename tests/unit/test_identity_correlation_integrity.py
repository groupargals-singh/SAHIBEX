from __future__ import annotations

from copy import deepcopy

from security.audit.execution_trace import ExecutionTraceVerifier


def make_execution(
    execution_id: str,
    tool: str = "read_file",
    action: str = "tool_execution",
    result: object | None = None,
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
        "permission_allowed": True,
        "confirmation_required": False,
        "confirmation_provided": False,
        "attempts": 1,
        "result": result,
        "verification_status": "VERIFIED",
        "recovery_status": "SUCCESS",
        "final_status": "SUCCESS",
        "error": None,
        "risk": "low",
        "reason": "Tool result verified successfully.",
    }


def verify(evidence: dict):
    return ExecutionTraceVerifier().verify(evidence)


def test_each_execution_has_unique_identity() -> None:
    execution_a = make_execution("execution-A")
    execution_b = make_execution("execution-B")

    assert execution_a["execution_id"] != execution_b["execution_id"]


def test_execution_a_is_valid() -> None:
    evidence = make_execution("execution-A")

    result = verify(evidence)

    assert result.verified is True
    assert result.execution_id == "execution-A"


def test_execution_b_is_valid() -> None:
    evidence = make_execution("execution-B")

    result = verify(evidence)

    assert result.verified is True
    assert result.execution_id == "execution-B"


def test_execution_identity_is_preserved() -> None:
    evidence = make_execution("execution-A")

    result = verify(evidence)

    assert result.execution_id == evidence["execution_id"]


def test_execution_id_cannot_be_empty() -> None:
    evidence = make_execution("execution-A")
    evidence["execution_id"] = ""

    try:
        verify(evidence)
    except ValueError:
        return

    raise AssertionError(
        "Empty execution_id must raise ValueError."
    )


def test_missing_execution_id_is_rejected() -> None:
    evidence = make_execution("execution-A")
    del evidence["execution_id"]

    try:
        verify(evidence)
    except ValueError:
        return

    raise AssertionError(
        "Missing execution_id must raise ValueError."
    )


def test_copy_preserves_execution_identity() -> None:
    original = make_execution("execution-A")
    copied = deepcopy(original)

    assert copied["execution_id"] == original["execution_id"]


def test_changing_identity_changes_trace_identity() -> None:
    evidence = make_execution("execution-A")

    evidence["execution_id"] = "execution-B"

    result = verify(evidence)

    assert result.verified is True
    assert result.execution_id == "execution-B"


def test_result_from_execution_a_cannot_change_execution_id() -> None:
    execution_a = make_execution(
        "execution-A",
        result={"owner": "A"},
    )

    execution_b = make_execution(
        "execution-B",
        result={"owner": "B"},
    )

    execution_b["result"] = execution_a["result"]

    result = verify(execution_b)

    assert result.verified is True
    assert result.execution_id == "execution-B"


def test_execution_a_and_b_remain_distinct_after_result_swap() -> None:
    execution_a = make_execution(
        "execution-A",
        result={"value": "A"},
    )

    execution_b = make_execution(
        "execution-B",
        result={"value": "B"},
    )

    original_a_id = execution_a["execution_id"]
    original_b_id = execution_b["execution_id"]

    execution_a["result"] = execution_b["result"]
    execution_b["result"] = execution_a["result"]

    assert execution_a["execution_id"] == original_a_id
    assert execution_b["execution_id"] == original_b_id


def test_permission_state_belongs_to_current_execution_record() -> None:
    execution_a = make_execution("execution-A")
    execution_b = make_execution("execution-B")

    execution_a["permission_allowed"] = False
    execution_a["final_status"] = "BLOCKED"
    execution_a["verification_status"] = "NOT_VERIFIED"
    execution_a["recovery_status"] = "BLOCKED"
    execution_a["error"] = "Permission denied."

    execution_b_result = verify(execution_b)

    assert execution_b_result.verified is True
    assert execution_b["permission_allowed"] is True
    assert execution_b["execution_id"] == "execution-B"


def test_denied_execution_cannot_become_success_by_identity_swap() -> None:
    denied = make_execution("execution-A")

    denied["permission_allowed"] = False
    denied["final_status"] = "BLOCKED"
    denied["verification_status"] = "NOT_VERIFIED"
    denied["recovery_status"] = "BLOCKED"
    denied["error"] = "Permission denied."

    blocked = verify(denied)

    assert blocked.verified is True

    denied["execution_id"] = "execution-B"
    denied["final_status"] = "SUCCESS"

    forged = verify(denied)

    assert forged.verified is False


def test_failed_execution_cannot_become_success_by_identity_swap() -> None:
    failed = make_execution("execution-A")

    failed["final_status"] = "FAILED"
    failed["verification_status"] = "NOT_VERIFIED"
    failed["recovery_status"] = "FAILED"
    failed["error"] = "Execution failed."

    valid_failed = verify(failed)

    assert valid_failed.verified is True

    failed["execution_id"] = "execution-B"
    failed["final_status"] = "SUCCESS"

    forged = verify(failed)

    assert forged.verified is False


def test_success_execution_cannot_use_denied_permission_state() -> None:
    evidence = make_execution("execution-A")

    evidence["permission_allowed"] = False

    result = verify(evidence)

    assert result.verified is False


def test_success_execution_cannot_use_failed_recovery_state() -> None:
    evidence = make_execution("execution-A")

    evidence["recovery_status"] = "FAILED"

    result = verify(evidence)

    assert result.verified is False


def test_success_execution_cannot_use_unverified_state() -> None:
    evidence = make_execution("execution-A")

    evidence["verification_status"] = "NOT_VERIFIED"

    result = verify(evidence)

    assert result.verified is False


def test_success_execution_cannot_use_error_state() -> None:
    evidence = make_execution("execution-A")

    evidence["error"] = "Forged error."

    result = verify(evidence)

    assert result.verified is False


def test_tool_change_is_currently_trace_layer_scope_boundary() -> None:
    evidence = make_execution("execution-A")

    evidence["tool"] = "different_tool"

    result = verify(evidence)

    assert result.verified is True
    assert result.execution_id == "execution-A"


def test_action_change_is_currently_trace_layer_scope_boundary() -> None:
    evidence = make_execution("execution-A")

    evidence["action"] = "different_action"

    result = verify(evidence)

    assert result.verified is True
    assert result.execution_id == "execution-A"


def test_trace_verifier_does_not_mutate_identity() -> None:
    evidence = make_execution("execution-A")
    original_id = evidence["execution_id"]

    verify(evidence)

    assert evidence["execution_id"] == original_id


def test_two_executions_remain_distinct() -> None:
    execution_a = make_execution("execution-A")
    execution_b = make_execution("execution-B")

    result_a = verify(execution_a)
    result_b = verify(execution_b)

    assert result_a.verified is True
    assert result_b.verified is True

    assert result_a.execution_id != result_b.execution_id


def test_identity_cannot_grant_permission() -> None:
    evidence = make_execution("execution-A")

    evidence["execution_id"] = "authorized-execution"
    evidence["permission_allowed"] = False
    evidence["final_status"] = "SUCCESS"

    result = verify(evidence)

    assert result.verified is False
    assert evidence["permission_allowed"] is False


def test_identity_correlation_has_no_execution_authority() -> None:
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
    test_each_execution_has_unique_identity()
    test_execution_a_is_valid()
    test_execution_b_is_valid()
    test_execution_identity_is_preserved()
    test_execution_id_cannot_be_empty()
    test_missing_execution_id_is_rejected()
    test_copy_preserves_execution_identity()
    test_changing_identity_changes_trace_identity()
    test_result_from_execution_a_cannot_change_execution_id()
    test_execution_a_and_b_remain_distinct_after_result_swap()
    test_permission_state_belongs_to_current_execution_record()
    test_denied_execution_cannot_become_success_by_identity_swap()
    test_failed_execution_cannot_become_success_by_identity_swap()
    test_success_execution_cannot_use_denied_permission_state()
    test_success_execution_cannot_use_failed_recovery_state()
    test_success_execution_cannot_use_unverified_state()
    test_success_execution_cannot_use_error_state()
    test_tool_change_is_currently_trace_layer_scope_boundary()
    test_action_change_is_currently_trace_layer_scope_boundary()
    test_trace_verifier_does_not_mutate_identity()
    test_two_executions_remain_distinct()
    test_identity_cannot_grant_permission()
    test_identity_correlation_has_no_execution_authority()


if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-17 IDENTITY CORRELATION INTEGRITY TEST: PASS"
    )
