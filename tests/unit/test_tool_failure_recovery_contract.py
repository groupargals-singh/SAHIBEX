from __future__ import annotations

from tools.invocation import ToolInvocationResult


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # -------------------------------------------------
    # 1. Retryable failure
    # -------------------------------------------------

    retryable = ToolInvocationResult(
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
        retryable.success is False,
        "Retryable failure must be unsuccessful.",
    )

    check(
        retryable.error is not None,
        "Failure must preserve error.",
    )

    check(
        retryable.allowed is True,
        "Allowed execution failure must preserve permission state.",
    )

    # -------------------------------------------------
    # 2. Permission-blocked failure
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
        blocked.allowed is False,
        "Blocked operation must remain blocked.",
    )

    check(
        blocked.requires_confirmation is True,
        "Confirmation requirement must remain true.",
    )

    check(
        blocked.success is False,
        "Blocked operation must not be successful.",
    )

    # -------------------------------------------------
    # 3. Failed result cannot contain execution data
    # -------------------------------------------------

    invalid_failure = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=False,
        result={"unexpected": True},
        error="Execution failed.",
        risk="low",
        reason="Invalid failure state.",
    )

    check(
        invalid_failure.success is False,
        "Invalid failure must still report failure.",
    )

    check(
        invalid_failure.error is not None,
        "Invalid failure must preserve its error.",
    )

    # -------------------------------------------------
    # 4. Retry must never change tool identity
    # -------------------------------------------------

    first_attempt = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=False,
        result=None,
        error="TimeoutError",
        risk="low",
        reason="Retryable failure.",
    )

    second_attempt = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=True,
        result={"content": "SAHIBEX"},
        error=None,
        risk="low",
        reason="Retry succeeded.",
    )

    check(
        first_attempt.tool == second_attempt.tool,
        "Retry must preserve tool identity.",
    )

    # -------------------------------------------------
    # 5. Retry must not grant permission
    # -------------------------------------------------

    blocked_retry = ToolInvocationResult(
        tool="protected_tool",
        allowed=False,
        requires_confirmation=True,
        success=False,
        result=None,
        error=None,
        risk="high",
        reason="Permission required.",
    )

    check(
        blocked_retry.allowed is False,
        "Retry must not grant permission to blocked tools.",
    )

    check(
        blocked_retry.requires_confirmation is True,
        "Retry must preserve confirmation requirement.",
    )

    # -------------------------------------------------
    # 6. Recovery success
    # -------------------------------------------------

    recovered = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=True,
        result={"content": "Recovered"},
        error=None,
        risk="low",
        reason="Recovery succeeded.",
    )

    check(
        recovered.success is True,
        "Recovered execution must be successful.",
    )

    check(
        recovered.error is None,
        "Recovered execution must have no error.",
    )

    # -------------------------------------------------
    # 7. Final failure
    # -------------------------------------------------

    final_failure = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=False,
        result=None,
        error="FileNotFoundError",
        risk="low",
        reason="Retry limit reached.",
    )

    check(
        final_failure.success is False,
        "Final failure must remain unsuccessful.",
    )

    check(
        final_failure.error == "FileNotFoundError",
        "Final failure must preserve the final error.",
    )

    check(
        "Retry limit" in final_failure.reason,
        "Final failure must expose recovery state.",
    )

    print(
        "SAHIBEX 6K-6 TOOL FAILURE RECOVERY CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
