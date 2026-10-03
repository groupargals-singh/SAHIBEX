from __future__ import annotations

from core.policies.approval import PermissionEngine
from tools.discovery import ToolDiscovery
from tools.executor import SafeToolExecutor
from tools.intelligence import ToolIntelligence
from tools.permission_gateway import ToolPermissionGateway
from tools.registry import ToolDefinition, ToolRegistry
from tools.result_handler import ToolResultHandler
from tools.failure_recovery import ToolFailureRecovery

from core.brain.operational_tool_execution import (
    OperationalToolExecution,
    OperationalToolExecutionResult,
)


def build_pipeline() -> OperationalToolExecution:
    registry = ToolRegistry()

    registry.register(
    name="test_read_tool",
    description="read test information",
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

    from tools.invocation import ToolInvoker

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
    )


def test_real_read_only_tool_execution() -> None:
    operational = build_pipeline()

    result = operational.execute(
        "read test information",
        value="REAL TOOL RESULT",
    )

    assert isinstance(
        result,
        OperationalToolExecutionResult,
    )

    assert result.success is True
    assert result.allowed is True
    assert result.requires_confirmation is False
    assert result.tool == "test_read_tool"
    assert result.result == "REAL TOOL RESULT"
    assert result.error is None
    assert result.attempts == 1
    assert result.recovery_status == "SUCCESS"
    assert result.retryable is False
    assert result.risk == "low"
    assert result.execution_id


def test_unknown_tool_is_blocked() -> None:
    operational = build_pipeline()

    result = operational.execute(
        "zzzz_nonexistent_sahibex_tool_987654",
    )

    assert result.success is False
    assert result.allowed is False
    assert result.tool == ""
    assert result.result is None
    assert result.recovery_status == "BLOCKED"
    assert result.retryable is False
    assert result.error is not None


def test_empty_query_is_rejected() -> None:
    operational = build_pipeline()

    try:
        operational.execute("")
    except ValueError as exc:
        assert str(exc) == (
            "discovery_query cannot be empty."
        )
    else:
        raise AssertionError(
            "Empty discovery query must be rejected."
        )


def test_invalid_max_attempts_is_rejected() -> None:
    operational = build_pipeline()

    try:
        operational.execute(
            "read test information",
            max_attempts=0,
        )
    except ValueError as exc:
        assert str(exc) == (
            "max_attempts must be at least 1."
        )
    else:
        raise AssertionError(
            "max_attempts=0 must be rejected."
        )


def test_permission_and_executor_pipeline_remains_authoritative() -> None:
    operational = build_pipeline()

    result = operational.execute(
        "read test information",
    )

    assert result.success is True
    assert result.allowed is True
    assert result.tool == "test_read_tool"

    assert not hasattr(
        operational,
        "grant_permission",
    )

    assert not hasattr(
        operational,
        "override_constitution",
    )

    assert not hasattr(
        operational,
        "run_command",
    )

    assert not hasattr(
        operational,
        "write_file",
    )

    assert not hasattr(
        operational,
        "delete_file",
    )

    assert not hasattr(
        operational,
        "system_change",
    )

    assert not hasattr(
        operational,
        "financial_action",
    )


if __name__ == "__main__":
    test_real_read_only_tool_execution()
    test_unknown_tool_is_blocked()
    test_empty_query_is_rejected()
    test_invalid_max_attempts_is_rejected()
    test_permission_and_executor_pipeline_remains_authoritative()

    print(
        "SAHIBEX 6O-6 REAL TOOL EXECUTION PIPELINE TEST: PASS"
    )
