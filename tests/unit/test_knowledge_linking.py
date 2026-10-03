from core.research.knowledge_linking import (
    KnowledgeLink,
    KnowledgeLinker,
)


def main() -> None:
    print("SAHIBEX 6H-5 KNOWLEDGE LINKING TEST")

    linker = KnowledgeLinker()

    # ---------------------------------------------------------
    # Knowledge -> Entity
    # ---------------------------------------------------------

    entity_link = linker.link(
        knowledge_id="knowledge_001",
        target_id="entity_001",
        target_type="entity",
    )

    assert isinstance(entity_link, KnowledgeLink)
    assert entity_link.knowledge_id == "knowledge_001"
    assert entity_link.target_id == "entity_001"
    assert entity_link.target_type == "entity"

    print("[PASS] knowledge to entity linking")

    # ---------------------------------------------------------
    # Knowledge -> Concept
    # ---------------------------------------------------------

    concept_link = linker.link(
        knowledge_id="knowledge_001",
        target_id="concept_001",
        target_type="concept",
    )

    assert concept_link.knowledge_id == "knowledge_001"
    assert concept_link.target_id == "concept_001"
    assert concept_link.target_type == "concept"

    print("[PASS] knowledge to concept linking")

    # ---------------------------------------------------------
    # Knowledge -> Relationship
    # ---------------------------------------------------------

    relationship_link = linker.link(
        knowledge_id="knowledge_001",
        target_id="rel_001",
        target_type="relationship",
    )

    assert relationship_link.knowledge_id == "knowledge_001"
    assert relationship_link.target_id == "rel_001"
    assert relationship_link.target_type == "relationship"

    print("[PASS] knowledge to relationship linking")

    # ---------------------------------------------------------
    # Duplicate protection
    # ---------------------------------------------------------

    duplicate = linker.link(
        knowledge_id="knowledge_001",
        target_id="entity_001",
        target_type="entity",
    )

    assert duplicate == entity_link

    print("[PASS] duplicate link protection")

    # ---------------------------------------------------------
    # Retrieve links for knowledge
    # ---------------------------------------------------------

    links = linker.links_for_knowledge(
        "knowledge_001"
    )

    assert len(links) == 3

    assert {
        (item.target_id, item.target_type)
        for item in links
    } == {
        ("entity_001", "entity"),
        ("concept_001", "concept"),
        ("rel_001", "relationship"),
    }

    print("[PASS] knowledge link retrieval")

    # ---------------------------------------------------------
    # Retrieve knowledge IDs for target
    # ---------------------------------------------------------

    knowledge_ids = linker.knowledge_for_target(
        target_id="entity_001",
        target_type="entity",
    )

    assert knowledge_ids == [
        "knowledge_001"
    ]

    print("[PASS] reverse knowledge lookup")

    # ---------------------------------------------------------
    # Invalid knowledge ID
    # ---------------------------------------------------------

    try:
        linker.link(
            knowledge_id="",
            target_id="entity_002",
            target_type="entity",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty knowledge_id should be rejected"
        )

    print("[PASS] empty knowledge ID protection")

    # ---------------------------------------------------------
    # Invalid target ID
    # ---------------------------------------------------------

    try:
        linker.link(
            knowledge_id="knowledge_002",
            target_id="",
            target_type="entity",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty target_id should be rejected"
        )

    print("[PASS] empty target ID protection")

    # ---------------------------------------------------------
    # Invalid target type
    # ---------------------------------------------------------

    try:
        linker.link(
            knowledge_id="knowledge_002",
            target_id="entity_002",
            target_type="invalid",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "invalid target_type should be rejected"
        )

    print("[PASS] target type protection")

    # ---------------------------------------------------------
    # Unknown knowledge has no links
    # ---------------------------------------------------------

    assert (
        linker.links_for_knowledge(
            "knowledge_unknown"
        )
        == []
    )

    print("[PASS] unknown knowledge lookup")

    print("SAHIBEX 6H-5 KNOWLEDGE LINKING TEST: PASS")


if __name__ == "__main__":
    main()
