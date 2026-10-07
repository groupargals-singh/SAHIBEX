from __future__ import annotations

from dataclasses import dataclass
import subprocess

from tools.computer_control import ComputerAction, ComputerControlRequest
from tools.android_computer_control import (
    AndroidComputerControlProvider,
    AndroidControlConfig,
)


@dataclass
class Runner:
    calls: list[list[str]]

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    runner = Runner([])
    provider = AndroidComputerControlProvider(
        config=AndroidControlConfig(
            input_command="input",
            screencap_command="screencap",
        ),
        command_runner=runner,
    )
    provider._available = lambda command: True  # type: ignore[method-assign]

    request = ComputerControlRequest(
        ComputerAction.CLICK,
        {"x": 100, "y": 200},
    )

    blocked = provider.execute(request)
    check(not blocked.success, "Unauthorized control must be blocked.")
    check("authorization" in (blocked.error or "").lower(), "Authorization error expected.")
    check(not runner.calls, "Blocked action must not reach OS runner.")

    result = provider.execute(request, authorized=True)
    check(result.success, "Authorized click should execute through runner.")
    check(runner.calls[-1] == ["input", "tap", "100", "200"], "Click command mismatch.")

    runner.calls.clear()
    result = provider.execute(
        ComputerControlRequest(
            ComputerAction.MOVE_MOUSE,
            {"x": 1, "y": 2, "end_x": 3, "end_y": 4, "duration_ms": 150},
        ),
        authorized=True,
    )
    check(result.success, "Authorized touch movement should execute.")
    check(
        runner.calls[-1] == ["input", "swipe", "1", "2", "3", "4", "150"],
        "Swipe command mismatch.",
    )

    runner.calls.clear()
    result = provider.execute(
        ComputerControlRequest(
            ComputerAction.TYPE_TEXT,
            {"text": "SAHIBEX test"},
        ),
        authorized=True,
    )
    check(result.success, "Authorized text input should execute.")
    check(
        runner.calls[-1] == ["input", "text", "SAHIBEX%stest"],
        "Text command mismatch.",
    )

    runner.calls.clear()
    result = provider.execute(
        ComputerControlRequest(
            ComputerAction.PRESS_KEY,
            {"key": "ENTER"},
        ),
        authorized=True,
    )
    check(result.success, "Authorized key input should execute.")
    check(
        runner.calls[-1] == ["input", "keyevent", "ENTER"],
        "Key command mismatch.",
    )

    print("SAHIBEX #15 ANDROID COMPUTER CONTROL ADAPTER TEST: PASS")


if __name__ == "__main__":
    main()
