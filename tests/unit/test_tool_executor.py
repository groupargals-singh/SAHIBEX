from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from tools.registry import build_default_registry
from tools.executor import SafeToolExecutor


def main() -> None:
    registry = build_default_registry(PROJECT_ROOT)
    executor = SafeToolExecutor(registry)

    print("=" * 60)
    print("SAHIBEX SAFE TOOL EXECUTOR TEST")
    print("=" * 60)

    result = executor.execute(
        "list_directory",
        path=".",
    )

    assert result.success is True
    assert result.tool == "list_directory"
    assert isinstance(result.result, dict)

    print("[PASS] list_directory executed")

    result = executor.execute(
        "read_file",
        path="app/config.py",
    )

    assert result.success is True
    assert result.tool == "read_file"
    assert "SAHIBEX" in result.result["content"]

    print("[PASS] read_file executed")

    result = executor.execute(
        "file_info",
        path="app/config.py",
    )

    assert result.success is True
    assert result.tool == "file_info"

    print("[PASS] file_info executed")

    result = executor.execute(
        "search_local_files",
        query="SAHIBEX",
        path="app",
    )

    assert result.success is True
    assert result.tool == "search_local_files"

    print("[PASS] search_local_files executed")

    result = executor.execute(
        "unknown_tool",
    )

    assert result.success is False
    assert result.error is not None

    print("[PASS] unknown tool blocked")

    print("=" * 60)
    print("SAFE TOOL EXECUTOR TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
