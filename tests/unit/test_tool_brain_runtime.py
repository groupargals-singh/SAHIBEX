from __future__ import annotations

from pathlib import Path

from core.brain.master_brain import MasterBrain
from core.brain.tool_brain import ToolBrain
from core.policies.approval import PermissionEngine


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_tool_brain_capability_and_security_contract() -> None:
    brain = ToolBrain(
        permission_engine=PermissionEngine(),
        project_root=PROJECT_ROOT,
    )

    capabilities = brain.capability_contract()

    assert capabilities["tool_discovery"] is True
    assert capabilities["tool_selection"] is True
    assert capabilities["permission_check"] is True
    assert capabilities["safe_execution"] is True
    assert capabilities["result_verification"] is True
    assert capabilities["failure_recovery"] is True
    assert capabilities["protected_action_support"] is True
    assert capabilities["permission_authority"] is False
    assert capabilities["constitution_mutation"] is False
    assert capabilities["human_authority_override"] is False


def test_tool_brain_discovers_and_executes_read_only_tool() -> None:
    brain = ToolBrain(
        permission_engine=PermissionEngine(),
        project_root=PROJECT_ROOT,
    )

    candidates = brain.discover("read file")

    assert candidates
    assert candidates[0].name == "read_file"

    result = brain.execute(
        "read file",
        path="tools/registry.py",
        max_bytes=2000,
    )

    assert result.success is True
    assert result.allowed is True
    assert result.tool == "read_file"
    assert result.recovery_status == "SUCCESS"
    assert result.attempts == 1
    assert result.error is None
    assert result.result is not None


def test_tool_brain_protected_tool_stops_before_execution_without_confirmation() -> None:
    brain = ToolBrain(
        permission_engine=PermissionEngine(),
        project_root=PROJECT_ROOT,
    )

    candidates = brain.discover("computer control")
    assert candidates
    assert candidates[0].name == "computer_control"

    result = brain.execute(
        "computer control",
        action="screenshot",
        parameters={},
        user_confirmation=False,
    )

    assert result.success is False
    assert result.allowed is False
    assert result.requires_confirmation is True
    assert result.tool == "computer_control"
    assert result.recovery_status == "BLOCKED"


def test_master_brain_owns_tool_brain() -> None:
    brain = MasterBrain()

    assert isinstance(brain.tool_brain, ToolBrain)
    assert brain.tool_brain.capability_contract()["human_authority_override"] is False
