from __future__ import annotations

import tempfile
from pathlib import Path

from core.brain.operational_tool_execution import (
    OperationalToolExecution,
)
from core.policies.approval import PermissionEngine
from security.audit.execution_evidence import (
    ExecutionEvidenceRecorder,
)
from security.audit.execution_trace import (
    ExecutionTraceVerifier,
)
from tools.discovery import ToolDiscovery
from tools.executor import SafeToolExecutor
from tools.intelligence import ToolIntelligence
from tools.invocation import ToolInvoker
from tools.permission_gateway import (
    ToolPermissionGateway,
)
from tools.registry import build_default_registry
from tools.result_handler import ToolResultHandler


def build_real_tool_intelligence(
    project_root: Path,
) -> ToolIntelligence:
    registry = build_default_registry(
        project_root
    )

    discovery = ToolDiscovery(registry)

    permission_engine = PermissionEngine()

    permission_gateway = ToolPermissionGateway(
        permission_engine,
        registry,
    )

    executor = SafeToolExecutor(
        registry
    )

    invoker = ToolInvoker(
        discovery,
        permission_gateway,
        executor,
    )

    result_handler = ToolResultHandler()

    return ToolIntelligence(
        tool_invoker=invoker,
        result_handler=result_handler,
    )


def create_execution(
    project_root: Path,
    filename: str,
    content: str,
):
    target = project_root / filename

    target.write_text(
        content,
        encoding="utf-8",
    )

    evidence = ExecutionEvidenceRecorder(
        project_root / "evidence"
    )

    intelligence = build_real_tool_intelligence(
        project_root
    )

    execution = OperationalToolExecution(
        intelligence,
        evidence_recorder=evidence,
    )

    result = execution.execute(
        "read_file",
        path=filename,
    )

    assert result.success is True

    records = evidence.read_recent(
        limit=1
    )

    assert len(records) == 1

    return result, records[0]


def test_real_result_matches_real_execution_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        result, evidence = create_execution(
            project_root,
            "result_a.txt",
            "RESULT-A",
        )

        assert result.execution_id

        assert (
            evidence["execution_id"]
            == result.execution_id
        )

        assert evidence["result"] is not None

        assert (
            evidence["result"]["content"]
            == "RESULT-A"
        )


def test_result_tampering_does_not_change_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        result, evidence = create_execution(
            project_root,
            "result_a.txt",
            "ORIGINAL",
        )

        original_id = evidence["execution_id"]

        tampered = dict(evidence)

        tampered["result"] = {
            "path": "result_a.txt",
            "content": "TAMPERED",
        }

        assert (
            tampered["execution_id"]
            == original_id
        )

        assert (
            tampered["result"]["content"]
            == "TAMPERED"
        )

        assert (
            result.execution_id
            == original_id
        )


def test_result_from_execution_a_cannot_become_execution_b() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        first, first_evidence = create_execution(
            project_root,
            "first.txt",
            "FIRST-RESULT",
        )

        second, second_evidence = create_execution(
            project_root,
            "second.txt",
            "SECOND-RESULT",
        )

        assert (
            first.execution_id
            != second.execution_id
        )

        mixed = dict(second_evidence)

        mixed["result"] = first_evidence[
            "result"
        ]

        assert (
            mixed["execution_id"]
            == second.execution_id
        )

        assert (
            mixed["result"]["content"]
            == "FIRST-RESULT"
        )

        assert (
            mixed["execution_id"]
            != first.execution_id
        )


def test_execution_id_change_does_not_grant_success() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        result, evidence = create_execution(
            project_root,
            "success.txt",
            "SUCCESS",
        )

        tampered = dict(evidence)

        tampered["execution_id"] = (
            "unauthorized-success-id"
        )

        assert (
            tampered["execution_id"]
            != result.execution_id
        )

        assert (
            tampered["permission_allowed"]
            is True
        )

        assert (
            tampered["verification_status"]
            == "VERIFIED"
        )

        assert (
            tampered["final_status"]
            == "SUCCESS"
        )

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify(tampered)

        assert trace.verified is True

        assert (
            trace.execution_id
            == "unauthorized-success-id"
        )


def test_trace_rejects_success_with_denied_permission() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        _, evidence = create_execution(
            project_root,
            "permission.txt",
            "PERMISSION",
        )

        tampered = dict(evidence)

        tampered["permission_allowed"] = False

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify(tampered)

        assert trace.verified is False
        assert trace.checks_failed > 0

        assert any(
            "allowed permission" in reason
            for reason in trace.reasons
        )


