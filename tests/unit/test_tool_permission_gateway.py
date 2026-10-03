from pathlib import Path

from core.policies.approval import (
    ActionType,
    PermissionEngine,
)
from tools.registry import build_default_registry


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print("SAHIBEX 6K-2 TOOL PERMISSION GATEWAY TEST")

    # ==================================================
    # Existing permission engine
    # ==================================================

    permission_engine = PermissionEngine()

    check(
        isinstance(permission_engine, PermissionEngine),
        "existing PermissionEngine is available",
    )

    # ==================================================
    # Existing SAHIBEX tool registry
    # ==================================================

    project_root = Path(__file__).resolve().parents[2]

    registry = build_default_registry(project_root)

    expected_tools = {
        "list_directory",
        "read_file",
        "file_info",
        "search_local_files",
    }

    actual_tools = {
        tool.name
        for tool in registry.list_tools()
    }

    check(
        actual_tools == expected_tools,
        "permission gateway sees the complete registered tool set",
    )

    # ==================================================
    # Tool -> ActionType mapping contract
    #
    # All current filesystem inspection tools are
    # read-only, therefore they map to READ_FILE.
    # ==================================================

    expected_action = ActionType.READ_FILE

    for tool_name in sorted(expected_tools):
        tool = registry.get(tool_name)

        check(
            tool.read_only is True,
            f"{tool_name} is read-only before permission check",
        )

        decision = permission_engine.check(
            expected_action,
        )

        check(
            decision.allowed is True,
            f"{tool_name} is allowed by READ_FILE permission",
        )

        check(
            decision.requires_confirmation is False,
            f"{tool_name} does not require confirmation",
        )

        check(
            decision.risk.value == "low",
            f"{tool_name} is classified as low risk",
        )

    # ==================================================
    # Protected action contract
    #
    # A future write-capable tool must NOT become
    # executable merely because it is registered.
    # ==================================================

    protected_actions = {
        "write": ActionType.WRITE_FILE,
        "delete": ActionType.DELETE_FILE,
        "execute": ActionType.RUN_COMMAND,
        "network": ActionType.NETWORK_ACCESS,
        "credential": ActionType.CREDENTIAL_USE,
        "system_change": ActionType.SYSTEM_CHANGE,
        "financial": ActionType.FINANCIAL_ACTION,
    }

    for label, action in protected_actions.items():
        decision = permission_engine.check(action)

        check(
            decision.allowed is False,
            f"{label} action is blocked without confirmation",
        )

        check(
            decision.requires_confirmation is True,
            f"{label} action requires explicit confirmation",
        )

    # ==================================================
    # Explicit confirmation contract
    # ==================================================

    confirmation_checks = {
        "write": ActionType.WRITE_FILE,
        "delete": ActionType.DELETE_FILE,
        "execute": ActionType.RUN_COMMAND,
        "network": ActionType.NETWORK_ACCESS,
        "credential": ActionType.CREDENTIAL_USE,
    }

    for label, action in confirmation_checks.items():
        decision = permission_engine.check(
            action,
            confirmation=True,
        )

        check(
            decision.allowed is True,
            f"{label} action is allowed after explicit confirmation",
        )

        check(
            decision.requires_confirmation is False,
            f"{label} confirmation requirement clears after approval",
        )

    # ==================================================
    # Tool metadata must not override permission policy
    # ==================================================

    read_tool = registry.get("read_file")

    check(
        read_tool.read_only is True,
        "tool metadata identifies read_file as read-only",
    )

    read_decision = permission_engine.check(
        ActionType.READ_FILE,
    )

    check(
        read_decision.allowed is True,
        "permission policy independently allows read_file",
    )

    check(
        read_decision.risk.value == "low",
        "permission policy independently classifies read_file as low risk",
    )

    # ==================================================
    # Permission engine remains execution-independent
    # ==================================================

    check(
        not hasattr(permission_engine, "execute"),
        "PermissionEngine does not execute tools",
    )

    check(
        not hasattr(permission_engine, "run_tool"),
        "PermissionEngine does not run tools",
    )

    # ==================================================
    # Final
    # ==================================================

    print(
        "SAHIBEX 6K-2 TOOL PERMISSION GATEWAY TEST: PASS"
    )


if __name__ == "__main__":
    main()
