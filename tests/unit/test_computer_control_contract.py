from __future__ import annotations

from tools.computer_control import (
    ComputerAction,
    ComputerControlRequest,
    ComputerControlResult,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # -------------------------------------------------
    # 1. Supported action contract
    # -------------------------------------------------

    check(
        ComputerAction.MOVE_MOUSE.value == "move_mouse",
        "MOVE_MOUSE action must exist.",
    )

    check(
        ComputerAction.CLICK.value == "click",
        "CLICK action must exist.",
    )

    check(
        ComputerAction.TYPE_TEXT.value == "type_text",
        "TYPE_TEXT action must exist.",
    )

    check(
        ComputerAction.PRESS_KEY.value == "press_key",
        "PRESS_KEY action must exist.",
    )

    check(
        ComputerAction.SCREENSHOT.value == "screenshot",
        "SCREENSHOT action must exist.",
    )

    # -------------------------------------------------
    # 2. Request contract
    # -------------------------------------------------

    request = ComputerControlRequest(
        action=ComputerAction.CLICK,
        parameters={
            "x": 100,
            "y": 200,
        },
    )

    check(
        request.action == ComputerAction.CLICK,
        "Request must preserve action.",
    )

    check(
        request.parameters["x"] == 100,
        "Request must preserve parameters.",
    )

    check(
        request.parameters["y"] == 200,
        "Request must preserve parameters.",
    )

    # -------------------------------------------------
    # 3. Result contract
    # -------------------------------------------------

    result = ComputerControlResult(
        action=ComputerAction.CLICK,
        success=True,
        result={"clicked": True},
        error=None,
    )

    check(
        result.action == ComputerAction.CLICK,
        "Result must preserve action.",
    )

    check(
        result.success is True,
        "Result must preserve success state.",
    )

    check(
        result.result == {"clicked": True},
        "Result must preserve execution data.",
    )

    check(
        result.error is None,
        "Successful result must have no error.",
    )

    # -------------------------------------------------
    # 4. Failure result
    # -------------------------------------------------

    failure = ComputerControlResult(
        action=ComputerAction.SCREENSHOT,
        success=False,
        result=None,
        error="Computer control provider unavailable.",
    )

    check(
        failure.success is False,
        "Failure must be represented.",
    )

    check(
        failure.result is None,
        "Failed operation must have no result.",
    )

    check(
        failure.error is not None,
        "Failure must preserve error.",
    )

    # -------------------------------------------------
    # 5. Invalid action rejected
    # -------------------------------------------------

    try:
        ComputerControlRequest(
            action="invalid",  # type: ignore[arg-type]
            parameters={},
        )
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError(
            "Invalid computer action must be rejected."
        )

    # -------------------------------------------------
    # 6. Immutable request
    # -------------------------------------------------

    try:
        request.action = ComputerAction.CLICK
    except Exception:
        pass
    else:
        raise AssertionError(
            "ComputerControlRequest must be immutable."
        )

    # -------------------------------------------------
    # 7. Immutable result
    # -------------------------------------------------

    try:
        result.success = False
    except Exception:
        pass
    else:
        raise AssertionError(
            "ComputerControlResult must be immutable."
        )

    print(
        "SAHIBEX 6K-7 COMPUTER CONTROL CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
