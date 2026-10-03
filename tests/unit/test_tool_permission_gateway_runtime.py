from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.policies.approval import (
    ActionType,
    PermissionEngine,
)
from tools.permission_gateway import (
    ToolPermissionGateway,
)
from tools.registry import (
    build_default_registry,
)


def check(condition: bool, message: str) -> None:
    assert condition, message
    print(f"[PASS] {message}")


def main() -> None:
    print("=" * 60)
    print("SAHIBEX 6K-2 TOOL PERMISSION GATEWAY RUNTIME TEST")
    print("=" * 60)

    engine = PermissionEngine()
    registry = build_default_registry(PROJECT_ROOT)

    gateway = ToolPermissionGateway(
        engine,
        registry,
    )

    check(
        gateway.permission_engine is engine,
        "gateway preserves PermissionEngine",
    )

    check(
        gateway.registry is registry,
        "gateway preserves ToolRegistry",
    )

    current_tools = {
        "list_directory",
        "read_file",
        "file_info",
        "search_local_files",
    }

    for tool_name in sorted(current_tools):
        check(
            registry.has(tool_name),
            f"{tool_name} is registered",
        )

        action = gateway.action_for_tool(tool_name)

        check(
            action == ActionType.READ_FILE,
            f"{tool_name} maps to READ_FILE",
        )

        decision = gateway.check(tool_name)

        check(
            decision.tool == tool_name,
            f"{tool_name} preserves tool identity",
        )

        check(
            decision.action == ActionType.READ_FILE,
            f"{tool_name} returns READ_FILE action",
        )

        check(
            decision.allowed is True,
            f"{tool_name} is allowed",
        )

        check(
            decision.requires_confirmation is False,
            f"{tool_name} does not require confirmation",
        )

        check(
            decision.risk == "low",
            f"{tool_name} is low risk",
        )

        required = gateway.require(tool_name)

        check(
            required.allowed is True,
            f"{tool_name} passes require()",
        )

    empty_name_failed = False

    try:
        gateway.action_for_tool("")
    except ValueError:
        empty_name_failed = True

    check(
        empty_name_failed,
        "empty tool name is rejected",
    )

    empty_check_failed = False

    try:
        gateway.check("")
    except ValueError:
        empty_check_failed = True

    check(
        empty_check_failed,
        "empty tool permission check is rejected",
    )

    unknown_action_failed = False

    try:
        gateway.action_for_tool("unknown_tool")
    except KeyError:
        unknown_action_failed = True

    check(
        unknown_action_failed,
        "unknown tool is rejected by action mapping",
    )

    unknown_check_failed = False

    try:
        gateway.check("unknown_tool")
    except KeyError:
        unknown_check_failed = True

    check(
        unknown_check_failed,
        "unknown tool is rejected by permission check",
    )

    unknown_require_failed = False

    try:
        gateway.require("unknown_tool")
    except KeyError:
        unknown_require_failed = True

    check(
        unknown_require_failed,
        "unknown tool is rejected by require()",
    )

    print("=" * 60)
    print(
        "SAHIBEX 6K-2 TOOL PERMISSION GATEWAY "
        "RUNTIME TEST: PASS"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
