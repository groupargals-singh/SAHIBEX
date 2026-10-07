from core.brain.meaning_interpretation import (
    MeaningInterpretationEngine,
)


def test_meaning_interpretation() -> None:
    engine = MeaningInterpretationEngine()

    result = engine.interpret(
        input_id="input-1",
        content="SAHIBEX created a new file.",
        subjects=["SAHIBEX"],
        actions=["created"],
        objects=["file"],
        events=["created"],
        attributes=["new"],
    )

    assert result.input_id == "input-1"
    assert result.subject == "SAHIBEX"
    assert "created" in result.situation
    assert "new" in result.state
    assert result.relationships == ("created -> file",)
    assert result.confidence > 0.0
    assert result.interpretation


def test_duplicate_signals_are_removed() -> None:
    engine = MeaningInterpretationEngine()

    result = engine.interpret(
        input_id="input-2",
        content="test",
        subjects=["SAHIBEX", "SAHIBEX"],
        actions=["create", "create"],
        objects=["file", "file"],
    )

    assert result.context_signals.count("SAHIBEX") == 1
    assert result.context_signals.count("create") == 1
    assert result.relationships == ("create -> file",)


def test_empty_signals_are_safe() -> None:
    engine = MeaningInterpretationEngine()

    result = engine.interpret(
        input_id="input-3",
        content="Something happened.",
    )

    assert result.subject == "unknown subject"
    assert result.situation == "general situation"
    assert result.state == "state unknown"
    assert result.confidence == 0.30


def test_invalid_input_is_blocked() -> None:
    engine = MeaningInterpretationEngine()

    try:
        engine.interpret(
            input_id="",
            content="test",
        )
        raise AssertionError("empty input_id must fail")
    except ValueError:
        pass


def test_security_boundaries() -> None:
    assert MeaningInterpretationEngine.is_read_only() is True
    assert MeaningInterpretationEngine.grants_permission() is False
    assert MeaningInterpretationEngine.executes_actions() is False
    assert MeaningInterpretationEngine.modifies_memory() is False
    assert MeaningInterpretationEngine.modifies_knowledge() is False
    assert MeaningInterpretationEngine.verifies_truth() is False


def main() -> None:
    test_meaning_interpretation()
    test_duplicate_signals_are_removed()
    test_empty_signals_are_safe()
    test_invalid_input_is_blocked()
    test_security_boundaries()

    print("SAHIBEX PHASE 1 #31 MEANING INTERPRETATION TEST: PASS")


if __name__ == "__main__":
    main()
