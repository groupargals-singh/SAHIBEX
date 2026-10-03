from __future__ import annotations

from tools.invocation import ToolInvocationResult
from tools.result_handler import ToolResult, ToolResultHandler


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    handler = ToolResultHandler()

    # -------------------------------------------------
    # 1. Successful tool result
    # -------------------------------------------------

    invocation = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=True,
        result={
            "path": "app/main.py",
            "content": "SAHIBEX",
        },
        error=None,
        risk="low",
        reason="Tool execution allowed.",
    )

    result = handler.handle(invocation)

    check(
        isinstance(result, ToolResult),
        "Handler must return ToolResult.",
    )

    check(
        result.tool == "read_file",
        "Tool identity must be preserved.",
    )

    check(
        result.allowed is True,
        "Allowed state must be preserved.",
    )

    check(
        result.success is True,
        "Success state must be preserved.",
    )

    check(
        result.requires_confirmation is False,
        "Confirmation state must be preserved.",
    )

    check(
        result.result["content"] == "SAHIBEX",
        "Actual tool result must be preserved.",
    )

    check(
        result.error is None,
        "Successful result must have no error.",
    )

    check(
        result.risk == "low",
        "Risk must be preserved.",
    )

    check(
        result.reason == "Tool execution allowed.",
        "Reason must be preserved.",
    )

    # -------------------------------------------------
    # 2. Failed tool result
    # -------------------------------------------------

    invocation = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=False,
        result=None,
        error="FileNotFoundError: missing.txt",
        risk="low",
        reason="FileNotFoundError: missing.txt",
    )

    result = handler.handle(invocation)

    check(
        result.success is False,
        "Failure state must be preserved.",
    )

    check(
        result.result is None,
        "Failed result must contain no execution result.",
    )

    check(
        result.error == "FileNotFoundError: missing.txt",
        "Failure error must be preserved.",
    )

    # -------------------------------------------------
    # 3. Permission-blocked result
    # -------------------------------------------------

    invocation = ToolInvocationResult(
        tool="protected_tool",
        allowed=False,
        requires_confirmation=True,
        success=False,
        result=None,
        error=None,
        risk="high",
        reason="User confirmation required.",
    )

    result = handler.handle(invocation)

    check(
        result.allowed is False,
        "Blocked state must be preserved.",
    )

    check(
        result.success is False,
        "Blocked tool must not become successful.",
    )

    check(
        result.requires_confirmation is True,
        "Confirmation requirement must be preserved.",
    )

    check(
        result.risk == "high",
        "Risk must be preserved.",
    )

    # -------------------------------------------------
    # 4. Invalid input
    # -------------------------------------------------

    try:
        handler.handle(None)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Invalid invocation type must be rejected."
        )

    # -------------------------------------------------
    # 5. Empty tool name
    # -------------------------------------------------

    invocation = ToolInvocationResult(
        tool="",
        allowed=True,
        requires_confirmation=False,
        success=True,
        result={"value": 1},
        error=None,
        risk="low",
        reason="Valid.",
    )

    try:
        handler.handle(invocation)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty tool name must be rejected."
        )

    # -------------------------------------------------
    # 6. Success + error inconsistency
    # -------------------------------------------------

    invocation = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=True,
        result={"content": "SAHIBEX"},
        error="Unexpected error",
        risk="low",
        reason="Invalid state.",
    )

    try:
        handler.handle(invocation)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Successful result with error must be rejected."
        )

    # -------------------------------------------------
    # 7. Failure + result inconsistency
    # -------------------------------------------------

    invocation = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=False,
        result={"content": "unexpected"},
        error="Execution failed.",
        risk="low",
        reason="Invalid state.",
    )

    try:
        handler.handle(invocation)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Failed result containing execution data must be rejected."
        )

    # -------------------------------------------------
    # 8. Blocked + success inconsistency
    # -------------------------------------------------

    invocation = ToolInvocationResult(
        tool="protected_tool",
        allowed=False,
        requires_confirmation=True,
        success=True,
        result={"executed": True},
        error=None,
        risk="high",
        reason="Invalid state.",
    )

    try:
        handler.handle(invocation)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Blocked successful invocation must be rejected."
        )

    # -------------------------------------------------
    # 9. Original invocation remains unchanged
    # -------------------------------------------------

    invocation = ToolInvocationResult(
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        success=True,
        result={"content": "SAHIBEX"},
        error=None,
        risk="low",
        reason="Tool execution allowed.",
    )

    result = handler.handle(invocation)

    check(
        invocation.result == {"content": "SAHIBEX"},
        "Original invocation result must remain unchanged.",
    )

    check(
        result.result == invocation.result,
        "Normalized result must preserve original data.",
    )

    print(
        "SAHIBEX 6K-5 TOOL RESULT HANDLING RUNTIME TEST: PASS"
    )


if __name__ == "__main__":
    main()
