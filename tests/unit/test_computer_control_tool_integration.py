from __future__ import annotations

from pathlib import Path
import tempfile

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


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    calls: list[list[str]] = []

    def runner(command: list[str]):
        import subprocess
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    provider = AndroidComputerControlProvider(
        config=AndroidControlConfig(input_command="input"),
        command_runner=runner,
    )
    provider._available = lambda command: True  # type: ignore[method-assign]

    audit_tmp = tempfile.TemporaryDirectory(prefix="sahibex-computer-audit-")
    recorder = ExecutionEvidenceRecorder(Path(audit_tmp.name))
    registry = ToolRegistry()
    tool = ComputerControlTool(
        provider=provider,
        evidence_recorder=recorder,
    )
    registry.register(
        name="computer_control",
        description="Control Android computer UI: click, type, press keys, swipe, screenshot.",
        handler=tool.execute,
        read_only=False,
        requires_confirmation=True,
        protected_action=ActionType.RUN_COMMAND,
    )

    # Protected tool must be discovered.
    candidate = ToolDiscovery(registry).select("computer control click")
    check(candidate is not None, "Computer-control tool must be discoverable.")
    check(candidate.name == "computer_control", "Wrong tool discovered.")

    gateway = ToolPermissionGateway(PermissionEngine(), registry)

    blocked = gateway.check("computer_control", confirmation=False)
    check(not blocked.allowed, "Computer control must be blocked without confirmation.")
    check(blocked.requires_confirmation, "Computer control must require confirmation.")

    executor = SafeToolExecutor(registry)
    invoker = ToolInvoker(
        ToolDiscovery(registry),
        gateway,
        executor,
    )

    # Through the real discovery -> permission -> executor -> handler path.
    result = invoker.invoke(
        "computer control click",
        user_confirmation=True,
        action=ComputerAction.CLICK,
        parameters={"x": 10, "y": 20},
    )
    check(result.allowed, "Confirmed computer control should be allowed.")
    check(result.success, f"Confirmed computer control should execute: {result.error}")
    check(calls[-1] == ["input", "tap", "10", "20"], "Real adapter command mismatch.")
    evidence = recorder.read_recent(limit=1)
    check(evidence, "Protected computer-control execution must create audit evidence.")
    check(evidence[-1].get("tool") == "computer_control", "Audit tool identity mismatch.")
    check(evidence[-1].get("permission_allowed") is True, "Audit must record allowed permission.")
    check(evidence[-1].get("confirmation_provided") is True, "Audit must record confirmation.")
    check(evidence[-1].get("provenance"), "Audit must contain authenticated provenance.")

    # Direct handler use without the private permission marker must not execute.
    calls.clear()
    direct = tool.execute(
        action=ComputerAction.CLICK,
        parameters={"x": 30, "y": 40},
    )
    check(not direct["success"], "Direct handler call must remain unauthorized.")
    check(not calls, "Unauthorized direct handler must not reach OS runner.")

    print("SAHIBEX #15 RUNTIME INTEGRATION TEST: PASS")


if __name__ == "__main__":
    main()
