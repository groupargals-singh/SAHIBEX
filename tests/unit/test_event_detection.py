from core.brain.event_detection import (
    EventCandidate,
    EventDetectionEngine,
    EventDetectionResult,
)
from core.brain.perception import PerceptionParser


def main() -> None:
    engine = EventDetectionEngine()

    # Direct event detection.
    result = engine.detect(
        input_id="input-001",
        events=("failed", "stopped"),
    )

    assert isinstance(
        result,
        EventDetectionResult,
    )

    assert result.input_id == "input-001"
    assert len(result.events) == 2

    event_types = {
        event.event_type
        for event in result.events
    }

    assert "failed" in event_types
    assert "stopped" in event_types

    for event in result.events:
        assert isinstance(event, EventCandidate)
        assert event.source_input_id == "input-001"
        assert 0.0 <= event.confidence <= 1.0

    # Duplicate events are removed.
    duplicate = engine.detect(
        input_id="input-002",
        events=(
            "failed",
            "failed",
            "stopped",
            "stopped",
        ),
    )

    assert len(duplicate.events) == 2

    # Existing #27 perception pipeline integration.
    parser = PerceptionParser()

    perception = parser.parse(
        input_id="input-003",
        content="The system failed and stopped.",
    )

    integrated = engine.detect_from_perception(
        perception
    )

    assert integrated.input_id == "input-003"

    integrated_types = {
        event.event_type
        for event in integrated.events
    }

    assert integrated_types == {
        "failed",
        "stopped",
    }

    # No event must be invented.
    empty = engine.detect(
        input_id="input-004",
        events=(),
    )

    assert empty.events == ()

    # Invalid input must fail closed.
    try:
        engine.detect(
            input_id="   ",
            events=("failed",),
        )
        raise AssertionError(
            "empty input_id was accepted"
        )
    except ValueError:
        pass

    try:
        engine.detect(
            input_id="input-005",
            events=["failed"],
        )
        raise AssertionError(
            "list events were accepted"
        )
    except TypeError:
        pass

    try:
        engine.detect(
            input_id="input-006",
            events=(123,),
        )
        raise AssertionError(
            "non-string event was accepted"
        )
    except TypeError:
        pass

    # Security / authority boundaries.
    assert engine.is_read_only() is True
    assert engine.grants_permission() is False
    assert engine.executes_actions() is False
    assert engine.verifies_truth() is False
    assert engine.persists_events() is False

    print(
        "SAHIBEX PHASE 1 #29 EVENT DETECTION TEST: PASS"
    )


if __name__ == "__main__":
    main()
