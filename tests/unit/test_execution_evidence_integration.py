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
from tools.discovery import ToolDiscovery
from tools.executor import SafeToolExecutor
from tools.failure_recovery import ToolFailureRecovery
from tools.intelligence import ToolIntelligence
from tools.invocation import ToolInvoker
from tools.permission_gateway import ToolPermissionGateway
from tools.registry import ToolRegistry
from tools.result_handler import ToolResultHandler


def build_pipeline(
    evidence_recorder: ExecutionEvidenceRecorder,
) -> OperationalToolExecution:
    registry = ToolRegistry()

    registry.register(
        name="evidence_test_tool",
        description="read evidence test information",
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

    result_handler = ToolResultHandler()
    recovery = ToolFailureRecovery()

    intelligence = ToolIntelligence(
        invoker,
        result_handler,
        recovery,
    )

    return OperationalToolExecution(
        intelligence,
        evidence_recorder,
    )


def test_successful_execution_creates_evidence() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        operational = build_pipeline(recorder)

        result = operational.execute(
            "read evidence test information",
            value="EVIDENCE RESULT",
        )

        assert result.success is True
        assert result.allowed is True
        assert result.tool == "evidence_test_tool"
        assert result.result == "EVIDENCE RESULT"
        assert result.execution_id

        records = recorder.read_recent()

        assert len(records) == 1

        record = records[0]

        assert record["execution_id"] == result.execution_id
        assert record["tool"] == "evidence_test_tool"
        assert record["action"] == "tool_execution"
        assert record["permission_allowed"] is True
        assert record["confirmation_required"] is False
        assert record["confirmation_provided"] is False
        assert record["attempts"] == 1
        assert record["result"] == "EVIDENCE RESULT"
        assert record["verification_status"] == "VERIFIED"
        assert record["recovery_status"] == "SUCCESS"
        assert record["final_status"] == "SUCCESS"
        assert record["error"] is None


def test_blocked_execution_creates_blocked_evidence() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        operational = build_pipeline(recorder)

        result = operational.execute(
            "zzzz_unknown_evidence_tool_987654",
        )

        assert result.success is False
        assert result.allowed is False
        assert result.result is None
        assert result.execution_id

        records = recorder.read_recent()

        assert len(records) == 1

        record = records[0]

        assert record["execution_id"] == result.execution_id
        assert record["tool"] == "unknown"
        assert record["permission_allowed"] is False
        assert record["verification_status"] == "NOT_VERIFIED"
        assert record["recovery_status"] == "BLOCKED"
        assert record["final_status"] == "BLOCKED"
        assert record["error"] is not None


def test_evidence_jsonl_contains_valid_json() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        operational = build_pipeline(recorder)

        operational.execute(
            "read evidence test information",
            value="JSON TEST",
        )

        lines = recorder.log_file.read_text(
            encoding="utf-8"
        ).splitlines()

        assert len(lines) == 1

        parsed = json.loads(lines[0])

        assert parsed["final_status"] == "SUCCESS"


def test_operational_result_and_evidence_share_execution_id() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        operational = build_pipeline(recorder)

        result = operational.execute(
            "read evidence test information",
            value="ID MATCH",
        )

        records = recorder.read_recent()

        assert len(records) == 1
        assert records[0]["execution_id"] == result.execution_id


def test_evidence_recorder_does_not_grant_authority() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        forbidden_methods = {
            "execute",
            "invoke",
            "grant_permission",
            "require_permission",
            "override_permission",
            "modify_constitution",
            "update_constitution",
            "write_file",
            "delete_file",
            "run_command",
        }

        public_methods = set(dir(recorder))

        assert not (
            forbidden_methods & public_methods
        )


def run_all_tests() -> None:
    test_successful_execution_creates_evidence()
    test_blocked_execution_creates_blocked_evidence()
    test_evidence_jsonl_contains_valid_json()
    test_operational_result_and_evidence_share_execution_id()
    test_evidence_recorder_does_not_grant_authority()


if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-10 EXECUTION EVIDENCE INTEGRATION TEST: PASS"
    )
