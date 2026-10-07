from core.brain.context_extraction import (
    ContextExtractionEngine,
)


def test_direct_context_extraction() -> None:
    engine = ContextExtractionEngine()

    result = engine.extract(
        input_id="input-1",
        content="SAHIBEX created a new file.",
        source_id="user",
        timestamp="2026-10-05T00:00:00+00:00",
        subjects=["SAHIBEX"],
        actions=["created"],
        objects=["file"],
        events=["created"],
        attributes=["new"],
        entity_candidates=["entity-1"],
        event_candidates=["event-1"],
    )

    assert result.input_id == "input-1"
    assert result.source_id == "user"
    assert result.subjects == ("SAHIBEX",)
    assert result.actions == ("created",)
    assert result.objects == ("file",)
    assert result.events == ("created",)
    assert result.attributes == ("new",)
    assert result.entity_ids == ("entity-1",)
    assert result.event_ids == ("event-1",)
    assert result.has_event is True
    assert result.has_entities is True
    assert result.signal_count == 7


def test_duplicate_signals_are_removed() -> None:
    engine = ContextExtractionEngine()

    result = engine.extract(
        input_id="input-2",
        content="test",
        source_id="source",
        timestamp="time",
        subjects=["SAHIBEX", "SAHIBEX"],
        actions=["create", "create"],
        events=["created", "created"],
    )

    assert result.subjects == ("SAHIBEX",)
    assert result.actions == ("create",)
    assert result.events == ("created",)


def test_perception_integration() -> None:
    from core.brain.perception import PerceptionParser

    perception = PerceptionParser().parse(
        input_id="input-perception-1",
        content="SAHIBEX created a new file.",
    )
    result = ContextExtractionEngine.from_perception(
        perception,
        source_id="user",
        timestamp="2026-10-05T00:00:00+00:00",
        entity_candidates=["entity-1"],
        event_candidates=["event-1"],
    )

    assert result.input_id == perception.input_id
    assert result.content == perception.content
    assert result.events
    assert result.entity_ids == ("entity-1",)
    assert result.event_ids == ("event-1",)


def test_invalid_input_is_blocked() -> None:
    engine = ContextExtractionEngine()

    try:
        engine.extract(
            input_id="",
            content="test",
            source_id="source",
            timestamp="time",
        )
        raise AssertionError("empty input_id must fail")
    except ValueError:
        pass


def test_security_boundaries() -> None:
    assert ContextExtractionEngine.is_read_only() is True
    assert ContextExtractionEngine.grants_permission() is False
    assert ContextExtractionEngine.executes_actions() is False
    assert ContextExtractionEngine.modifies_memory() is False
    assert ContextExtractionEngine.modifies_knowledge() is False
    assert ContextExtractionEngine.verifies_truth() is False


def main() -> None:
    test_direct_context_extraction()
    test_duplicate_signals_are_removed()
    test_perception_integration()
    test_invalid_input_is_blocked()
    test_security_boundaries()

    print("SAHIBEX PHASE 1 #30 CONTEXT EXTRACTION TEST: PASS")


if __name__ == "__main__":
    main()
