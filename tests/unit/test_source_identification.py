from core.brain.source_identification import (
    SourceIdentificationEngine,
    SourceType,
)


def test_source_identification() -> None:
    engine = SourceIdentificationEngine()

    result = engine.identify(
        input_id="input-1",
        source_type=SourceType.HUMAN,
        source_id="user-1",
        origin="direct_user_input",
        provenance_reference="conversation-1",
    )

    assert result.source_type is SourceType.HUMAN
    assert result.source_id == "user-1"
    assert result.origin == "direct_user_input"
    assert result.provenance_reference == "conversation-1"


def test_string_source_type_is_normalized() -> None:
    engine = SourceIdentificationEngine()

    result = engine.identify(
        input_id="input-2",
        source_type="web",
        source_id="web-source-1",
    )

    assert result.source_type is SourceType.WEB
    assert result.origin == "web"


def test_all_source_types_are_supported() -> None:
    engine = SourceIdentificationEngine()

    for source_type in SourceType:
        result = engine.identify(
            input_id=f"input-{source_type.value}",
            source_type=source_type,
            source_id=f"source-{source_type.value}",
        )

        assert result.source_type is source_type


def test_invalid_source_type_is_blocked() -> None:
    engine = SourceIdentificationEngine()

    try:
        engine.identify(
            input_id="input-3",
            source_type="not-a-source",
            source_id="source-3",
        )
        raise AssertionError("invalid source type must fail")
    except ValueError:
        pass


def test_invalid_input_is_blocked() -> None:
    engine = SourceIdentificationEngine()

    try:
        engine.identify(
            input_id="",
            source_type=SourceType.HUMAN,
            source_id="user-1",
        )
        raise AssertionError("empty input_id must fail")
    except ValueError:
        pass


def test_security_boundary() -> None:
    assert SourceIdentificationEngine.is_read_only() is True
    assert SourceIdentificationEngine.judges_quality() is False
    assert SourceIdentificationEngine.determines_truth() is False
    assert SourceIdentificationEngine.grants_permission() is False
    assert SourceIdentificationEngine.executes_actions() is False
    assert SourceIdentificationEngine.modifies_memory() is False
    assert SourceIdentificationEngine.modifies_knowledge() is False


def main() -> None:
    test_source_identification()
    test_string_source_type_is_normalized()
    test_all_source_types_are_supported()
    test_invalid_source_type_is_blocked()
    test_invalid_input_is_blocked()
    test_security_boundary()

    print("SAHIBEX PHASE 1 #32 SOURCE IDENTIFICATION TEST: PASS")


if __name__ == "__main__":
    main()
