from __future__ import annotations

from tools.computer_control import (
    ComputerAction,
    ComputerControlProvider,
    ComputerControlRequest,
    ComputerControlResult,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    provider = ComputerControlProvider()

    # -------------------------------------------------
    # 1. Provider exists
    # -------------------------------------------------

    check(
        provider is not None,
        "Computer control provider must exist.",
    )

    # -------------------------------------------------
    # 2. Click request
    # -------------------------------------------------

    click_request = ComputerControlRequest(
        action=ComputerAction.CLICK,
        parameters={
            "x": 100,
            "y": 200,
        },
    )

    result = provider.execute(click_request)

    check(
        isinstance(result, ComputerControlResult),
        "Provider must return ComputerControlResult.",
    )

    check(
        result.action == ComputerAction.CLICK,
        "Result must preserve requested action.",
    )

    check(
        result.success is False,
        "Unconnected provider must not report success.",
    )

    check(
        result.result is None,
        "Unconnected provider must not return execution data.",
    )

    check(
        result.error is not None,
        "Unconnected provider must return an error.",
    )

    # -------------------------------------------------
    # 3. Type text request
    # -------------------------------------------------

    type_request = ComputerControlRequest(
        action=ComputerAction.TYPE_TEXT,
        parameters={
            "text": "SAHIBEX",
        },
    )

    result = provider.execute(type_request)

    check(
        result.action == ComputerAction.TYPE_TEXT,
        "TYPE_TEXT action must be preserved.",
    )

    check(
        result.success is False,
        "TYPE_TEXT must not execute yet.",
    )

    # -------------------------------------------------
    # 4. Press key request
    # -------------------------------------------------

    key_request = ComputerControlRequest(
        action=ComputerAction.PRESS_KEY,
        parameters={
            "key": "ENTER",
        },
    )

    result = provider.execute(key_request)

    check(
        result.action == ComputerAction.PRESS_KEY,
        "PRESS_KEY action must be preserved.",
    )

    check(
        result.success is False,
        "PRESS_KEY must not execute yet.",
    )

    # -------------------------------------------------
    # 5. Screenshot request
    # -------------------------------------------------

    screenshot_request = ComputerControlRequest(
        action=ComputerAction.SCREENSHOT,
        parameters={},
    )

    result = provider.execute(screenshot_request)

    check(
        result.action == ComputerAction.SCREENSHOT,
        "SCREENSHOT action must be preserved.",
    )

    check(
        result.success is False,
        "SCREENSHOT must not execute yet.",
    )

    # -------------------------------------------------
    # 6. Invalid request type
    # -------------------------------------------------

    try:
        provider.execute(None)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Invalid request type must be rejected."
        )

    # -------------------------------------------------
    # 7. Request validation
    # -------------------------------------------------

    try:
        ComputerControlRequest(
            action="click",  # type: ignore[arg-type]
            parameters={},
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "String action must be rejected."
        )

    try:
        ComputerControlRequest(
            action=ComputerAction.CLICK,
            parameters=None,  # type: ignore[arg-type]
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Non-dictionary parameters must be rejected."
        )

    # -------------------------------------------------
    # 8. No real computer control
    # -------------------------------------------------

    result = provider.execute(
        ComputerControlRequest(
            action=ComputerAction.MOVE_MOUSE,
            parameters={
                "x": 500,
                "y": 500,
            },
        )
    )

    check(
        result.success is False,
        "MOVE_MOUSE must remain disconnected.",
    )

    check(
        result.result is None,
        "No real computer action may execute.",
    )

    print(
        "SAHIBEX 6K-7 COMPUTER CONTROL RUNTIME TEST: PASS"
    )


if __name__ == "__main__":
    main()
