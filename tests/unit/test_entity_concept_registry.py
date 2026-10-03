from core.research.knowledge_registry import (
    Concept,
    Entity,
    KnowledgeRegistry,
)


def main() -> None:
    print("SAHIBEX 6H-2 ENTITY & CONCEPT REGISTRY TEST")

    registry = KnowledgeRegistry()

    # Entity registration
    entity = Entity(
        entity_id="entity_001",
        name="OpenAI",
        entity_type="organization",
    )

    result = registry.register_entity(entity)

    assert result.is_new is True
    assert result.entity == entity
    assert registry.entity_count() == 1

    print("[PASS] entity registration")

    # Duplicate entity ID protection
    duplicate_entity = Entity(
        entity_id="entity_001",
        name="Different Name",
        entity_type="organization",
    )

    duplicate_result = registry.register_entity(
        duplicate_entity
    )

    assert duplicate_result.is_new is False
    assert duplicate_result.entity == entity
    assert registry.entity_count() == 1

    print("[PASS] duplicate entity identity protection")

    # Entity lookup
    assert registry.get_entity("entity_001") == entity
    assert registry.contains_entity("entity_001") is True
    assert registry.contains_entity("missing") is False

    print("[PASS] entity lookup")

    # Entity require
    assert registry.require_entity("entity_001") == entity

    try:
        registry.require_entity("missing")
    except KeyError:
        pass
    else:
        raise AssertionError(
            "unknown entity should raise KeyError"
        )

    print("[PASS] unknown entity protection")

    # Concept registration
    concept = Concept(
        concept_id="concept_001",
        name="Artificial Intelligence",
        concept_type="technology",
    )

    concept_result = registry.register_concept(concept)

    assert concept_result.is_new is True
    assert concept_result.concept == concept
    assert registry.concept_count() == 1

    print("[PASS] concept registration")

    # Duplicate concept ID protection
    duplicate_concept = Concept(
        concept_id="concept_001",
        name="Different Concept",
        concept_type="topic",
    )

    duplicate_concept_result = (
        registry.register_concept(duplicate_concept)
    )

    assert duplicate_concept_result.is_new is False
    assert duplicate_concept_result.concept == concept
    assert registry.concept_count() == 1

    print("[PASS] duplicate concept identity protection")

    # Concept lookup
    assert registry.get_concept("concept_001") == concept
    assert registry.contains_concept("concept_001") is True
    assert registry.contains_concept("missing") is False

    print("[PASS] concept lookup")

    # Concept require
    assert registry.require_concept("concept_001") == concept

    try:
        registry.require_concept("missing")
    except KeyError:
        pass
    else:
        raise AssertionError(
            "unknown concept should raise KeyError"
        )

    print("[PASS] unknown concept protection")

    # Registry summary
    summary = registry.summary()

    assert summary["entity_count"] == 1
    assert summary["concept_count"] == 1

    print("[PASS] registry summary")

    # Clear
    registry.clear()

    assert registry.entity_count() == 0
    assert registry.concept_count() == 0

    print("[PASS] registry clear")

    print("SAHIBEX 6H-2 ENTITY & CONCEPT REGISTRY TEST: PASS")


if __name__ == "__main__":
    main()
