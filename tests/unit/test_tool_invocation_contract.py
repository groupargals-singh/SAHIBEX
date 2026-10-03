from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from tools.discovery import ToolCandidate
from tools.executor import ToolExecutionResult
from tools.permission_gateway import ToolPermissionDecision


def check(condition: bool, message: str) -> None:
    assert condition, message
    print(f"[PASS] {message}")


def main() -> None:
    print("=" * 60)
    print("SAHIBEX 6K-4 TOOL INVOCATION CONTRACT TEST")
    print("=" * 60)

    candidate = ToolCandidate(
        name="read_file",
        description="Read a text file.",
        score=100,
        read_only=True,
        requires_confirmation=False,
    )

    check(
        candidate.name == "read_file",
        "tool candidate preserves selected tool",
    )

    check(
        candidate.read_only is True,
        "tool candidate preserves read-only state",
    )

    permission = ToolPermissionDecision(
        tool="read_file",
        action=__import__(
            "core.policies.approval",
            fromlist=["ActionType"],
        ).ActionType.READ_FILE,
        allowed=True,
        requires_confirmation=False,
        risk="low",
        reason="Low-risk action is allowed.",
    )

    check(
        permission.tool == "read_file",
        "permission decision preserves tool identity",
    )

    check(
        permission.allowed is True,
        "permission decision records allowed state",
    )

    check(
        permission.requires_confirmation is False,
        "permission decision records confirmation state",
    )

    result = ToolExecutionResult(
        success=True,
        tool="read_file",
        result={
            "path": "example.txt",
            "content": "SAHIBEX",
        },
        error=None,
    )

    check(
        result.success is True,
        "execution result records success",
    )

    check(
        result.tool == "read_file",
        "execution result preserves tool identity",
    )

    check(
        isinstance(result.result, dict),
        "execution result preserves tool output",
    )

    check(
        result.error is None,
        "successful execution has no error",
    )

    failed_result = ToolExecutionResult(
        success=False,
        tool="read_file",
        result=None,
        error="FileNotFoundError: missing.txt",
    )

    check(
        failed_result.success is False,
        "failed execution records failure",
    )

    check(
        failed_result.error is not None,
        "failed execution preserves error",
    )

    check(
        failed_result.result is None,
        "failed execution has no result",
    )

    print("=" * 60)
    print(
        "SAHIBEX 6K-4 TOOL INVOCATION "
        "CONTRACT TEST: PASS"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
