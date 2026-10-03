from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from tools.registry import build_default_registry


def main() -> None:
    registry = build_default_registry(PROJECT_ROOT)

    expected = {
        "list_directory",
        "read_file",
        "file_info",
        "search_local_files",
    }

    actual = {
        tool.name
        for tool in registry.list_tools()
    }

    assert actual == expected, (
        f"Tool mismatch:\n"
        f"Expected: {expected}\n"
        f"Actual: {actual}"
    )

    for tool in registry.list_tools():
        assert tool.read_only is True, (
            f"{tool.name} must be read-only."
        )

        assert tool.requires_confirmation is False, (
            f"{tool.name} must not require confirmation."
        )

    tools = registry.list_tools()

    print("TOOL REGISTRY TEST: PASS")
    print(f"Registered tools: {len(tools)}")

    for tool in tools:
        print(
            f"- {tool.name}"
            f" | read_only={tool.read_only}"
            f" | confirmation={tool.requires_confirmation}"
        )


if __name__ == "__main__":
    main()
