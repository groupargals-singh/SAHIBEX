from core.brain.entity_identification import (
    EntityCandidate,
    EntityIdentificationEngine,
    EntityIdentificationResult,
)
from core.research.knowledge_registry import Entity


def main() -> None:
    engine = EntityIdentificationEngine()

    result = engine.identify(
        input_id="input-001",
        content="Build SAHIBEX using Python on Termux.",
    )

    assert isinstance(
        result,
        EntityIdentificationResult,
    )

    assert result.input_id == "input-001"
    assert len(result.candidates) == 3

    names = {
        candidate.entity.name
        for candidate in result.candidates
    }

    assert "sahibex" in names
    assert "python" in names
    assert "termux" in names

    for candidate in result.candidates:
        assert isinstance(candidate, EntityCandidate)
        assert isinstance(candidate.entity, Entity)
        assert 0.0 <= candidate.confidence <= 1.0
        assert (
            candidate.source_input_id
            == "input-001"
        )

    # Duplicate entity must be deduplicated.
    duplicate = engine.identify(
        input_id="input-002",
        content="Python Python Python.",
    )

    assert len(duplicate.candidates) == 1

    # Unknown entities are not invented.
    unknown = engine.identify(
        input_id="input-003",
        content="This contains an unknownthing.",
    )

    assert unknown.candidates == ()

    # Invalid input must fail closed.
    try:
        engine.identify(
            input_id="   ",
            content="Python",
        )
        raise AssertionError(
            "empty input_id was accepted"
        )
    except ValueError:
        pass

    try:
        engine.identify(
            input_id="input-004",
            content="   ",
        )
        raise AssertionError(
            "empty content was accepted"
        )
    except ValueError:
        pass

    # Security / persistence boundaries.
    assert engine.is_persistent() is False
    assert engine.verifies_identity() is False
    assert engine.grants_permission() is False
    assert engine.executes_actions() is False

    print(
        "SAHIBEX PHASE 1 #28 ENTITY IDENTIFICATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
