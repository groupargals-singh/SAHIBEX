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
from tools.failure_recovery import ToolFailureRecovery
from tools.intelligence import ToolIntelligence
from tools.invocation import ToolInvoker
from tools.permission_gateway import ToolPermissionGateway
from tools.registry import ToolRegistry
from tools.result_handler import ToolResultHandler


class TemporaryError(Exception):
    """Test-only retryable failure."""

    pass


class ControlledFailureTool:
    """
    Fails once with a retryable TemporaryError,
    then succeeds.
    """

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, value: str = "OK") -> str:
        self.calls += 1

        if self.calls == 1:
            raise TemporaryError(
                "Injected temporary failure."
            )

        return value


class PermanentFailureTool:
    """
    Always fails with a non-retryable RuntimeError.
    """

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, value: str = "FAIL") -> str:
        self.calls += 1

        raise RuntimeError(
            "Injected permanent failure."
        )


def build_system(
    root: Path,
    handler,
) -> tuple[
    OperationalToolExecution,
    ExecutionEvidenceRecorder,
]:
    registry = ToolRegistry()

    registry.register(
        name="failure_test_tool",
        description="controlled failure recovery tool",
        handler=handler,
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

    operational = OperationalToolExecution(
        intelligence,
        evidence_recorder,
    )

    return operational, evidence_recorder


def test_temporary_failure_can_recover() -> None:
    with tempfile.TemporaryDirectory() as directory:
        tool = ControlledFailureTool()

        operational, recorder = build_system(
            Path(directory),
            tool,
        )

        result = operational.execute(
            "controlled failure recovery tool",
            max_attempts=3,
            value="RECOVERED",
        )

        assert result.success is True
        assert result.result == "RECOVERED"
        assert result.error is None
        assert result.attempts >= 2
        assert tool.calls == 2

        evidence = recorder.read_recent()

        assert len(evidence) == 1
        assert evidence[0]["final_status"] == "SUCCESS"
        assert evidence[0]["verification_status"] == "VERIFIED"
        assert evidence[0]["recovery_status"] == "SUCCESS"

        trace = ExecutionTraceVerifier().verify(
            evidence[0]
        )

        assert trace.verified is True
        assert (
            trace.execution_id
            == result.execution_id
        )


def test_permanent_failure_cannot_become_success() -> None:
    with tempfile.TemporaryDirectory() as directory:
        tool = PermanentFailureTool()

        operational, recorder = build_system(
            Path(directory),
            tool,
        )

        result = operational.execute(
            "controlled failure recovery tool",
            max_attempts=3,
            value="SHOULD NOT SUCCEED",
        )

        assert result.success is False
        assert result.result is None
        assert result.error is not None
        assert result.recovery_status == "FAILED"
        assert result.retryable is False
        assert tool.calls == 1

        evidence = recorder.read_recent()

        assert len(evidence) == 1
        assert evidence[0]["final_status"] == "FAILED"
        assert evidence[0]["verification_status"] == (
            "NOT_VERIFIED"
        )
        assert evidence[0]["recovery_status"] == "FAILED"

        trace = ExecutionTraceVerifier().verify(
            evidence[0]
        )

        assert trace.verified is True
        assert (
            trace.execution_id
            == result.execution_id
        )


def test_max_attempts_limits_recovery() -> None:
    with tempfile.TemporaryDirectory() as directory:
        tool = PermanentFailureTool()

        operational, recorder = build_system(
            Path(directory),
            tool,
        )

        result = operational.execute(
            "controlled failure recovery tool",
            max_attempts=2,
            value="NO SUCCESS",
        )

        assert result.success is False
        assert result.result is None
        assert result.attempts == 1
        assert tool.calls == 1

        evidence = recorder.read_recent()

        assert len(evidence) == 1
        assert evidence[0]["attempts"] == 1


def test_retryable_failure_respects_max_attempts() -> None:
    with tempfile.TemporaryDirectory() as directory:

        class AlwaysTemporaryFailure:
            def __init__(self) -> None:
                self.calls = 0

            def __call__(
                self,
                value: str = "FAIL",
            ) -> str:
                self.calls += 1

                raise TemporaryError(
                    "Injected repeated temporary failure."
                )

        tool = AlwaysTemporaryFailure()

        operational, recorder = build_system(
            Path(directory),
            tool,
        )

        result = operational.execute(
            "controlled failure recovery tool",
            max_attempts=2,
            value="NO SUCCESS",
        )

        assert result.success is False
        assert result.result is None
        assert result.attempts == 2
        assert tool.calls == 2
        assert result.recovery_status == "FAILED"
        assert result.retryable is True

        evidence = recorder.read_recent()

        assert len(evidence) == 1
        assert evidence[0]["attempts"] == 2
        assert evidence[0]["final_status"] == "FAILED"
        assert evidence[0]["verification_status"] == (
            "NOT_VERIFIED"
        )


def test_recovery_does_not_change_permission_state() -> None:
    with tempfile.TemporaryDirectory() as directory:
        tool = PermanentFailureTool()

        operational, recorder = build_system(
            Path(directory),
            tool,
        )

        result = operational.execute(
            "controlled failure recovery tool",
            max_attempts=2,
            value="NO SUCCESS",
        )

        assert result.allowed is True
        assert result.requires_confirmation is False

        evidence = recorder.read_recent()

        assert len(evidence) == 1

        assert evidence[0]["permission_allowed"] is True
        assert evidence[0]["confirmation_required"] is False
        assert evidence[0]["confirmation_provided"] is False


def test_recovery_cannot_modify_execution_id() -> None:
    with tempfile.TemporaryDirectory() as directory:
        tool = PermanentFailureTool()

        operational, recorder = build_system(
            Path(directory),
            tool,
        )

        result = operational.execute(
            "controlled failure recovery tool",
            max_attempts=3,
        )

        evidence = recorder.read_recent()

        assert len(evidence) == 1
        assert (
            evidence[0]["execution_id"]
            == result.execution_id
        )


def test_failed_recovery_trace_is_consistent() -> None:
    with tempfile.TemporaryDirectory() as directory:
        tool = PermanentFailureTool()

        operational, recorder = build_system(
            Path(directory),
            tool,
        )

        result = operational.execute(
            "controlled failure recovery tool",
            max_attempts=2,
        )

        assert result.success is False
        assert result.result is None

        evidence = recorder.read_recent()

        assert len(evidence) == 1

        trace = ExecutionTraceVerifier().verify(
            evidence[0]
        )

        assert trace.verified is True
        assert (
            trace.execution_id
            == result.execution_id
        )


def test_recovered_execution_has_verified_result() -> None:
    with tempfile.TemporaryDirectory() as directory:
        tool = ControlledFailureTool()

        operational, recorder = build_system(
            Path(directory),
            tool,
        )

        result = operational.execute(
            "controlled failure recovery tool",
            max_attempts=3,
            value="VERIFIED AFTER RETRY",
        )

        assert result.success is True
        assert result.result == (
            "VERIFIED AFTER RETRY"
        )

        evidence = recorder.read_recent()

        assert len(evidence) == 1

        record = evidence[0]

        assert record["final_status"] == "SUCCESS"
        assert record["verification_status"] == (
            "VERIFIED"
        )
        assert record["recovery_status"] == "SUCCESS"
        assert record["error"] is None

        trace = ExecutionTraceVerifier().verify(
            record
        )

        assert trace.verified is True


def test_failure_recovery_has_no_permission_authority() -> None:
    recovery = ToolFailureRecovery()

    forbidden_methods = {
        "grant_permission",
        "require_permission",
        "change_permission",
        "modify_constitution",
        "update_constitution",
        "execute",
        "invoke",
    }

    public_methods = set(dir(recovery))

    assert not (
        forbidden_methods & public_methods
    )


def run_all_tests() -> None:
    test_temporary_failure_can_recover()
    test_permanent_failure_cannot_become_success()
    test_max_attempts_limits_recovery()
    test_retryable_failure_respects_max_attempts()
    test_recovery_does_not_change_permission_state()
    test_recovery_cannot_modify_execution_id()
    test_failed_recovery_trace_is_consistent()
    test_recovered_execution_has_verified_result()
    test_failure_recovery_has_no_permission_authority()


if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-14 FAILURE INJECTION & RECOVERY INTEGRITY TEST: PASS"
    )