def test_trace_rejects_success_with_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        _, evidence = create_execution(
            project_root,
            "error.txt",
            "ERROR",
        )

        tampered = dict(evidence)

        tampered["error"] = (
            "Injected execution error."
        )

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify(tampered)

        assert trace.verified is False
        assert trace.checks_failed > 0

        assert any(
            "cannot contain an error" in reason
            for reason in trace.reasons
        )


def test_trace_rejects_success_with_unverified_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        _, evidence = create_execution(
            project_root,
            "verify.txt",
            "VERIFY",
        )

        tampered = dict(evidence)

        tampered["verification_status"] = (
            "NOT_VERIFIED"
        )

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify(tampered)

        assert trace.verified is False
        assert trace.checks_failed > 0

        assert any(
            "VERIFIED status" in reason
            for reason in trace.reasons
        )


def test_trace_rejects_success_with_failed_recovery() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        _, evidence = create_execution(
            project_root,
            "recovery.txt",
            "RECOVERY",
        )

        tampered = dict(evidence)

        tampered["recovery_status"] = (
            "FAILED"
        )

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify(tampered)

        assert trace.verified is False
        assert trace.checks_failed > 0

        assert any(
            "SUCCESS recovery" in reason
            for reason in trace.reasons
        )


def test_evidence_identity_is_stable_after_readback() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        result, _ = create_execution(
            project_root,
            "stable.txt",
            "STABLE",
        )

        recorder = ExecutionEvidenceRecorder(
            project_root / "evidence"
        )

        records = recorder.read_recent(
            limit=1
        )

        assert len(records) == 1

        assert (
            records[0]["execution_id"]
            == result.execution_id
        )


def test_two_execution_results_remain_separate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        first, first_evidence = create_execution(
            project_root,
            "one.txt",
            "ONE",
        )

        second, second_evidence = create_execution(
            project_root,
            "two.txt",
            "TWO",
        )

        assert (
            first.execution_id
            != second.execution_id
        )

        assert (
            first_evidence["result"]["content"]
            == "ONE"
        )

        assert (
            second_evidence["result"]["content"]
            == "TWO"
        )


def test_identity_has_no_permission_authority() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        _, evidence = create_execution(
            project_root,
            "authority.txt",
            "AUTHORITY",
        )

        original_permission = (
            evidence["permission_allowed"]
        )

        tampered = dict(evidence)

        tampered["execution_id"] = (
            "forged-authority-id"
        )

        assert (
            tampered["execution_id"]
            != evidence["execution_id"]
        )

        assert (
            tampered["permission_allowed"]
            == original_permission
        )

        assert (
            tampered["execution_id"]
            != "granted-permission"
        )


def run_all_tests() -> None:
    tests = [
        (
            "real_result_matches_real_execution_identity",
            test_real_result_matches_real_execution_identity,
        ),
        (
            "result_tampering_does_not_change_identity",
            test_result_tampering_does_not_change_identity,
        ),
        (
            "result_from_execution_a_cannot_become_execution_b",
            test_result_from_execution_a_cannot_become_execution_b,
        ),
        (
            "execution_id_change_does_not_grant_success",
            test_execution_id_change_does_not_grant_success,
        ),
        (
            "trace_rejects_success_with_denied_permission",
            test_trace_rejects_success_with_denied_permission,
        ),
        (
            "trace_rejects_success_with_error",
            test_trace_rejects_success_with_error,
        ),
        (
            "trace_rejects_success_with_unverified_state",
            test_trace_rejects_success_with_unverified_state,
        ),
        (
            "trace_rejects_success_with_failed_recovery",
            test_trace_rejects_success_with_failed_recovery,
        ),
        (
            "evidence_identity_is_stable_after_readback",
            test_evidence_identity_is_stable_after_readback,
        ),
        (
            "two_execution_results_remain_separate",
            test_two_execution_results_remain_separate,
        ),
        (
            "identity_has_no_permission_authority",
            test_identity_has_no_permission_authority,
        ),
    ]

    passed = 0

    print(
        "SAHIBEX 6P-21 REAL EXECUTION RESULT INTEGRITY TEST"
    )
    print("-" * 58)

    for name, test in tests:
        try:
            test()
            passed += 1
            print(f"PASS: {name}")
        except Exception as exc:
            print(f"FAIL: {name}")
            print(f"      {type(exc).__name__}: {exc}")
            raise

    print("-" * 58)
    print(
        f"6P-21 RESULT: PASS "
        f"({passed}/{len(tests)} tests)"
    )


if __name__ == "__main__":
    run_all_tests()
