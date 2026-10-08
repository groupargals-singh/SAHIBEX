from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.emergency_stop import EmergencyStop
from core.brain.tool_brain import ToolBrain
from core.policies.approval import PermissionEngine
from tools.android_ui_understanding import find_elements
from tools.computer_control import ComputerAction, ComputerControlRequest
from tools.computer_control_tool import ComputerControlTool


def main() -> None:
    tree = [{"class": "Button", "text": "Open", "contentDescription": "open", "clickable": True, "enabled": True, "bounds": [1, 2, 30, 40], "children": []}, {"class": "EditText", "text": "", "contentDescription": "name", "editable": True, "enabled": True, "bounds": [2, 3, 40, 50], "children": []}]
    assert len(find_elements(tree, clickable=True)) == 1
    assert len(find_elements(tree, editable=True)) == 1
    assert find_elements(tree, text="open")[0].bounds == (1, 2, 30, 40)

    with TemporaryDirectory() as temp:
        root = Path(temp)
        stop = EmergencyStop()
        brain = ToolBrain(PermissionEngine(), project_root=root, emergency_stop=stop)
        stop.engage("test stop")
        blocked = brain.execute("computer control", user_confirmation=True, action="screenshot", parameters={})
        assert blocked.success is False
        assert blocked.recovery_status == "BLOCKED"
        assert blocked.allowed is False

        recorder_tool = ComputerControlTool(evidence_recorder=brain.evidence_recorder)
        denied = recorder_tool.execute(action=ComputerAction.CLICK, parameters={"x": 1, "y": 2})
        assert denied["success"] is False
        assert denied["final_status"] == "FAILED"
        records = brain.evidence_recorder.read_recent(1)
        assert records and records[-1]["tool"] == "computer_control"
        assert records[-1].get("provenance")

    print("PHASE 8 DEVICE CONTROL INTEGRATION: PASS")


if __name__ == "__main__":
    main()
