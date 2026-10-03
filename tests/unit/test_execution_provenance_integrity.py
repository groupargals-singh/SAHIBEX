from __future__ import annotations

import json
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
from tools.failure_recovery import ToolFailureRecovery
from tools.intelligence import ToolIntelligence
from tools.invocation import ToolInvoker
from tools.permission_gateway import ToolPermissionGateway
from tools.registry import ToolRegistry
from tools.result_handler import ToolResultHandler


def build_pipeline(
    recorder: ExecutionEvidenceRecorder,
) -> OperationalToolExecution:
    registry = ToolRegistry()

    registry.register(
        name="provenance_test_tool",
        description="6P-22 provenance test tool",
        handler=lambda value="OK": value,
        read_only=True,
        requires_confirmation=False,
    )

    discovery = ToolDiscovery(registry)

    permission_gateway = ToolPermissionGateway(
        PermissionEngine(),
        registry,
    )

    executor = SafeToolExecutor(registry)

    invoker = ToolInvoker(
        discovery,
        permission_gateway,
        executor,
    )

    intelligence = ToolIntelligence(
        invoker,
        ToolResultHandler(),
        ToolFailureRecovery(),
    )

    return OperationalToolExecution(
        intelligence,
        recorder,
    )


def test_real_execution_has_authenticated_provenance() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        recorder = ExecutionEvidenceRecorder(root)

        operational = build_pipeline(
            recorder
        )

        execution = operational.execute(
            "6P-22 provenance test",
            value="AUTHENTIC",
        )

        assert execution.success is True

        records = recorder.read_recent()

        assert len(records) == 1

        evidence = records[0]

        assert evidence["execution_id"] == (
            execution.execution_id
        )

        assert isinstance(
            evidence.get("provenance"),
            str,
        )

        assert evidence["provenance"]


def test_real_provenance_verifies() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        recorder = ExecutionEvidenceRecorder(root)

        operational = build_pipeline(
            recorder
        )

        execution = operational.execute(
            "6P-22 provenance verification",
            value="VERIFIED",
        )

        assert execution.success is True

        evidence = recorder.read_recent()[0]

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify_provenance(
            evidence,
            root,
        )

        assert trace.verified is True

        assert (
            trace.execution_id
            == execution.execution_id
        )


def test_execution_id_tampering_breaks_provenance() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        recorder = ExecutionEvidenceRecorder(root)

        operational = build_pipeline(
            recorder
        )

        execution = operational.execute(
            "6P-22 identity tampering",
            value="ORIGINAL",
        )

        assert execution.success is True

        evidence = dict(
            recorder.read_recent()[0]
        )

        evidence["execution_id"] = (
            "unauthorized-success-id"
        )

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify_provenance(
            evidence,
            root,
        )

        assert trace.verified is False

        assert (
            "Provenance authentication failed."
            in trace.reasons
        )


def test_result_tampering_breaks_provenance() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        recorder = ExecutionEvidenceRecorder(root)

        operational = build_pipeline(
            recorder
        )

        operational.execute(
            "6P-22 result tampering",
            value="ORIGINAL",
        )

        evidence = dict(
            recorder.read_recent()[0]
        )

        evidence["result"] = {
            "tampered": True,
        }

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify_provenance(
            evidence,
            root,
        )

        assert trace.verified is False


def test_permission_tampering_breaks_provenance() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        recorder = ExecutionEvidenceRecorder(root)

        operational = build_pipeline(
            recorder
        )

        operational.execute(
            "6P-22 permission tampering",
            value="ORIGINAL",
        )

        evidence = dict(
            recorder.read_recent()[0]
        )

        evidence["permission_allowed"] = False

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify_provenance(
            evidence,
            root,
        )

        assert trace.verified is False


def test_provenance_cannot_be_fabricated_with_new_id() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        recorder = ExecutionEvidenceRecorder(root)

        operational = build_pipeline(
            recorder
        )

        operational.execute(
            "6P-22 forged identity",
            value="REAL",
        )

        evidence = dict(
            recorder.read_recent()[0]
        )

        original_proof = evidence[
            "provenance"
        ]

        evidence["execution_id"] = (
            "forged-execution-id"
        )

        evidence["provenance"] = original_proof

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify_provenance(
            evidence,
            root,
        )

        assert trace.verified is False


def test_missing_provenance_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        recorder = ExecutionEvidenceRecorder(root)

        operational = build_pipeline(
            recorder
        )

        operational.execute(
            "6P-22 missing provenance",
            value="REAL",
        )

        evidence = dict(
            recorder.read_recent()[0]
        )

        evidence.pop(
            "provenance",
            None,
        )

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify_provenance(
            evidence,
            root,
        )

        assert trace.verified is False

        assert (
            "Missing provenance proof."
            in trace.reasons
        )


def test_provenance_readback_is_stable() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        recorder = ExecutionEvidenceRecorder(root)

        operational = build_pipeline(
            recorder
        )

        operational.execute(
            "6P-22 JSONL readback",
            value="READBACK",
        )

        raw_line = (
            recorder.log_file.read_text(
                encoding="utf-8"
            )
            .splitlines()[0]
        )

        evidence = json.loads(
            raw_line
        )

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify_provenance(
            evidence,
            root,
        )

        assert trace.verified is True


def test_provenance_does_not_grant_permission() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        recorder = ExecutionEvidenceRecorder(root)

        operational = build_pipeline(
            recorder
        )

        operational.execute(
            "6P-22 authority separation",
            value="REAL",
        )

        evidence = dict(
            recorder.read_recent()[0]
        )

        evidence["permission_allowed"] = False
        evidence["final_status"] = "BLOCKED"
        evidence["verification_status"] = (
            "NOT_VERIFIED"
        )
        evidence["recovery_status"] = "BLOCKED"
        evidence["error"] = (
            "Permission required."
        )

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify_provenance(
            evidence,
            root,
        )

        assert trace.verified is False


def test_old_consistency_verifier_remains_compatible() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        recorder = ExecutionEvidenceRecorder(root)

        operational = build_pipeline(
            recorder
        )

        execution = operational.execute(
            "6P-22 backward compatibility",
            value="COMPATIBLE",
        )

        evidence = recorder.read_recent()[0]

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify(
            evidence
        )

        assert trace.verified is True

        assert (
            trace.execution_id
            == execution.execution_id
        )


def run_all_tests() -> None:
    test_real_execution_has_authenticated_provenance()
    test_real_provenance_verifies()
    test_execution_id_tampering_breaks_provenance()
    test_result_tampering_breaks_provenance()
    test_permission_tampering_breaks_provenance()
    test_provenance_cannot_be_fabricated_with_new_id()
    test_missing_provenance_is_rejected()
    test_provenance_readback_is_stable()
    test_provenance_does_not_grant_permission()
    test_old_consistency_verifier_remains_compatible()


if __name__ == "__main__":
    run_all_tests()
    print(
        "SAHIBEX 6P-22 EXECUTION IDENTITY "
        "AUTHENTICITY & PROVENANCE TEST: PASS"
    )
