from __future__ import annotations

import os
import subprocess
import tempfile

from tools.android_computer_control import AndroidComputerControlProvider, AndroidControlConfig
from tools.computer_control import ComputerAction, ComputerControlRequest


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    input_path = "/system/bin/input"
    screencap_path = "/system/bin/screencap"

    check(os.path.exists(input_path), "Android input binary must exist.")
    check(os.access(input_path, os.X_OK), "Android input binary must be executable.")
    check(os.path.exists(screencap_path), "Android screencap binary must exist.")
    check(os.access(screencap_path, os.X_OK), "Android screencap binary must be executable.")

    # Non-destructive runtime probe: help output only.
    probe = subprocess.run(
        [input_path, "help"],
        check=False,
        capture_output=True,
        text=True,
    )
    check(
        probe.returncode == 0 or bool(probe.stdout or probe.stderr),
        "Android input help probe returned no usable response.",
    )

    # Real screenshot capture is read-only and must not inject UI input.
    with tempfile.TemporaryDirectory(prefix="sahibex-screen-") as temp:
        screenshot = os.path.join(temp, "screen.png")
        result = AndroidComputerControlProvider(
            config=AndroidControlConfig(
                input_command=input_path,
                screencap_command=screencap_path,
                screenshot_path=screenshot,
            )
        ).execute(
            ComputerControlRequest(
                action=ComputerAction.SCREENSHOT,
                parameters={},
            ),
            authorized=True,
        )

        check(result.success, f"Real screenshot capture failed: {result.error}")
        payload = result.result or {}
        check(payload.get("bytes", 0) > 0, "Screenshot must contain bytes.")
        check(payload.get("sha256"), "Screenshot must have SHA-256 evidence.")
        check(payload.get("base64"), "Screenshot must have bounded base64 evidence.")

    print("SAHIBEX #15 ANDROID REAL SCREENSHOT PROBE: PASS")


if __name__ == "__main__":
    main()
