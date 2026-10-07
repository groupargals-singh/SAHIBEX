from datetime import datetime, timezone

from core.brain.data_quality import (
    DATA_QUALITY_VERSION,
    DataQualityEngine,
)


def test_high_quality_input() -> None:
    engine = DataQualityEngine()

    result = engine.assess(
        input_id="input_001",
        content="SAHIBEX data quality test",
        source_id="terminal",
        timestamp="2026-10-05T10:00:00+00:00",
        confidence=0.90,
        metadata={
            "modality": "text",
            "source_type": "terminal",
            "origin": "user",
            "content_type": "text",
            "language": "en",
        },
        now=datetime(2026, 10, 5, 10, 1, tzinfo=timezone.utc),
    )

    assert result.input_id == "input_001"
    assert result.quality_score >= 0.80
    assert result.high_quality is True
    assert result.acceptable is True
    assert result.version == DATA_QUALITY_VERSION


def test_missing_content_is_detected() -> None:
    engine = DataQualityEngine()

    result = engine.assess(
        input_id="input_002",
        content="",
        source_id="terminal",
        timestamp="2026-10-05T10:00:00+00:00",
        confidence=0.80,
        metadata={"modality": "text"},
        now=datetime(2026, 10, 5, 10, 1, tzinfo=timezone.utc),
    )

    assert "missing_content" in result.issues
    assert result.completeness_score < 1.0


def test_invalid_timestamp_is_detected() -> None:
    engine = DataQualityEngine()

    result = engine.assess(
        input_id="input_003",
        content="test",
        source_id="terminal",
        timestamp="not-a-timestamp",
        confidence=0.80,
        metadata={"modality": "text"},
    )

    assert "invalid_timestamp_format" in result.issues
    assert result.freshness_score == 0.0


def test_security_boundary() -> None:
    engine = DataQualityEngine()

    assert engine.is_read_only() is True
    assert engine.grants_permission() is False
    assert engine.executes_actions() is False
    assert engine.verifies_truth() is False
    assert engine.modifies_source() is False


def test_invalid_confidence_is_rejected() -> None:
    engine = DataQualityEngine()

    try:
        engine.assess(
            input_id="input_004",
            content="test",
            source_id="terminal",
            timestamp="2026-10-05T10:00:00+00:00",
            confidence=1.5,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid confidence was not rejected")


if __name__ == "__main__":
    test_high_quality_input()
    test_missing_content_is_detected()
    test_invalid_timestamp_is_detected()
    test_security_boundary()
    test_invalid_confidence_is_rejected()
    print("SAHIBEX PHASE 1 #33 DATA QUALITY TEST: PASS")
