from core.research.relationship import Relationship


def main() -> None:
    print("SAHIBEX 6H-3 RELATIONSHIP MODEL TEST")

    relationship = Relationship(
        relationship_id="rel_001",
        source_id="entity_001",
        source_type="entity",
        relationship_type="develops",
        target_id="concept_001",
        target_type="concept",
    )

    assert relationship.relationship_id == "rel_001"
    assert relationship.source_id == "entity_001"
    assert relationship.source_type == "entity"
    assert relationship.relationship_type == "develops"
    assert relationship.target_id == "concept_001"
    assert relationship.target_type == "concept"

    print("[PASS] relationship fields")

    # Metadata
    relationship_with_metadata = Relationship(
        relationship_id="rel_002",
        source_id="concept_001",
        source_type="concept",
        relationship_type="includes",
        target_id="concept_002",
        target_type="concept",
        metadata={
            "confidence": 0.90,
            "origin": "research",
        },
    )

    assert relationship_with_metadata.metadata["confidence"] == 0.90
    assert relationship_with_metadata.metadata["origin"] == "research"

    print("[PASS] relationship metadata")

    # Empty ID protection
    try:
        Relationship(
            relationship_id="",
            source_id="entity_001",
            source_type="entity",
            relationship_type="develops",
            target_id="concept_001",
            target_type="concept",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty relationship_id should be rejected"
        )

    print("[PASS] empty relationship ID protection")

    # Empty source protection
    try:
        Relationship(
            relationship_id="rel_003",
            source_id="",
            source_type="entity",
            relationship_type="develops",
            target_id="concept_001",
            target_type="concept",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty source_id should be rejected"
        )

    print("[PASS] empty source protection")

    # Empty relationship type protection
    try:
        Relationship(
            relationship_id="rel_004",
            source_id="entity_001",
            source_type="entity",
            relationship_type="",
            target_id="concept_001",
            target_type="concept",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty relationship_type should be rejected"
        )

    print("[PASS] empty relationship type protection")

    # Empty target protection
    try:
        Relationship(
            relationship_id="rel_005",
            source_id="entity_001",
            source_type="entity",
            relationship_type="develops",
            target_id="",
            target_type="concept",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty target_id should be rejected"
        )

    print("[PASS] empty target protection")

    # Self relationship is allowed at the model level.
    # Higher-level graph rules may restrict it later.
    self_relationship = Relationship(
        relationship_id="rel_006",
        source_id="concept_001",
        source_type="concept",
        relationship_type="related_to",
        target_id="concept_001",
        target_type="concept",
    )

    assert (
        self_relationship.source_id
        == self_relationship.target_id
    )

    print("[PASS] self relationship representation")

    print("SAHIBEX 6H-3 RELATIONSHIP MODEL TEST: PASS")


if __name__ == "__main__":
    main()
