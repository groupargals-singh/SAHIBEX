from core.research.memory_association import (
    MemoryAssociation,
    MemoryAssociationEngine,
)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX PHASE 2 MEMORY ASSOCIATION TEST")

    engine = MemoryAssociationEngine()

    association = engine.associate(
        "memory-001",
        "concept-python",
        "concept",
        "memory_to_concept",
        strength=0.9,
        confidence=0.95,
    )

    check(
        isinstance(association, MemoryAssociation),
        "association object created",
    )

    check(
        association.source_memory_id == "memory-001",
        "source memory preserved",
    )

    check(
        association.target_id == "concept-python",
        "shared target identity preserved",
    )

    check(
        association.strength == 0.9,
        "association strength preserved",
    )

    check(
        association.confidence == 0.95,
        "association confidence preserved",
    )

    memory_links = engine.associations_for_memory("memory-001")

    check(
        len(memory_links) == 1,
        "memory association retrieval works",
    )

    target_memories = engine.memories_for_target(
        "concept-python",
        "concept",
    )

    check(
        target_memories == ("memory-001",),
        "reverse association retrieval works",
    )

    duplicate = engine.associate(
        "memory-001",
        "concept-python",
        "concept",
        "memory_to_concept",
        strength=0.1,
        confidence=0.1,
    )

    check(
        duplicate.association_id == association.association_id,
        "duplicate association reuses existing link",
    )

    engine.associate(
        "memory-002",
        "concept-python",
        "concept",
        "memory_to_concept",
    )

    check(
        engine.association_count() == 2,
        "shared concept supports multiple memories",
    )

    summary = engine.summary()

    check(
        summary["read_only"] is True,
        "association layer is read-only",
    )

    check(
        summary["grants_permission"] is False,
        "association layer grants no permission",
    )

    check(
        summary["executes_actions"] is False,
        "association layer executes no actions",
    )

    check(
        summary["modifies_constitution"] is False,
        "association layer cannot modify constitution",
    )

    try:
        MemoryAssociation(
            association_id="bad",
            source_memory_id="memory",
            target_id="concept",
            target_type="concept",
            association_type="invalid",
        )
    except ValueError:
        print("[PASS] invalid association type blocked")
    else:
        raise AssertionError("invalid association type was accepted")

    print("SAHIBEX PHASE 2 MEMORY ASSOCIATION TEST: PASS")


if __name__ == "__main__":
    main()
