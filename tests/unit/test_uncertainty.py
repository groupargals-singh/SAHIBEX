from core.brain.uncertainty import (
    UNCERTAINTY_VERSION,
    UncertaintyEngine,
    UncertaintyLevel,
)


def test_low_uncertainty_for_strong_input() -> None:
    engine = UncertaintyEngine()

    result = engine.assess(
        input_id="input_001",
        confidence=0.95,
        quality_score=0.95,
        conflict_score=0.0,
    )

    assert result.uncertainty < 0.20
    assert result.level == UncertaintyLevel.VERY_LOW
    assert result.uncertain is False
    assert result.requires_verification is False
    assert result.version == UNCERTAINTY_VERSION


def test_high_uncertainty_for_weak_input() -> None:
    engine = UncertaintyEngine()

    result = engine.assess(
        input_id="input_002",
        confidence=0.20,
        quality_score=0.20,
        conflict_score=0.80,
        missing_information=True,
        ambiguous=True,
    )

    assert result.uncertainty >= 0.60
    assert result.level in (
        UncertaintyLevel.HIGH,
        UncertaintyLevel.VERY_HIGH,
    )
    assert result.uncertain is True
    assert result.requires_verification is True
    assert "missing_information" in result.reasons
    assert "ambiguous_input" in result.reasons
    assert "conflicting_signals" in result.reasons


def test_medium_uncertainty() -> None:
    engine = UncertaintyEngine()

    result = engine.assess(
        input_id="input_003",
        confidence=0.50,
        quality_score=0.50,
        conflict_score=0.40,
    )

    assert 0.20 <= result.uncertainty < 0.60
    assert result.level == UncertaintyLevel.MEDIUM
    assert result.uncertain is True


def test_security_and_scope_boundary() -> None:
    engine = UncertaintyEngine()

    assert engine.is_truth_score() is False
    assert engine.performs_verification() is False
    assert engine.performs_research() is False
    assert engine.resolves_conflicts() is False
    assert engine.grants_permission() is False
    assert engine.executes_actions() is False
    assert engine.modifies_source() is False


def test_invalid_score_rejected() -> None:
    engine = UncertaintyEngine()

    try:
        engine.assess(
            input_id="input_004",
            confidence=1.5,
            quality_score=0.8,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid confidence was not rejected")


if __name__ == "__main__":
    test_low_uncertainty_for_strong_input()
    test_high_uncertainty_for_weak_input()
    test_medium_uncertainty()
    test_security_and_scope_boundary()
    test_invalid_score_rejected()

    print("SAHIBEX PHASE 1 #34 UNCERTAINTY TEST: PASS")
