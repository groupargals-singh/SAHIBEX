from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from tools.discovery import ToolCandidate, ToolDiscovery
from tools.registry import build_default_registry


def check(condition: bool, message: str) -> None:
    assert condition, message
    print(f"[PASS] {message}")


def main() -> None:
    print("=" * 60)
    print("SAHIBEX 6K-3 TOOL DISCOVERY RUNTIME TEST")
    print("=" * 60)

    registry = build_default_registry(PROJECT_ROOT)
    discovery = ToolDiscovery(registry)

    check(
        discovery.registry is registry,
        "discovery preserves ToolRegistry",
    )

    candidates = discovery.discover("read file")

    check(
        len(candidates) > 0,
        "read-file query returns candidates",
    )

    check(
        all(
            isinstance(candidate, ToolCandidate)
            for candidate in candidates
        ),
        "discovery returns ToolCandidate objects",
    )

    read_candidate = discovery.select("read file")

    check(
        read_candidate is not None,
        "read-file query selects a tool",
    )

    check(
        read_candidate.name == "read_file",
        "read-file query selects read_file",
    )

    check(
        read_candidate.read_only is True,
        "selected read_file is read-only",
    )

    check(
        read_candidate.requires_confirmation is False,
        "selected read_file does not require confirmation",
    )

    search_candidate = discovery.select("search text")

    check(
        search_candidate is not None,
        "search query selects a tool",
    )

    check(
        search_candidate.name == "search_local_files",
        "search query selects search_local_files",
    )

    directory_candidate = discovery.select(
        "list directory"
    )

    check(
        directory_candidate is not None,
        "directory query selects a tool",
    )

    check(
        directory_candidate.name == "list_directory",
        "directory query selects list_directory",
    )

    info_candidate = discovery.select(
        "file metadata"
    )

    check(
        info_candidate is not None,
        "metadata query selects a tool",
    )

    check(
        info_candidate.name == "file_info",
        "metadata query selects file_info",
    )

    no_match = discovery.select(
        "financial transaction"
    )

    check(
        no_match is None,
        "unrelated query returns no tool",
    )

    empty_query_failed = False

    try:
        discovery.discover("")
    except ValueError:
        empty_query_failed = True

    check(
        empty_query_failed,
        "empty discovery query is rejected",
    )

    invalid_limit_failed = False

    try:
        discovery.discover(
            "read",
            max_results=0,
        )
    except ValueError:
        invalid_limit_failed = True

    check(
        invalid_limit_failed,
        "invalid result limit is rejected",
    )

    candidates = discovery.discover(
        "file",
        max_results=2,
    )

    check(
        len(candidates) <= 2,
        "max_results limit is respected",
    )

    scores = [candidate.score for candidate in candidates]

    check(
        scores == sorted(
            scores,
            reverse=True,
        ),
        "candidates are ordered by descending score",
    )

    check(
        all(candidate.score > 0 for candidate in candidates),
        "all returned candidates have positive scores",
    )

    print("=" * 60)
    print(
        "SAHIBEX 6K-3 TOOL DISCOVERY "
        "RUNTIME TEST: PASS"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
