from core.brain.input_confidence import (
    InputConfidenceAssessment,
    InputConfidenceEngine,
    InputConfidenceLevel,
)


def main() -> None:
    engine = InputConfidenceEngine()

    # Very high
    result = engine.assess(
        input_id="input-001",
        confidence=0.95,
    )

    assert isinstance(
        result,
        InputConfidenceAssessment,
    )
    assert result.level is InputConfidenceLevel.VERY_HIGH
    assert result.confidence == 0.95

    # High
    result = engine.assess(
        input_id="input-002",
        confidence=0.80,
    )

    assert result.level is InputConfidenceLevel.HIGH

    # Medium
    result = engine.assess(
        input_id="input-003",
        confidence=0.50,
    )

    assert result.level is InputConfidenceLevel.MEDIUM

    # Low
    result = engine.assess(
        input_id="input-004",
        confidence=0.25,
    )

    assert result.level is InputConfidenceLevel.LOW

    # Very low
    result = engine.assess(
        input_id="input-005",
        confidence=0.10,
    )

    assert result.level is InputConfidenceLevel.VERY_LOW

    # Boundary checks
    assert (
        engine.assess(
            input_id="boundary-high",
            confidence=0.90,
        ).level
        is InputConfidenceLevel.VERY_HIGH
    )

    assert (
        engine.assess(
            input_id="boundary-medium",
            confidence=0.40,
        ).level
        is InputConfidenceLevel.MEDIUM
    )

    assert (
        engine.assess(
            input_id="boundary-low",
            confidence=0.20,
        ).level
        is InputConfidenceLevel.LOW
    )

    # Invalid confidence must fail closed
    try:
        engine.assess(
            input_id="invalid",
            confidence=1.5,
        )
        raise AssertionError(
            "invalid confidence was accepted"
        )
    except ValueError:
        pass

    # Invalid input ID
    try:
        engine.assess(
            input_id="   ",
            confidence=0.5,
        )
        raise AssertionError(
            "empty input ID was accepted"
        )
    except ValueError:
        pass

    # Security / authority boundaries
    assert engine.is_truth_score() is False
    assert engine.replaces_verification() is False
    assert engine.replaces_research_confidence() is False
    assert engine.grants_permission() is False
    assert engine.executes_actions() is False

    print(
        "SAHIBEX PHASE 1 #26 INPUT CONFIDENCE TEST: PASS"
    )


if __name__ == "__main__":
    main()
