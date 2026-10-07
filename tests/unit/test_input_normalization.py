from core.brain.input_normalization import (
    InputNormalizationEngine,
    NormalizedInput,
)


def main() -> None:
    engine = InputNormalizationEngine()

    # 1. Common normalization
    result = engine.normalize(
        modality="  TEXT ",
        content="  Hello    SAHIBEX   world.  ",
        source_id="  user-001 ",
        timestamp="  2026-10-05T19:00:00+05:30 ",
        confidence=0.90,
        input_id="input-001",
        metadata={"channel": "user"},
    )

    assert isinstance(result, NormalizedInput)
    assert result.modality == "text"
    assert result.content == "Hello SAHIBEX world."
    assert result.source_id == "user-001"
    assert result.timestamp == "2026-10-05T19:00:00+05:30"
    assert result.confidence == 0.90
    assert result.input_id == "input-001"
    assert result.metadata == {"channel": "user"}

    # 2. Modality normalization
    image_result = engine.normalize(
        modality=" IMAGE ",
        content="  Object detected  ",
        source_id="camera-01",
        timestamp="2026-10-05T19:01:00+05:30",
        confidence=0.80,
    )

    assert image_result.modality == "image"
    assert image_result.content == "Object detected"

    # 3. Child input compatibility
    child_result = engine.normalize(
        modality=" CHILD ",
        content="  Child reports anomaly.  ",
        source_id="child-001",
        timestamp="2026-10-05T19:02:00+05:30",
        confidence=0.85,
    )

    assert child_result.modality == "child"
    assert child_result.content == "Child reports anomaly."
    assert child_result.source_id == "child-001"

    # 4. Confidence must be preserved, not invented
    assert child_result.confidence == 0.85

    # 5. Automatic input ID
    assert isinstance(child_result.input_id, str)
    assert child_result.input_id

    # 6. Invalid confidence
    try:
        engine.normalize(
            modality="sensor",
            content="Temperature",
            source_id="sensor-01",
            timestamp="2026-10-05T19:03:00+05:30",
            confidence=1.5,
        )
        raise AssertionError(
            "invalid confidence was accepted"
        )
    except ValueError:
        pass

    # 7. Empty content
    try:
        engine.normalize(
            modality="text",
            content="   ",
            source_id="user-001",
            timestamp="2026-10-05T19:04:00+05:30",
            confidence=0.5,
        )
        raise AssertionError(
            "empty content was accepted"
        )
    except ValueError:
        pass

    # 8. Security boundary
    assert engine.is_read_only() is True
    assert engine.grants_permission() is False
    assert engine.executes_actions() is False
    assert engine.modifies_sources() is False
    assert engine.changes_semantic_meaning() is False

    print(
        "SAHIBEX PHASE 1 #25 INPUT NORMALIZATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
