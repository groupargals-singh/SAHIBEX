from __future__ import annotations

from pathlib import Path

from core.policies.approval import (
    ActionType,
    PermissionEngine,
)
from tools.permission_gateway import ToolPermissionGateway
from tools.registry import build_default_registry


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]

    engine = PermissionEngine()
    registry = build_default_registry(project_root)

    gateway = ToolPermissionGateway(
        engine,
        registry,
    )

    # Current registered tools are autonomous read-only tools.
    for tool_name in (
        "list_directory",
        "read_file",
        "file_info",
        "search_local_files",
    ):
        without_confirmation = gateway.check(
            tool_name,
            confirmation=False,
        )

        with_confirmation = gateway.check(
            tool_name,
            confirmation=True,
        )

        check(
            without_confirmation.allowed is True,
            f"{tool_name} must remain allowed without confirmation.",
        )

        check(
            with_confirmation.allowed is True,
            f"{tool_name} must remain allowed with confirmation.",
        )

        check(
            without_confirmation.action == ActionType.READ_FILE,
            f"{tool_name} must map to READ_FILE.",
        )

        check(
            with_confirmation.action == ActionType.READ_FILE,
            f"{tool_name} confirmation must not change action class.",
        )

        check(
            without_confirmation.risk == "low",
            f"{tool_name} must remain low risk.",
        )

        check(
            with_confirmation.risk == "low",
            f"{tool_name} confirmation must not change risk.",
        )

        check(
            without_confirmation.requires_confirmation is False,
            f"{tool_name} must not require confirmation.",
        )

        check(
            with_confirmation.requires_confirmation is False,
            f"{tool_name} must not require confirmation after explicit confirmation.",
        )

    # Confirmation must not create permission for unknown tools.
    unknown_blocked = False

    try:
        gateway.check(
            "unknown_tool",
            confirmation=True,
        )
    except KeyError:
        unknown_blocked = True

    check(
        unknown_blocked,
        "Explicit confirmation must not bypass unknown-tool protection.",
    )

    print(
        "SAHIBEX 6P-8 APPROVAL PROPAGATION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
