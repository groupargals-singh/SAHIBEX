from __future__ import annotations

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


def build_system(
    root: Path,
) -> tuple[
    OperationalToolExecution,
    ExecutionEvidenceRecorder,
    AuditLogger,
]:
    registry = ToolRegistry()

    registry.register(
        name="e2e_integrity_tool",
        description="read end to end integrity information",
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

    evidence_recorder = ExecutionEvidenceRecorder(
        root / "evidence"
    )

    audit_logger = AuditLogger(
        root / "audit"
    )

    operational = OperationalToolExecution(
        intelligence,
        evidence_recorder,
    )

    return (
        operational,
        evidence_recorder,
        audit_logger,
    )


def test_complete_success_path() -> None:
    with tempfile.TemporaryDirectory() as directory:
        (
            operational,
            evidence_recorder,
            audit_logger,
        ) = build_system(Path(directory))

        result = operational.execute(
            "read end to end integrity information",
            value="E2E SUCCESS",
        )

        assert result.success is True
        assert result.allowed is True
        assert result.error is None
        assert result.result == "E2E SUCCESS"

        evidence = evidence_recorder.read_recent()

        assert len(evidence) == 1

        trace = ExecutionTraceVerifier().verify(
            evidence[0]
        )

        assert trace.verified is True
        assert (
            trace.execution_id
            == result.execution_id
        )

        audit_logger.record(
            request=result.discovery_query,
            intent="read",
            intent_confidence=1.0,
            action="tool_execution",
            action_confidence=1.0,
            risk=result.risk,
            permission_allowed=result.allowed,
            confirmation_required=(
                result.requires_confirmation
            ),
            reason=result.reason,
        )

        audit = audit_logger.read_recent()

        assert len(audit) == 1
        assert audit[0]["permission"] == "allowed"


def test_unknown_tool_cannot_become_success() -> None:
    with tempfile.TemporaryDirectory() as directory:
        (
            operational,
            evidence_recorder,
            audit_logger,
        ) = build_system(Path(directory))

        result = operational.execute(
            "zzzz_nonexistent_tool_987654",
        )

        assert result.success is False
        assert result.allowed is False
        assert result.result is None

        evidence = evidence_recorder.read_recent()

        assert len(evidence) == 1
        assert evidence[0]["final_status"] == "BLOCKED"

        trace = ExecutionTraceVerifier().verify(
            evidence[0]
        )

        assert trace.verified is True

        audit_logger.record(
            request=result.discovery_query,
            intent="unknown",
            intent_confidence=0.0,
            action="tool_execution",
            action_confidence=0.0,
            risk=result.risk,
            permission_allowed=result.allowed,
            confirmation_required=(
                result.requires_confirmation
            ),
            reason=result.reason,
        )

        audit = audit_logger.read_recent()

        assert audit[0]["permission"] == "blocked"


def test_failed_result_cannot_claim_success() -> None:
    with tempfile.TemporaryDirectory() as directory:
        (
            operational,
            evidence_recorder,
            _audit_logger,
        ) = build_system(Path(directory))

        result = operational.execute(
            "zzzz_nonexistent_tool_failure",
        )

        assert result.success is False
        assert result.result is None

        evidence = evidence_recorder.read_recent()

        assert len(evidence) == 1

        record = evidence[0]

        assert record["final_status"] != "SUCCESS"
        assert record["verification_status"] != "VERIFIED"

        trace = ExecutionTraceVerifier().verify(
            record
        )

        assert trace.verified is True


def test_tampered_success_trace_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        (
            operational,
            evidence_recorder,
            _audit_logger,
        ) = build_system(Path(directory))

        result = operational.execute(
            "read end to end integrity information",
            value="REAL RESULT",
        )

        assert result.success is True

        evidence = evidence_recorder.read_recent()

        assert len(evidence) == 1

        tampered = dict(evidence[0])

        tampered["permission_allowed"] = False

        trace = ExecutionTraceVerifier().verify(
            tampered
        )

        assert trace.verified is False


def test_execution_id_is_preserved_across_chain() -> None:
    with tempfile.TemporaryDirectory() as directory:
        (
            operational,
            evidence_recorder,
            _audit_logger,
        ) = build_system(Path(directory))

        result = operational.execute(
            "read end to end integrity information",
            value="IDENTITY",
        )

        evidence = evidence_recorder.read_recent()

        assert len(evidence) == 1

        assert (
            evidence[0]["execution_id"]
            == result.execution_id
        )

        trace = ExecutionTraceVerifier().verify(
            evidence[0]
        )

        assert trace.execution_id == (
            result.execution_id
        )


def test_multiple_executions_remain_distinct() -> None:
    with tempfile.TemporaryDirectory() as directory:
        (
            operational,
            evidence_recorder,
            _audit_logger,
        ) = build_system(Path(directory))

        first = operational.execute(
            "read end to end integrity information",
            value="FIRST",
        )

        second = operational.execute(
            "read end to end integrity information",
            value="SECOND",
        )

        assert first.success is True
        assert second.success is True

        assert first.execution_id != (
            second.execution_id
        )

        evidence = evidence_recorder.read_recent()

        assert len(evidence) == 2

        ids = {
            evidence[0]["execution_id"],
            evidence[1]["execution_id"],
        }

        assert first.execution_id in ids
        assert second.execution_id in ids


def test_audit_cannot_upgrade_blocked_execution() -> None:
    with tempfile.TemporaryDirectory() as directory:
        (
            operational,
            evidence_recorder,
            audit_logger,
        ) = build_system(Path(directory))

        result = operational.execute(
            "zzzz_blocked_execution_123456",
        )

        assert result.success is False
        assert result.allowed is False

        audit_logger.record(
            request=result.discovery_query,
            intent="unknown",
            intent_confidence=0.0,
            action="tool_execution",
            action_confidence=0.0,
            risk=result.risk,
            permission_allowed=result.allowed,
            confirmation_required=(
                result.requires_confirmation
            ),
            reason=result.reason,
        )

        evidence = evidence_recorder.read_recent()
        audit = audit_logger.read_recent()

        assert evidence[0]["final_status"] == (
            "BLOCKED"
        )

        assert audit[0]["permission"] == "blocked"


def test_trace_verification_does_not_change_result() -> None:
    with tempfile.TemporaryDirectory() as directory:
        (
            operational,
            evidence_recorder,
            _audit_logger,
        ) = build_system(Path(directory))

        result = operational.execute(
            "read end to end integrity information",
            value="IMMUTABLE RESULT",
        )

        original_result = result.result
        original_id = result.execution_id

        evidence = evidence_recorder.read_recent()

        trace = ExecutionTraceVerifier().verify(
            evidence[0]
        )

        assert trace.verified is True
        assert result.result == original_result
        assert result.execution_id == original_id


def test_protected_authority_methods_are_not_created() -> None:
    with tempfile.TemporaryDirectory() as directory:
        (
            operational,
            _evidence_recorder,
            _audit_logger,
        ) = build_system(Path(directory))

        forbidden = {
            "grant_permission",
            "modify_constitution",
            "update_constitution",
            "delete_file",
            "write_file",
            "run_command",
            "change_permission",
        }

        public_methods = set(dir(operational))

        assert not (
            forbidden & public_methods
        )


def run_all_tests() -> None:
    test_complete_success_path()
    test_unknown_tool_cannot_become_success()
    test_failed_result_cannot_claim_success()
    test_tampered_success_trace_is_rejected()
    test_execution_id_is_preserved_across_chain()
    test_multiple_executions_remain_distinct()
    test_audit_cannot_upgrade_blocked_execution()
    test_trace_verification_does_not_change_result()
    test_protected_authority_methods_are_not_created()


if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-13 END-TO-END OPERATIONAL INTEGRITY TEST: PASS"
    )
