from core.research.models import ResearchSource
from core.research.source_registry import SourceRegistry


def make_source(
    source_id: str,
    locator: str,
    title: str = "AI Security",
    publisher: str = "Example Research",
) -> ResearchSource:
    return ResearchSource(
        source_id=source_id,
        title=title,
        source_type="web",
        locator=locator,
        publisher=publisher,
        reliability=0.9,
    )


def main() -> None:
    registry = SourceRegistry()

    source = make_source(
        "src-001",
        "https://example.com/ai-security",
    )

    result = registry.register(source)

    assert result.is_new is True
    assert registry.count() == 1
    assert registry.get("src-001") == source

    duplicate = make_source(
        "src-002",
        "https://example.com/ai-security",
    )

    duplicate_result = registry.register(duplicate)

    assert duplicate_result.is_new is False
    assert duplicate_result.source.source_id == "src-001"
    assert registry.count() == 1

    found = registry.find_by_locator(
        " HTTPS://EXAMPLE.COM/AI-SECURITY "
    )

    assert found is not None
    assert found.source_id == "src-001"

    matches = registry.find(
        title="AI Security",
        publisher="Example Research",
    )

    assert len(matches) == 1
    assert matches[0].source_id == "src-001"

    assert registry.contains("src-001") is True
    assert registry.contains("missing") is False

    try:
        registry.require("missing")
    except KeyError:
        pass
    else:
        raise AssertionError("Unknown source was not rejected")

    summary = registry.summary()

    assert summary["source_count"] == 1
    assert summary["locator_index_count"] == 1

    registry.clear()

    assert registry.count() == 0

    print("SAHIBEX SOURCE REGISTRY TEST")
    print("[PASS] source registration")
    print("[PASS] duplicate locator protection")
    print("[PASS] locator lookup")
    print("[PASS] source search")
    print("[PASS] unknown source protection")
    print("[PASS] registry summary")
    print("[PASS] registry clear")
    print("SAHIBEX SOURCE REGISTRY TEST: PASS")


if __name__ == "__main__":
    main()
