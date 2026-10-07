from datetime import datetime, timedelta, timezone

from core.research.semantic_memory import (
    SEMANTIC_MEMORY_VERSION,
    SemanticMemory,
    SemanticMemoryStore,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    memory_1 = SemanticMemory(
        memory_id="semantic-001",
        concept="Python",
        meaning="A programming language used to build software.",
        source="test-source-1",
        confidence=0.95,
        importance=0.90,
        provenance={"source_id": "source-1"},
        tags=["programming", "language"],
        created_at=base_time,
        updated_at=base_time,
    )

    memory_2 = SemanticMemory(
        memory_id="semantic-002",
        concept="Python",
        meaning="A language commonly used for automation and AI.",
        source="test-source-2",
        confidence=0.85,
        importance=0.80,
        provenance={"source_id": "source-2"},
        tags=["programming", "ai"],
        created_at=base_time + timedelta(seconds=1),
        updated_at=base_time + timedelta(seconds=1),
    )

    memory_3 = SemanticMemory(
        memory_id="semantic-003",
        concept="Termux",
        meaning="An Android terminal environment.",
        source="test-source-3",
        confidence=0.90,
        importance=0.75,
        provenance={"source_id": "source-3"},
        tags=["android", "terminal"],
        created_at=base_time + timedelta(seconds=2),
        updated_at=base_time + timedelta(seconds=2),
    )

    check(memory_1.memory_id == "semantic-001", "semantic memory identity preserved")
    check(memory_1.concept == "Python", "semantic concept preserved")
    check(memory_1.meaning.startswith("A programming"), "semantic meaning preserved")
    check(memory_1.source == "test-source-1", "semantic source preserved")
    check(memory_1.provenance["source_id"] == "source-1", "semantic provenance preserved")

    store = SemanticMemoryStore(capacity=3)

    store.store(memory_1)
    store.store(memory_2)
    store.store(memory_3)

    check(store.count() == 3, "semantic memory storage works")
    check(store.get("semantic-001") == memory_1, "semantic memory retrieval works")
    check(store.contains("semantic-002"), "semantic memory identity lookup works")

    python_memories = store.by_concept("python")

    check(
        len(python_memories) == 2,
        "concept retrieval returns shared semantic memories",
    )

    check(
        python_memories[0].memory_id == "semantic-001",
        "concept retrieval ranks higher-value memory first",
    )

    ai_memories = store.by_tag("AI")

    check(
        len(ai_memories) == 1 and ai_memories[0].memory_id == "semantic-002",
        "tag retrieval works",
    )

    search_results = store.search("automation")

    check(
        len(search_results) == 1
        and search_results[0].memory_id == "semantic-002",
        "semantic text search works",
    )

    all_memories = store.all()

    check(
        len(all_memories) == 3,
        "semantic memory listing works",
    )

    check(
        all_memories[0].memory_id == "semantic-001",
        "semantic memory ranking works",
    )

    memory_4 = SemanticMemory(
        memory_id="semantic-004",
        concept="Old Concept",
        meaning="Old semantic information.",
        source="test-source-4",
        confidence=0.50,
        importance=0.20,
        provenance={"source_id": "source-4"},
        tags=["old"],
        created_at=base_time - timedelta(days=1),
        updated_at=base_time - timedelta(days=1),
    )

    store.store(memory_4)

    check(
        not store.contains("semantic-004"),
        "oldest semantic memory is evicted when capacity is exceeded",
    )

    check(
        store.contains("semantic-001"),
        "newer semantic memory is retained",
    )

    try:
        memory_1.meaning = "changed"
        immutable_blocked = False
    except (AttributeError, TypeError):
        immutable_blocked = True

    check(
        immutable_blocked,
        "semantic memory objects are immutable",
    )

    check(
        SEMANTIC_MEMORY_VERSION == "P2-SM-1",
        "semantic memory version is correct",
    )

    summary = store.summary()

    check(
        summary["preserves_meaning"] is True,
        "semantic meaning preservation enabled",
    )

    check(
        summary["preserves_provenance"] is True,
        "semantic provenance preservation enabled",
    )

    check(
        summary["supports_concept_retrieval"] is True,
        "concept retrieval capability enabled",
    )

    check(
        summary["supports_tag_retrieval"] is True,
        "tag retrieval capability enabled",
    )

    check(
        summary["supports_text_search"] is True,
        "semantic search capability enabled",
    )

    check(
        summary["grants_permission"] is False,
        "semantic memory grants no permission",
    )

    check(
        summary["executes_actions"] is False,
        "semantic memory executes no actions",
    )

    check(
        summary["modifies_constitution"] is False,
        "semantic memory cannot modify constitution",
    )

    removed = store.remove("semantic-002")

    check(
        removed is not None and not store.contains("semantic-002"),
        "semantic memory removal works",
    )

    store.clear()

    check(
        store.count() == 0,
        "semantic memory cleanup works",
    )

    print("SAHIBEX PHASE 2 #45 SEMANTIC MEMORY TEST: PASS")


if __name__ == "__main__":
    main()
