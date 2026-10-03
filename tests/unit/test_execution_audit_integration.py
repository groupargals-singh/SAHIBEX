from __future__ import annotations

import json
import tempfile
from pathlib import Path

from core.brain.operational_tool_execution import (
    OperationalToolExecution,
)
from core.policies.approval import PermissionEngine
from security.audit.audit_logger import AuditLogger
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
        name="audit_test_tool",
        description="read audit test information",
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


def test_execution_evidence_can_be_audited() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        evidence_recorder = ExecutionEvidenceRecorder(
            root / "evidence"
        )

        audit_logger = AuditLogger(
            root / "audit"
        )

        operational = build_pipeline(
            evidence_recorder
        )

        execution = operational.execute(
            "read audit test information",
            value="AUDIT TEST",
        )

        assert execution.success is True

        evidence = evidence_recorder.read_recent()

        assert len(evidence) == 1

        record = evidence[0]

        trace = ExecutionTraceVerifier().verify(
            record
        )

        assert trace.verified is True

        audit = audit_logger.record(
            request=execution.discovery_query,
            intent="read",
            intent_confidence=1.0,
            action="tool_execution",
            action_confidence=1.0,
            risk=execution.risk,
            permission_allowed=execution.allowed,
            confirmation_required=(
                execution.requires_confirmation
            ),
            reason=execution.reason,
        )

        assert audit["permission"] == "allowed"
        assert audit["confirmation_required"] is False

        recent = audit_logger.read_recent()

        assert len(recent) == 1
        assert recent[0]["request"] == (
            execution.discovery_query
        )


def test_audit_and_evidence_share_execution_context() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        evidence_recorder = ExecutionEvidenceRecorder(
            root / "evidence"
        )

        audit_logger = AuditLogger(
            root / "audit"
        )

        operational = build_pipeline(
            evidence_recorder
        )

        execution = operational.execute(
            "read audit test information",
            value="CONTEXT",
        )

        evidence = evidence_recorder.read_recent()

        assert len(evidence) == 1

        evidence_record = evidence[0]

        audit_logger.record(
            request=execution.discovery_query,
            intent="read",
            intent_confidence=1.0,
            action="tool_execution",
            action_confidence=1.0,
            risk=execution.risk,
            permission_allowed=execution.allowed,
            confirmation_required=(
                execution.requires_confirmation
            ),
            reason=execution.reason,
        )

        audit_records = audit_logger.read_recent()

        assert len(audit_records) == 1

        audit_record = audit_records[0]

        assert audit_record["request"] == (
            execution.discovery_query
        )

        assert audit_record["action"] == (
            evidence_record["action"]
        )

        assert audit_record["risk"] == (
            evidence_record["risk"]
        )

        assert audit_record["permission"] == "allowed"


def test_blocked_execution_produces_denied_audit() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        evidence_recorder = ExecutionEvidenceRecorder(
            root / "evidence"
        )

        audit_logger = AuditLogger(
            root / "audit"
        )

        operational = build_pipeline(
            evidence_recorder
        )

        execution = operational.execute(
        "zzzz_nonexistent_tool_987654"
        )

        assert execution.success is False
        assert execution.allowed is False

        evidence = evidence_recorder.read_recent()

        assert len(evidence) == 1

        trace = ExecutionTraceVerifier().verify(
            evidence[0]
        )

        assert trace.verified is True

        audit_logger.record(
            request=execution.discovery_query,
            intent="unknown",
            intent_confidence=0.0,
            action="tool_execution",
            action_confidence=0.0,
            risk=execution.risk,
            permission_allowed=execution.allowed,
            confirmation_required=(
                execution.requires_confirmation
            ),
            reason=execution.reason,
        )

        audit_records = audit_logger.read_recent()

        assert len(audit_records) == 1
        assert audit_records[0]["permission"] == "blocked"


def test_audit_does_not_modify_execution_evidence() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        evidence_recorder = ExecutionEvidenceRecorder(
            root / "evidence"
        )

        audit_logger = AuditLogger(
            root / "audit"
        )

        operational = build_pipeline(
            evidence_recorder
        )

        operational.execute(
            "read audit test information",
            value="IMMUTABLE",
        )

        before = (
            evidence_recorder.log_file.read_text(
                encoding="utf-8"
            )
        )

        evidence = evidence_recorder.read_recent()

        audit_logger.record(
            request="audit verification",
            intent="read",
            intent_confidence=1.0,
            action="tool_execution",
            action_confidence=1.0,
            risk=evidence[0]["risk"],
            permission_allowed=evidence[0][
                "permission_allowed"
            ],
            confirmation_required=evidence[0][
                "confirmation_required"
            ],
            reason=evidence[0]["reason"],
        )

        after = (
            evidence_recorder.log_file.read_text(
                encoding="utf-8"
            )
        )

        assert before == after


def test_audit_and_evidence_are_valid_jsonl() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        evidence_recorder = ExecutionEvidenceRecorder(
            root / "evidence"
        )

        audit_logger = AuditLogger(
            root / "audit"
        )

        operational = build_pipeline(
            evidence_recorder
        )

        operational.execute(
            "read audit test information",
            value="JSONL",
        )

        evidence_recorder.read_recent()

        evidence_lines = (
            evidence_recorder.log_file.read_text(
                encoding="utf-8"
            ).splitlines()
        )

        assert len(evidence_lines) == 1
        json.loads(evidence_lines[0])

        audit_logger.record(
            request="JSONL audit",
            intent="read",
            intent_confidence=1.0,
            action="tool_execution",
            action_confidence=1.0,
            risk="low",
            permission_allowed=True,
            confirmation_required=False,
            reason="Audit test.",
        )

        audit_lines = (
            audit_logger.log_file.read_text(
                encoding="utf-8"
            ).splitlines()
        )

        assert len(audit_lines) == 1
        json.loads(audit_lines[0])


def test_audit_logger_has_no_execution_authority() -> None:
    with tempfile.TemporaryDirectory() as directory:
        logger = AuditLogger(Path(directory))

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

        public_methods = set(dir(logger))

        assert not (
            forbidden_methods & public_methods
        )


def run_all_tests() -> None:
    test_execution_evidence_can_be_audited()
    test_audit_and_evidence_share_execution_context()
    test_blocked_execution_produces_denied_audit()
    test_audit_does_not_modify_execution_evidence()
    test_audit_and_evidence_are_valid_jsonl()
    test_audit_logger_has_no_execution_authority()


if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-12 EXECUTION AUDIT INTEGRATION TEST: PASS"
    )
