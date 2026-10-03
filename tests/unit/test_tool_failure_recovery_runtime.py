from __future__ import annotations

from tools.failure_recovery import (
    RecoveryResult,
    RetryPolicy,
    ToolFailureRecovery,
)
from tools.invocation import ToolInvocationResult


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    recovery = ToolFailureRecovery(
        RetryPolicy(max_retries=2)
    )

    # -------------------------------------------------
    # 1. Successful invocation
    # -------------------------------------------------

    success = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=True,
        result={"content": "SAHIBEX"},
        error=None,
        risk="low",
        reason="Execution succeeded.",
    )

    result = recovery.recover(
        success,
        attempts=1,
    )

    check(
        isinstance(result, RecoveryResult),
        "Recovery must return RecoveryResult.",
    )

    check(
        result.status == "SUCCESS",
        "Successful invocation must have SUCCESS status.",
    )

    check(
        result.success is True,
        "Successful invocation must remain successful.",
    )

    check(
        result.result == {"content": "SAHIBEX"},
        "Successful result must be preserved.",
    )

    check(
        result.retryable is False,
        "Successful invocation must not be retryable.",
    )

    # -------------------------------------------------
    # 2. Retryable timeout
    # -------------------------------------------------

    timeout = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=False,
        result=None,
        error="TimeoutError: operation timed out.",
        risk="low",
        reason="Tool execution failed.",
    )

    check(
        recovery.is_retryable(timeout) is True,
        "Timeout must be retryable.",
    )

    result = recovery.recover(
        timeout,
        attempts=1,
    )

    check(
        result.status == "RETRY",
        "First retryable failure must request RETRY.",
    )

    check(
        result.retryable is True,
        "Retryable failure must remain retryable.",
    )

    check(
        result.attempts == 1,
        "Attempt count must be preserved.",
    )

    # -------------------------------------------------
    # 3. Retry limit
    # -------------------------------------------------

    result = recovery.recover(
        timeout,
        attempts=3,
    )

    check(
        result.status == "FAILED",
        "Retry limit must produce FAILED status.",
    )

    check(
        result.retryable is False,
        "Retry limit must stop further retries.",
    )

    check(
        result.attempts == 3,
        "Final attempt count must be preserved.",
    )

    check(
        result.error == timeout.error,
        "Final error must be preserved.",
    )

    # -------------------------------------------------
    # 4. Non-retryable failure
    # -------------------------------------------------

    missing_file = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=False,
        result=None,
        error="FileNotFoundError: missing.txt",
        risk="low",
        reason="File does not exist.",
    )

    check(
        recovery.is_retryable(missing_file) is False,
        "FileNotFoundError must not be retryable.",
    )

    result = recovery.recover(
        missing_file,
        attempts=1,
    )

    check(
        result.status == "FAILED",
        "Non-retryable failure must be FAILED.",
    )

    check(
        result.retryable is False,
        "Non-retryable failure must not request retry.",
    )

    # -------------------------------------------------
    # 5. Permission blocked
    # -------------------------------------------------

    blocked = ToolInvocationResult(
        tool="protected_tool",
        allowed=False,
        requires_confirmation=True,
        success=False,
        result=None,
        error=None,
        risk="high",
        reason="User confirmation required.",
    )

    check(
        recovery.is_retryable(blocked) is False,
        "Blocked tool must never be retryable.",
    )

    result = recovery.recover(
        blocked,
        attempts=1,
    )

    check(
        result.status == "BLOCKED",
        "Blocked tool must have BLOCKED status.",
    )

    check(
        result.success is False,
        "Blocked tool must not succeed.",
    )

    check(
        result.retryable is False,
        "Blocked tool must not be retryable.",
    )

    # -------------------------------------------------
    # 6. Permission cannot be granted by recovery
    # -------------------------------------------------

    check(
        blocked.allowed is False,
        "Recovery must not change permission state.",
    )

    # -------------------------------------------------
    # 7. Invalid attempt count
    # -------------------------------------------------

    try:
        recovery.recover(
            timeout,
            attempts=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Zero attempts must be rejected."
        )

    # -------------------------------------------------
    # 8. Invalid invocation type
    # -------------------------------------------------

    try:
        recovery.recover(None)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Invalid invocation type must be rejected."
        )

    try:
        recovery.is_retryable(None)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Invalid invocation type must be rejected."
        )

    # -------------------------------------------------
    # 9. Retry policy validation
    # -------------------------------------------------

    try:
        RetryPolicy(max_retries=-1)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Negative retry limit must be rejected."
        )

    print(
        "SAHIBEX 6K-6 TOOL FAILURE RECOVERY RUNTIME TEST: PASS"
    )


if __name__ == "__main__":
    main()
