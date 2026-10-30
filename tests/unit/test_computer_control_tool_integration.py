from __future__ import annotations
from pathlib import Path
import tempfile
from types import SimpleNamespace

from core.policies.approval import ActionType, PermissionEngine
from security.audit.execution_evidence import ExecutionEvidenceRecorder
from tools.android_computer_control import AndroidComputerControlProvider, AndroidControlConfig
from tools.computer_control import ComputerAction
from tools.computer_control_tool import ComputerControlTool
from tools.discovery import ToolDiscovery
from tools.executor import SafeToolExecutor
from tools.invocation import ToolInvoker
from tools.permission_gateway import ToolPermissionGateway
from tools.registry import ToolRegistry

class FakeBridgeClient:
    def __init__(self): self.calls = []
    def call(self, action, payload):
        self.calls.append((action, payload))
        return SimpleNamespace(success=True, result={"completed": True}, error=None)

def check(condition: bool, message: str) -> None:
    if not condition: raise AssertionError(message)

def main() -> None:
    calls = []
    with tempfile.TemporaryDirectory(prefix="sahibex-computer-audit-") as temp:
        token_path = Path(temp) / "control-token"
        token_path.write_text("private-test-token", encoding="utf-8")
        token_path.chmod(0o600)
        client = FakeBridgeClient()
        provider = AndroidComputerControlProvider(config=AndroidControlConfig(token_path=str(token_path)),
            client_factory=lambda session: client)
        recorder = ExecutionEvidenceRecorder(Path(temp) / "audit")
        registry = ToolRegistry()
        tool = ComputerControlTool(provider=provider, evidence_recorder=recorder)
        registry.register(name="computer_control",
            description="Control Android computer UI: click, type, press keys, swipe, screenshot.",
            handler=tool.execute, read_only=False, requires_confirmation=True,
            protected_action=ActionType.RUN_COMMAND)
        candidate = ToolDiscovery(registry).select("computer control click")
        check(candidate is not None, "Computer-control tool must be discoverable.")
        check(candidate.name == "computer_control", "Wrong tool discovered.")
        gateway = ToolPermissionGateway(PermissionEngine(), registry)
        blocked = gateway.check("computer_control", confirmation=False)
        check(not blocked.allowed, "Computer control must be blocked without confirmation.")
        check(blocked.requires_confirmation, "Computer control must require confirmation.")
        invoker = ToolInvoker(ToolDiscovery(registry), gateway, SafeToolExecutor(registry))
        result = invoker.invoke("computer control click", user_confirmation=True,
            action=ComputerAction.CLICK, parameters={"x": 10, "y": 20})
        check(result.allowed, "Confirmed computer control should be allowed.")
        check(result.success, f"Confirmed computer control should execute: {result.error}")
        check(client.calls[-1] == ("tap", {"x": 10, "y": 20}), "Bridge adapter payload mismatch.")
        evidence = recorder.read_recent(limit=1)
        check(evidence, "Protected computer-control execution must create audit evidence.")
        check(evidence[-1].get("tool") == "computer_control", "Audit tool identity mismatch.")
        check(evidence[-1].get("permission_allowed") is True, "Audit must record allowed permission.")
        check(evidence[-1].get("confirmation_provided") is True, "Audit must record confirmation.")
        check(evidence[-1].get("provenance"), "Audit must contain authenticated provenance.")
        client.calls.clear()
        direct = tool.execute(action=ComputerAction.CLICK, parameters={"x": 30, "y": 40})
        check(not direct["success"], "Direct handler call must remain unauthorized.")
        check(not client.calls, "Unauthorized direct handler must not reach bridge client.")
    print("SAHIBEX #15 RUNTIME INTEGRATION TEST: PASS")

if __name__ == "__main__": main()
