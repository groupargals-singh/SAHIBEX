from __future__ import annotations

import json
import tempfile
from pathlib import Path

from core.brain.operational_tool_execution import (
    OperationalToolExecution,
)
from core.brain.operational_verification import (
    OperationalVerificationRecovery,
)
from core.policies.approval import PermissionEngine
from security.audit.execution_evidence import (
    ExecutionEvidenceRecorder,
)
from security.audit.execution_trace import (
    ExecutionTraceVerifier,
)
from security.audit.audit_logger import AuditLogger
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

    verification = (
        OperationalVerificationRecovery()
    )

    return ToolIntelligence(
        tool_invoker=invoker,
        result_handler=result_handler,
        operational_verification=verification,
    )


def test_real_execution_creates_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        target = (
            project_root / "identity_test.txt"
        )

        target.write_text(
            "SAHIBEX 6P-20 identity test.",
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
            path="identity_test.txt",
        )

        assert result.success is True
        assert result.execution_id
        assert result.tool == "read_file"


def test_execution_evidence_contains_same_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        (
            project_root / "identity_test.txt"
        ).write_text(
            "identity binding",
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
            path="identity_test.txt",
        )

        records = evidence.read_recent(
            limit=1
        )

        assert len(records) == 1
        assert (
            records[0]["execution_id"]
            == result.execution_id
        )


def test_audit_and_evidence_share_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        (
            project_root / "identity_test.txt"
        ).write_text(
            "three layer binding",
            encoding="utf-8",
        )

        evidence = ExecutionEvidenceRecorder(
            project_root / "evidence"
        )

        audit = AuditLogger(
            project_root / "audit"
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
            path="identity_test.txt",
        )

        audit_event = audit.record(
            request=result.discovery_query,
            intent="read",
            intent_confidence=0.95,
            action="read_file",
            action_confidence=0.95,
            risk=result.risk,
            permission_allowed=result.allowed,
            confirmation_required=(
                result.requires_confirmation
            ),
            reason=result.reason,
            execution_id=result.execution_id,
        )

        evidence_records = evidence.read_recent(
            limit=1
        )

        assert (
            evidence_records[0]["execution_id"]
            == result.execution_id
        )

        assert (
            audit_event["execution_id"]
            == result.execution_id
        )

        assert (
            evidence_records[0]["execution_id"]
            == audit_event["execution_id"]
        )


def test_trace_accepts_real_execution_evidence() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        (
            project_root / "identity_test.txt"
        ).write_text(
            "trace verification",
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
            path="identity_test.txt",
        )

        records = evidence.read_recent(
            limit=1
        )

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify(
            records[0]
        )

        assert trace.verified is True
        assert (
            trace.execution_id
            == result.execution_id
        )


def test_tampered_execution_identity_is_detectable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        (
            project_root / "identity_test.txt"
        ).write_text(
            "tamper test",
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
            path="identity_test.txt",
        )

        records = evidence.read_recent(
            limit=1
        )

        original_id = records[0][
            "execution_id"
        ]

        tampered = dict(records[0])

        tampered["execution_id"] = (
            "tampered-execution-id"
        )

        assert (
            tampered["execution_id"]
            != original_id
        )

        assert (
            result.execution_id
            == original_id
        )


def test_two_real_executions_have_distinct_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        (
            project_root / "first.txt"
        ).write_text(
            "first",
            encoding="utf-8",
        )

        (
            project_root / "second.txt"
        ).write_text(
            "second",
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

        first = execution.execute(
            "read_file",
            path="first.txt",
        )

        second = execution.execute(
            "read_file",
            path="second.txt",
        )

        assert first.success is True
        assert second.success is True

        assert first.execution_id
        assert second.execution_id

        assert (
            first.execution_id
            != second.execution_id
        )


def test_identity_cannot_grant_permission() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        (
            project_root / "identity_test.txt"
        ).write_text(
            "permission boundary",
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
            path="identity_test.txt",
        )

        records = evidence.read_recent(
            limit=1
        )

        tampered = dict(records[0])

        tampered["execution_id"] = (
            "different-identity"
        )

        assert (
            tampered["permission_allowed"]
            == records[0]["permission_allowed"]
        )

        assert (
            result.allowed
            is records[0]["permission_allowed"]
        )


def test_audit_identity_is_persisted_as_json() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        audit = AuditLogger(
            Path(tmp)
        )

        audit.record(
            request="6P-20 audit test",
            intent="read",
            intent_confidence=0.95,
            action="read_file",
            action_confidence=0.95,
            risk="low",
            permission_allowed=True,
            confirmation_required=False,
            reason="6P-20 audit persistence.",
            execution_id="6P20-execution-A",
        )

        lines = audit.log_file.read_text(
            encoding="utf-8"
        ).splitlines()

        assert len(lines) == 1

        event = json.loads(lines[0])

        assert (
            event["execution_id"]
            == "6P20-execution-A"
        )


def run_all_tests() -> None:
    test_real_execution_creates_identity()
    test_execution_evidence_contains_same_identity()
    test_audit_and_evidence_share_identity()
    test_trace_accepts_real_execution_evidence()
    test_tampered_execution_identity_is_detectable()
    test_two_real_executions_have_distinct_identity()
    test_identity_cannot_grant_permission()
    test_audit_identity_is_persisted_as_json()


if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-20 REAL 3-LAYER IDENTITY BINDING TEST: PASS"
    )
