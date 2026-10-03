from __future__ import annotations

from tools.invocation import ToolInvocationResult


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # -------------------------------------------------
    # 1. ToolInvocationResult contract
    # -------------------------------------------------

    result = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=True,
        result={"content": "SAHIBEX"},
        error=None,
        risk="low",
        reason="Tool execution allowed.",
    )

    check(
        result.tool == "read_file",
        "Tool name must be preserved.",
    )

    check(
        result.allowed is True,
        "Allowed state must be preserved.",
    )

    check(
        result.requires_confirmation is False,
        "Confirmation state must be preserved.",
    )

    check(
        result.success is True,
        "Success state must be preserved.",
    )

    check(
        result.result == {"content": "SAHIBEX"},
        "Tool result must be preserved.",
    )

    check(
        result.error is None,
        "Successful result should have no error.",
    )

    check(
        result.risk == "low",
        "Risk must be preserved.",
    )

    check(
        result.reason != "",
        "Reason must be preserved.",
    )

    # -------------------------------------------------
    # 2. Failure result
    # -------------------------------------------------

    failure = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=False,
        result=None,
        error="FileNotFoundError: missing.txt",
        risk="low",
        reason="FileNotFoundError: missing.txt",
    )

    check(
        failure.success is False,
        "Failure state must be represented.",
    )

    check(
        failure.result is None,
        "Failed execution should have no result.",
    )

    check(
        failure.error is not None,
        "Failure must preserve error.",
    )

    # -------------------------------------------------
    # 3. Permission-blocked result
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
        "Blocked result must preserve denied state.",
    )

    check(
        blocked.requires_confirmation is True,
        "Blocked result must preserve confirmation state.",
    )

    check(
        blocked.success is False,
        "Blocked operation must not be successful.",
    )

    check(
        blocked.result is None,
        "Blocked operation must not contain execution result.",
    )

    check(
        blocked.risk == "high",
        "Blocked operation must preserve risk.",
    )

    check(
        blocked.reason != "",
        "Blocked operation must preserve reason.",
    )

    # -------------------------------------------------
    # 4. Immutable contract
    # -------------------------------------------------

    try:
        result.tool = "changed"
    except Exception:
        pass
    else:
        raise AssertionError(
            "ToolInvocationResult must be immutable."
        )

    print(
        "SAHIBEX 6K-5 TOOL RESULT HANDLING CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
