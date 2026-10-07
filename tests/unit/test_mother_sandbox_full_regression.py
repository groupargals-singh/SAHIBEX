from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.brain.mother_sandbox_runtime import (
    MotherSandboxDecision,
    MotherSandboxRequest,
    MotherSandboxRuntime,
)
from tools.executor import SafeToolExecutor
from tools.registry import build_default_registry


class TrackingSandbox(MotherSandboxRuntime):
    def __init__(self) -> None:
        self.handler_called = False

    def validate(self, request):
        self.handler_called = False
        return super().validate(request)


class BlockingSandbox(MotherSandboxRuntime):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        self.handler_called = False

    def validate(self, request):
        self.handler_called = False
        return self._blocked(self.reason)


def check(condition: bool, message: str) -> None:
    assert condition, message
    print(f"[PASS] {message}")


def main() -> None:
    print("=" * 60)
    print("SAHIBEX 6S-3 FULL SANDBOX SECURITY REGRESSION")
    print("=" * 60)

    sandbox = MotherSandboxRuntime()

    # 1. Fully isolated sandbox
    result = sandbox.validate(
        MotherSandboxRequest(
            request_id="6s3-001",
            action="protected_execution",
            isolated_filesystem=True,
            isolated_memory=True,
            isolated_credentials=True,
            isolated_network=True,
            isolated_runtime=True,
        )
    )

    check(
        result.decision == MotherSandboxDecision.ALLOW,
        "fully isolated sandbox is allowed",
    )

    check(
        result.allowed is True,
        "fully isolated sandbox reports allowed",
    )

    # 2. Filesystem isolation
    result = sandbox.validate(
        MotherSandboxRequest(
            request_id="6s3-002",
            action="protected_execution",
            isolated_filesystem=False,
            isolated_memory=True,
            isolated_credentials=True,
            isolated_network=True,
            isolated_runtime=True,
        )
    )

    check(
        result.decision == MotherSandboxDecision.BLOCK,
        "missing filesystem isolation is blocked",
    )

    # 3. Credential isolation
    result = sandbox.validate(
        MotherSandboxRequest(
            request_id="6s3-003",
            action="protected_execution",
            isolated_filesystem=True,
            isolated_memory=True,
            isolated_credentials=False,
            isolated_network=True,
            isolated_runtime=True,
        )
    )

    check(
        result.decision == MotherSandboxDecision.BLOCK,
        "missing credential isolation is blocked",
    )

    # 4. Network isolation
    result = sandbox.validate(
        MotherSandboxRequest(
            request_id="6s3-004",
            action="protected_execution",
            isolated_filesystem=True,
            isolated_memory=True,
            isolated_credentials=True,
            isolated_network=False,
            isolated_runtime=True,
        )
    )

    check(
        result.decision == MotherSandboxDecision.BLOCK,
        "missing network isolation is blocked",
    )

    # 5. Runtime isolation
    result = sandbox.validate(
        MotherSandboxRequest(
            request_id="6s3-005",
            action="protected_execution",
            isolated_filesystem=True,
            isolated_memory=True,
            isolated_credentials=True,
            isolated_network=True,
            isolated_runtime=False,
        )
    )

    check(
        result.decision == MotherSandboxDecision.BLOCK,
        "missing runtime isolation is blocked",
    )

    # 6. Executor happy path
    registry = build_default_registry(PROJECT_ROOT)
    executor = SafeToolExecutor(
        registry,
        sandbox=MotherSandboxRuntime(),
    )

    result = executor.execute(
        "list_directory",
        path=".",
    )

    check(
        result.success is True,
        "valid sandbox allows read-only tool execution",
    )

    # 7. Executor sandbox block
    blocking_sandbox = BlockingSandbox(
        "regression sandbox failure"
    )

    executor = SafeToolExecutor(
        registry,
        sandbox=blocking_sandbox,
    )

    result = executor.execute(
        "list_directory",
        path=".",
    )

    check(
        result.success is False,
        "sandbox failure blocks executor",
    )

    check(
        result.result is None,
        "blocked executor returns no result",
    )

    check(
        result.error is not None
        and "Mother Sandbox" in result.error,
        "sandbox block is reported by executor",
    )

    # 8. Unknown tool remains blocked
    executor = SafeToolExecutor(
        registry,
        sandbox=MotherSandboxRuntime(),
    )

    result = executor.execute(
        "unknown_tool",
    )

    check(
        result.success is False,
        "unknown tool remains blocked",
    )

    check(
        result.error is not None
        and "Unknown tool" in result.error,
        "unknown tool error remains preserved",
    )

    print("=" * 60)
    print("SAHIBEX 6S-3 FULL SANDBOX SECURITY REGRESSION: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
