from __future__ import annotations

from pathlib import Path

from core.policies.approval import PermissionEngine
from tools.discovery import ToolDiscovery
from tools.executor import SafeToolExecutor
from tools.failure_recovery import ToolFailureRecovery
from tools.intelligence import ToolIntelligence
from tools.invocation import ToolInvoker
from tools.permission_gateway import ToolPermissionGateway
from tools.result_handler import ToolResultHandler
from tools.registry import ReadOnlyTools, ToolRegistry


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def build_intelligence(project_root: Path) -> ToolIntelligence:
    registry = ToolRegistry()
    read_only = ReadOnlyTools(project_root)

    registry.register(
        name="read_file",
        description="Read a local project file.",
        handler=read_only.read_file,
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

    return ToolIntelligence(
        tool_invoker=invoker,
        result_handler=result_handler,
        recovery=recovery,
    )


def main() -> None:
    project_root = Path.cwd()

    intelligence = build_intelligence(project_root)

    # ---------------------------------------------------------
    # 1. Successful read-only tool execution.
    # ---------------------------------------------------------
    result = intelligence.execute(
        "read file",
        path="tools/registry.py",
        max_bytes=5000,
    )

    check(
        result.tool == "read_file",
        "Intelligence layer must select read_file.",
    )

    check(
        result.allowed is True,
        "Read-only execution must be allowed.",
    )

    check(
        result.success is True,
        "Valid read-only execution must succeed.",
    )

    check(
        result.attempts == 1,
        "Successful execution should require only one attempt.",
    )

    check(
        result.error is None,
        "Successful execution must not contain an error.",
    )

    check(
        result.result is not None,
        "Successful execution must return a result.",
    )

    check(
        result.recovery_status == "SUCCESS",
        "Successful execution must have SUCCESS recovery status.",
    )

    # ---------------------------------------------------------
    # 2. Unknown tool query must be handled safely.
    # ---------------------------------------------------------
    unknown = intelligence.execute(
        "this tool does not exist",
    )

    check(
        unknown.success is False,
        "Unknown tool must not report success.",
    )

    check(
        unknown.allowed is False,
        "Unknown tool must not be allowed.",
    )

    check(
        unknown.attempts == 1,
        "Unknown tool must not be retried unnecessarily.",
    )

    check(
        unknown.error is not None,
        "Unknown tool must return an error.",
    )

    # ---------------------------------------------------------
    # 3. Invalid input must be rejected.
    # ---------------------------------------------------------
    try:
        intelligence.execute("")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty discovery query must raise ValueError."
        )

    # ---------------------------------------------------------
    # 4. Invalid attempt count must be rejected.
    # ---------------------------------------------------------
    try:
        intelligence.execute(
            "read file",
            max_attempts=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "max_attempts=0 must raise ValueError."
        )

    # ---------------------------------------------------------
    # 5. Intelligence layer must use existing safe layers.
    # ---------------------------------------------------------
    check(
        isinstance(
            intelligence.tool_invoker,
            ToolInvoker,
        ),
        "ToolIntelligence must use ToolInvoker.",
    )

    check(
        isinstance(
            intelligence.result_handler,
            ToolResultHandler,
        ),
        "ToolIntelligence must use ToolResultHandler.",
    )

    check(
        isinstance(
            intelligence.recovery,
            ToolFailureRecovery,
        ),
        "ToolIntelligence must use ToolFailureRecovery.",
    )

    print(
        "SAHIBEX 6K-10 TOOL INTELLIGENCE RUNTIME TEST: PASS"
    )


if __name__ == "__main__":
    main()
