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
        name="trace_test_tool",
        description="read trace test information",
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


def test_real_execution_evidence_can_be_verified() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        operational = build_pipeline(recorder)

        execution = operational.execute(
            "read trace test information",
            value="TRACE VERIFIED",
        )

        assert execution.success is True

        records = recorder.read_recent()

        assert len(records) == 1

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify(records[0])

        assert trace.verified is True
        assert trace.execution_id == execution.execution_id
        assert trace.checks_failed == 0


def test_trace_reads_the_actual_jsonl_record() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        operational = build_pipeline(recorder)

        execution = operational.execute(
            "read trace test information",
            value="JSONL TRACE",
        )

        raw_lines = recorder.log_file.read_text(
            encoding="utf-8"
        ).splitlines()

        assert len(raw_lines) == 1

        raw_record = json.loads(raw_lines[0])

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify(raw_record)

        assert trace.verified is True
        assert (
            trace.execution_id
            == execution.execution_id
        )


def test_tampered_permission_state_is_detected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        operational = build_pipeline(recorder)

        execution = operational.execute(
            "read trace test information",
            value="ORIGINAL",
        )

        records = recorder.read_recent()

        assert len(records) == 1
        assert execution.success is True

        tampered = dict(records[0])

        tampered["permission_allowed"] = False

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify(tampered)

        assert trace.verified is False
        assert trace.execution_id == execution.execution_id


def test_tampered_verification_state_is_detected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        operational = build_pipeline(recorder)

        execution = operational.execute(
            "read trace test information",
            value="ORIGINAL",
        )

        records = recorder.read_recent()

        assert len(records) == 1
        assert execution.success is True

        tampered = dict(records[0])

        tampered["verification_status"] = (
            "NOT_VERIFIED"
        )

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify(tampered)

        assert trace.verified is False


def test_tampered_final_status_is_detected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        operational = build_pipeline(recorder)

        execution = operational.execute(
            "read trace test information",
            value="ORIGINAL",
        )

        records = recorder.read_recent()

        assert len(records) == 1
        assert execution.success is True

        tampered = dict(records[0])

        tampered["final_status"] = "FAILED"
        tampered["error"] = "Tampered failure."

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify(tampered)

        assert trace.verified is False


def test_execution_ids_are_traceable_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        operational = build_pipeline(recorder)

        first = operational.execute(
            "read trace test information",
            value="FIRST",
        )

        second = operational.execute(
            "read trace test information",
            value="SECOND",
        )

        records = recorder.read_recent()

        assert len(records) == 2

        ids = {
            records[0]["execution_id"],
            records[1]["execution_id"],
        }

        assert first.execution_id in ids
        assert second.execution_id in ids
        assert first.execution_id != second.execution_id


def test_trace_verifier_does_not_change_evidence() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        operational = build_pipeline(recorder)

        operational.execute(
            "read trace test information",
            value="IMMUTABLE CHECK",
        )

        before = recorder.log_file.read_text(
            encoding="utf-8"
        )

        records = recorder.read_recent()

        verifier = ExecutionTraceVerifier()

        verifier.verify(records[0])

        after = recorder.log_file.read_text(
            encoding="utf-8"
        )

        assert before == after


def run_all_tests() -> None:
    test_real_execution_evidence_can_be_verified()
    test_trace_reads_the_actual_jsonl_record()
    test_tampered_permission_state_is_detected()
    test_tampered_verification_state_is_detected()
    test_tampered_final_status_is_detected()
    test_execution_ids_are_traceable_end_to_end()
    test_trace_verifier_does_not_change_evidence()


if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-11 EXECUTION TRACE INTEGRATION TEST: PASS"
    )
