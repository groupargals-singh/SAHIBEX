from __future__ import annotations

import tempfile
from pathlib import Path

from core.brain.operational_tool_execution import OperationalToolExecution
from core.brain.operational_verification import OperationalVerificationRecovery
from core.policies.approval import PermissionEngine
from security.audit.audit_logger import AuditLogger
from security.audit.execution_evidence import ExecutionEvidenceRecorder
from security.audit.execution_trace import ExecutionTraceVerifier
from tools.discovery import ToolDiscovery
from tools.executor import SafeToolExecutor
from tools.intelligence import ToolIntelligence
from tools.invocation import ToolInvoker
from tools.permission_gateway import ToolPermissionGateway
from tools.registry import build_default_registry
from tools.result_handler import ToolResultHandler


def build_real_tool_intelligence(
    project_root: Path,
) -> ToolIntelligence:
    registry = build_default_registry(project_root)

    discovery = ToolDiscovery(registry)

    permission_engine = PermissionEngine()

    permission_gateway = ToolPermissionGateway(
        permission_engine,
        registry,
    )

    executor = SafeToolExecutor(registry)

    invoker = ToolInvoker(
        discovery,
        permission_gateway,
        executor,
    )

    result_handler = ToolResultHandler()

    verification = OperationalVerificationRecovery()

    return ToolIntelligence(
        tool_invoker=invoker,
        result_handler=result_handler,
        operational_verification=verification,
    )


def test_real_execution_provenance_trace_audit_identity_chain() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        target = project_root / "integration_test.txt"
        target.write_text(
            "SAHIBEX 6P-23 integration test.",
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
            path="integration_test.txt",
        )

        assert result.success is True
        assert result.execution_id

        records = evidence.read_recent(limit=1)

        assert len(records) == 1

        record = records[0]

        assert record["execution_id"] == result.execution_id
        assert record["provenance"]

        verifier = ExecutionTraceVerifier()

        trace = verifier.verify_provenance(
            record,
            project_root / "evidence",
        )

        assert trace.verified is True
        assert trace.execution_id == result.execution_id

        audit_event = audit.record(
            request=result.discovery_query,
            intent="read",
            intent_confidence=0.95,
            action="read_file",
            action_confidence=0.95,
            risk=result.risk,
            permission_allowed=result.allowed,
            confirmation_required=result.requires_confirmation,
            reason=result.reason,
            execution_id=result.execution_id,
        )

        assert audit_event["execution_id"] == result.execution_id

        audit_records = audit.read_recent(limit=1)

        assert len(audit_records) == 1

        assert (
            audit_records[0]["execution_id"]
            == record["execution_id"]
            == trace.execution_id
            == result.execution_id
        )


def test_provenance_tampering_breaks_full_trace_chain() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        target = project_root / "tamper_test.txt"
        target.write_text(
            "SAHIBEX 6P-23 tamper test.",
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
            path="tamper_test.txt",
        )

        assert result.success is True

        records = evidence.read_recent(limit=1)
        assert len(records) == 1

        original = records[0]

        valid_trace = ExecutionTraceVerifier().verify_provenance(
            original,
            project_root / "evidence",
        )

        assert valid_trace.verified is True

        tampered = dict(original)
        tampered["execution_id"] = "forged-6p23-execution"

        invalid_trace = ExecutionTraceVerifier().verify_provenance(
            tampered,
            project_root / "evidence",
        )

        assert invalid_trace.verified is False


def test_audit_identity_does_not_replace_provenance_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        target = project_root / "boundary_test.txt"
        target.write_text(
            "SAHIBEX 6P-23 authority boundary.",
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
            path="boundary_test.txt",
        )

        assert result.success is True

        record = evidence.read_recent(limit=1)[0]

        valid_trace = ExecutionTraceVerifier().verify_provenance(
            record,
            project_root / "evidence",
        )

        assert valid_trace.verified is True

        audit_event = audit.record(
            request=result.discovery_query,
            intent="read",
            intent_confidence=0.95,
            action="read_file",
            action_confidence=0.95,
            risk=result.risk,
            permission_allowed=result.allowed,
            confirmation_required=result.requires_confirmation,
            reason=result.reason,
            execution_id="different-audit-identity",
        )

        assert (
            audit_event["execution_id"]
            != result.execution_id
        )

        assert (
            record["execution_id"]
            == result.execution_id
        )

        assert (
            valid_trace.execution_id
            == result.execution_id
        )


def test_provenance_trace_has_no_permission_authority() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)

        target = project_root / "authority_test.txt"
        target.write_text(
            "SAHIBEX 6P-23 permission boundary.",
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
            path="authority_test.txt",
        )

        assert result.success is True

        record = evidence.read_recent(limit=1)[0]

        trace = ExecutionTraceVerifier().verify_provenance(
            record,
            project_root / "evidence",
        )

        assert trace.verified is True

        assert record["permission_allowed"] is True

        tampered = dict(record)
        tampered["permission_allowed"] = False

        rejected = ExecutionTraceVerifier().verify_provenance(
            tampered,
            project_root / "evidence",
        )

        assert rejected.verified is False


def run_all_tests() -> None:
    test_real_execution_provenance_trace_audit_identity_chain()
    test_provenance_tampering_breaks_full_trace_chain()
    test_audit_identity_does_not_replace_provenance_identity()
    test_provenance_trace_has_no_permission_authority()


if __name__ == "__main__":
    run_all_tests()
    print(
        "SAHIBEX 6P-23 PROVENANCE + TRACE + AUDIT "
        "INTEGRATION TEST: PASS"
    )
