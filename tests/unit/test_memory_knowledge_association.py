from core.research.memory_knowledge_association import (
    MemoryKnowledgeAssociation,
    MEMORY_KNOWLEDGE_ASSOCIATION_VERSION,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"[PASS] {message}")


def main() -> None:
    graph = MemoryKnowledgeAssociation()

    first = graph.link(
        memory_id="memory-001",
        target_id="concept-python",
        target_type="concept",
        strength=0.9,
        confidence=0.95,
        metadata={"shared": True},
    )

    check(
        first.association.source_memory_id == "memory-001",
        "memory identity preserved",
    )

    check(
        first.association.target_id == "concept-python",
        "concept identity preserved",
    )

    check(
        first.association.target_type == "concept",
        "target type preserved",
    )

    check(
        first.association.association_type == "memory_to_concept",
        "association type resolved",
    )

    check(
        first.association.strength == 0.9,
        "association strength preserved",
    )

    check(
        first.association.confidence == 0.95,
        "association confidence preserved",
    )

    second = graph.link(
        memory_id="memory-002",
        target_id="concept-python",
        target_type="concept",
    )

    check(
        second.association.target_id == "concept-python",
        "second memory shares concept identity",
    )

    links = graph.links_for_memory("memory-001")

    check(
        len(links) == 1,
        "memory association retrieval works",
    )

    memories = graph.memories_for_target(
        "concept-python",
        "concept",
    )

    check(
        memories == ("memory-001", "memory-002"),
        "shared concept reverse retrieval works",
    )

    duplicate = graph.link(
        memory_id="memory-001",
        target_id="concept-python",
        target_type="concept",
    )

    check(
        duplicate.created is False,
        "duplicate link does not create duplicate",
    )

    check(
        graph.association_count() == 2,
        "duplicate protection works",
    )

    summary = graph.summary()

    check(
        summary["version"] == MEMORY_KNOWLEDGE_ASSOCIATION_VERSION,
        "integration version is correct",
    )

    check(
        summary["link_based"] is True,
        "integration uses link-based architecture",
    )

    check(
        summary["duplicates_memory_content"] is False,
        "memory content is not duplicated",
    )

    check(
        summary["read_only"] is True,
        "integration layer is read-only",
    )

    check(
        summary["grants_permission"] is False,
        "integration grants no permission",
    )

    check(
        summary["executes_actions"] is False,
        "integration executes no actions",
    )

    check(
        summary["modifies_constitution"] is False,
        "integration cannot modify constitution",
    )

    blocked = False

    try:
        graph.link(
            memory_id="memory-003",
            target_id="bad-target",
            target_type="invalid",
        )
    except ValueError:
        blocked = True

    check(
        blocked,
        "invalid target type blocked",
    )

    print(
        "SAHIBEX PHASE 2 MEMORY-KNOWLEDGE ASSOCIATION "
        "INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
