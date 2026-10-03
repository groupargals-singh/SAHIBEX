from __future__ import annotations

from core.brain.operational_protected_action import (
    OperationalProtectedActionGateway,
    ProtectedActionStatus,
)
from core.policies.approval import ActionType
from core.policies.constitution import ActionClass


def test_protected_action_requires_confirmation() -> None:
    gateway = OperationalProtectedActionGateway()

    result = gateway.approve(
        ActionClass.WRITE,
        user_confirmation=False,
    )

    assert result.status == ProtectedActionStatus.BLOCKED
    assert result.allowed is False
    assert result.requires_confirmation is True
    assert result.execution_allowed is False
    assert result.action_type == ActionType.WRITE_FILE
    assert result.risk == "medium"


def test_explicit_confirmation_approves_write_action() -> None:
    gateway = OperationalProtectedActionGateway()

    result = gateway.approve(
        ActionClass.WRITE,
        user_confirmation=True,
    )

    assert result.status == ProtectedActionStatus.APPROVED
    assert result.allowed is True
    assert result.requires_confirmation is False
    assert result.execution_allowed is True
    assert result.action_type == ActionType.WRITE_FILE
    assert result.risk == "medium"
    assert result.user_confirmation is True


def test_delete_requires_confirmation() -> None:
    gateway = OperationalProtectedActionGateway()

    result = gateway.approve(
        ActionClass.DELETE,
        user_confirmation=False,
    )

    assert result.status == ProtectedActionStatus.BLOCKED
    assert result.allowed is False
    assert result.requires_confirmation is True
    assert result.execution_allowed is False
    assert result.action_type == ActionType.DELETE_FILE
    assert result.risk == "high"


def test_execute_requires_confirmation() -> None:
    gateway = OperationalProtectedActionGateway()

    result = gateway.approve(
        ActionClass.EXECUTE,
        user_confirmation=False,
    )

    assert result.status == ProtectedActionStatus.BLOCKED
    assert result.allowed is False
    assert result.requires_confirmation is True
    assert result.execution_allowed is False
    assert result.action_type == ActionType.RUN_COMMAND
    assert result.risk == "high"


def test_critical_system_change_remains_blocked() -> None:
    gateway = OperationalProtectedActionGateway()

    result = gateway.approve(
        ActionClass.SYSTEM_CHANGE,
        user_confirmation=True,
    )

    assert result.status == ProtectedActionStatus.BLOCKED
    assert result.allowed is False
    assert result.requires_confirmation is True
    assert result.execution_allowed is False
    assert result.action_type == ActionType.SYSTEM_CHANGE
    assert result.risk == "critical"


def test_critical_financial_action_remains_blocked() -> None:
    gateway = OperationalProtectedActionGateway()

    result = gateway.approve(
        ActionClass.FINANCIAL,
        user_confirmation=True,
    )

    assert result.status == ProtectedActionStatus.BLOCKED
    assert result.allowed is False
    assert result.requires_confirmation is True
    assert result.execution_allowed is False
    assert result.action_type == ActionType.FINANCIAL_ACTION
    assert result.risk == "critical"


def test_self_update_is_not_executable_here() -> None:
    gateway = OperationalProtectedActionGateway()

    result = gateway.approve(
        ActionClass.SELF_UPDATE,
        user_confirmation=True,
    )

    assert result.status == ProtectedActionStatus.BLOCKED
    assert result.allowed is False
    assert result.execution_allowed is False


def test_external_control_is_not_executable_here() -> None:
    gateway = OperationalProtectedActionGateway()

    result = gateway.approve(
        ActionClass.EXTERNAL_CONTROL,
        user_confirmation=True,
    )

    assert result.status == ProtectedActionStatus.BLOCKED
    assert result.allowed is False
    assert result.execution_allowed is False


def test_gateway_cannot_override_constitution() -> None:
    gateway = OperationalProtectedActionGateway()

    assert not hasattr(
        gateway,
        "override_constitution",
    )

    assert not hasattr(
        gateway,
        "modify_constitution",
    )

    assert not hasattr(
        gateway,
        "grant_permission",
    )

    assert not hasattr(
        gateway,
        "execute",
    )

    assert not hasattr(
        gateway,
        "run_command",
    )

    assert not hasattr(
        gateway,
        "write_file",
    )

    assert not hasattr(
        gateway,
        "delete_file",
    )


if __name__ == "__main__":
    test_protected_action_requires_confirmation()
    test_explicit_confirmation_approves_write_action()
    test_delete_requires_confirmation()
    test_execute_requires_confirmation()
    test_critical_system_change_remains_blocked()
    test_critical_financial_action_remains_blocked()
    test_self_update_is_not_executable_here()
    test_external_control_is_not_executable_here()
    test_gateway_cannot_override_constitution()

    print(
        "SAHIBEX 6O-7 APPROVAL-GATED PROTECTED ACTION TEST: PASS"
    )
