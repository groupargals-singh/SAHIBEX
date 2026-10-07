from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.brain.mother_sandbox_runtime import (
    MotherSandboxRuntime,
)
from tools.executor import SafeToolExecutor
from tools.registry import build_default_registry


class BlockingSandbox(MotherSandboxRuntime):
    def validate(self, request):
        return self._blocked(
            "test sandbox isolation failure"
        )


def main() -> None:
    print("=" * 60)
    print("SAHIBEX 6S-2 SANDBOX EXECUTOR BOUNDARY TEST")
    print("=" * 60)

    registry = build_default_registry(PROJECT_ROOT)

    sandbox = BlockingSandbox()

    executor = SafeToolExecutor(
        registry,
        sandbox=sandbox,
    )

    result = executor.execute(
        "list_directory",
        path=".",
    )

    assert result.success is False
    assert result.tool == "list_directory"
    assert result.result is None
    assert result.error is not None
    assert "Mother Sandbox" in result.error

    print("[PASS] sandbox failure blocks tool execution")
    print("[PASS] blocked execution returns no result")
    print("[PASS] sandbox boundary is reached before handler")

    print("=" * 60)
    print("SAHIBEX 6S-2 SANDBOX EXECUTOR BOUNDARY TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
