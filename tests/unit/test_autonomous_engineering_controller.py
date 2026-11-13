from pathlib import Path

import pytest

from core.agent.engineering_controller import (
    AutonomousEngineeringController,
    EngineeringAction,
    EngineeringPolicyError,
)


@pytest.fixture
def controller() -> AutonomousEngineeringController:
    root = Path(__file__).resolve().parents[2]
    return AutonomousEngineeringController(root, timeout_seconds=30)


def test_repository_status_is_available_and_read_only(controller):
    result = controller.run(EngineeringAction.REPOSITORY_STATUS)
    assert result.success is True
    assert result.return_code == 0
    assert "## " in result.output
    assert controller.protected_capabilities()["file_write_or_delete"] is False


def test_diff_check_passes(controller):
    result = controller.run(EngineeringAction.DIFF_CHECK)
    assert result.success is True
    assert result.return_code == 0


def test_compile_check_uses_fixed_command(controller):
    result = controller.run(EngineeringAction.COMPILE_CHECK)
    assert result.success is True
    assert result.command[1:3] == ("-m", "compileall")


def test_test_runner_accepts_only_files_inside_tests(controller):
    with pytest.raises(EngineeringPolicyError):
        controller.run(EngineeringAction.TEST_FILE, test_file="../app/main.py")
    with pytest.raises(EngineeringPolicyError):
        controller.run(EngineeringAction.TEST_FILE, test_file="tests/missing_test.py")


def test_unknown_action_is_rejected(controller):
    with pytest.raises(EngineeringPolicyError):
        controller.run("shell:rm -rf .")


def test_protected_actions_are_not_granted():
    capabilities = AutonomousEngineeringController.protected_capabilities()
    assert all(value is False for value in capabilities.values())
    assert capabilities["github_commit_or_push"] is False
    assert capabilities["cloud_deploy"] is False
    assert capabilities["android_ui_control"] is False


def test_output_redaction_masks_common_secrets():
    cleaned = AutonomousEngineeringController._redact(
        "token=abc123 Authorization: Bearer xyz987"
    )
    assert "abc123" not in cleaned
    assert "xyz987" not in cleaned
    assert cleaned.count("[REDACTED]") == 2
