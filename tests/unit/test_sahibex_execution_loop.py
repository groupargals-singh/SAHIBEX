from pathlib import Path

from core.brain.master_brain import MasterBrain
from core.brain.sahibex_execution_loop import SahibexExecutionLoop


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_main_execution_loop_read_only_tool() -> None:
    loop = SahibexExecutionLoop(
        brain=MasterBrain(),
        project_root=PROJECT_ROOT,
    )

    result = loop.process(
        "Read file core/brain/master_brain.py"
    )

    assert result.success is True
    assert result.status == "COMPLETED"
    assert result.brain.plan_created is True
    assert result.brain.goal_id
    assert result.tool is not None
    assert result.tool.success is True
    assert result.tool.allowed is True
    assert result.tool.tool == "read_file"
    assert result.metadata["verified"] is True
    assert result.observation_count == 1
    assert "master_brain.py" in result.response
    assert loop.recovery.state.value == "ready"


def test_main_execution_loop_protected_request_stops_before_execution() -> None:
    loop = SahibexExecutionLoop(
        brain=MasterBrain(),
        project_root=PROJECT_ROOT,
    )

    result = loop.process(
        "Delete the project files."
    )

    assert result.success is False
    assert result.status == "WAITING_APPROVAL"
    assert result.tool is None
    assert result.brain.confirmation_required is True
    assert result.metadata["execution_skipped"] is True


def test_main_execution_loop_cognitive_request() -> None:
    loop = SahibexExecutionLoop(
        brain=MasterBrain(),
        project_root=PROJECT_ROOT,
    )

    result = loop.process(
        "Explain how SAHIBEX works."
    )

    assert result.success is True
    assert result.status == "COMPLETED"
    assert result.tool is None
    assert result.brain.plan_created is True
    assert result.observation_count == 1
    assert result.response


def test_main_execution_loop_never_grants_authority() -> None:
    loop = SahibexExecutionLoop(
        brain=MasterBrain(),
        project_root=PROJECT_ROOT,
    )

    assert loop.recovery.grants_permission() is False
    assert loop.recovery.executes_actions() is False
    assert loop.recovery.overrides_human_authority() is False
    assert loop.observability.grants_permission is False
    assert loop.observability.is_authority is False
