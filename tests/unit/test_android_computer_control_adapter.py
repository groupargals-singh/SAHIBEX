from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from tools.computer_control import ComputerAction, ComputerControlRequest
from tools.android_computer_control import AndroidComputerControlProvider, AndroidControlConfig

@dataclass
class FakeBridgeClient:
    calls: list[tuple[str, dict]]
    def call(self, action: str, payload: dict):
        self.calls.append((action, payload))
        result = {"completed": True}
        if action == "ui_tree": result["tree"] = []
        return SimpleNamespace(success=True, result=result, error=None)

def check(condition: bool, message: str) -> None:
    if not condition: raise AssertionError(message)

def main() -> None:
    token = Path("data/test_android_control_token.tmp")
    token.parent.mkdir(parents=True, exist_ok=True)
    token.write_text("private-test-token", encoding="utf-8")
    token.chmod(0o600)
    client = FakeBridgeClient([])
    provider = AndroidComputerControlProvider(
        config=AndroidControlConfig(token_path=str(token)),
        client_factory=lambda session: client,
    )
    try:
        request = ComputerControlRequest(ComputerAction.CLICK, {"x": 100, "y": 200})
        blocked = provider.execute(request)
        check(not blocked.success, "Unauthorized control must be blocked.")
        check("authorization" in (blocked.error or "").lower(), "Authorization error expected.")
        check(not client.calls, "Blocked action must not reach bridge client.")

        result = provider.execute(request, authorized=True)
        check(result.success, "Authorized click should execute through bridge.")
        check(client.calls[-1] == ("tap", {"x": 100, "y": 200}), "Click payload mismatch.")

        result = provider.execute(ComputerControlRequest(ComputerAction.MOVE_MOUSE,
            {"x": 1, "y": 2, "end_x": 3, "end_y": 4, "duration_ms": 150}), authorized=True)
        check(result.success, "Authorized swipe should execute.")
        check(client.calls[-1] == ("swipe", {"x": 1, "y": 2, "end_x": 3, "end_y": 4, "duration_ms": 150}), "Swipe payload mismatch.")

        result = provider.execute(ComputerControlRequest(ComputerAction.TYPE_TEXT, {"text": "SAHIBEX test"}), authorized=True)
        check(result.success, "Authorized text input should execute.")
        check(client.calls[-1] == ("type_text", {"text": "SAHIBEX test"}), "Text payload mismatch.")

        result = provider.execute(ComputerControlRequest(ComputerAction.PRESS_KEY, {"key": "BACK"}), authorized=True)
        check(result.success, "Supported BACK key should execute.")
        check(client.calls[-1] == ("keyevent", {"keycode": 4}), "Key payload mismatch.")

        unsupported = provider.execute(ComputerControlRequest(ComputerAction.PRESS_KEY, {"key": "ENTER"}), authorized=True)
        check(not unsupported.success, "Unsupported global key must be rejected.")
    finally:
        token.unlink(missing_ok=True)
    print("SAHIBEX #15 ANDROID COMPUTER CONTROL ADAPTER TEST: PASS")

if __name__ == "__main__": main()
