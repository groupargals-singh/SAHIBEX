from core.brain.input_validation import InputValidationEngine


def main() -> None:
    engine = InputValidationEngine()

    valid = engine.validate(
        input_id="in-1",
        modality="text",
        content="hello",
        source_id="user",
        timestamp="2026-10-07T10:00:00+00:00",
        confidence=0.9,
        metadata={"language": "hi"},
    )
    assert valid.valid is True
    assert valid.errors == ()
    assert valid.modality == "text"

    invalid = engine.validate(
        input_id="",
        modality="",
        content="",
        source_id="",
        timestamp="",
        confidence=1.5,
        metadata=[],
    )
    assert invalid.valid is False
    assert "invalid_input_id" in invalid.errors
    assert "empty_content" in invalid.errors
    assert "confidence_out_of_range" in invalid.errors
    assert "metadata_must_be_dictionary" in invalid.errors

    unknown = engine.validate(
        input_id="in-2",
        modality="unknown",
        content="data",
        source_id="sensor",
        timestamp="2026-10-07T10:00:00+00:00",
        confidence=0.5,
    )
    assert unknown.valid is True
    assert "unknown_modality" in unknown.warnings

    assert engine.is_read_only() is True
    assert engine.grants_permission() is False
    assert engine.executes_actions() is False
    assert engine.verifies_truth() is False
    assert engine.modifies_sources() is False

    print("SAHIBEX PHASE B INPUT VALIDATION TEST: PASS")


if __name__ == "__main__":
    main()
