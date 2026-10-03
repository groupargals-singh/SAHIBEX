from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.research.freshness import (
    STATUS_AGING,
    STATUS_FRESH,
    STATUS_INVALID,
    STATUS_STALE,
    STATUS_UNKNOWN,
    assess_source_freshness,
)
from core.research.models import ResearchSource


UTC = timezone.utc


def make_source(
    source_id: str,
    published_at=None,
    accessed_at=None,
    reliability: float = 0.8,
) -> ResearchSource:
    return ResearchSource(
        source_id=source_id,
        title=f"Source {source_id}",
        source_type="web",
        locator=f"https://example.com/{source_id}",
        publisher="Test Publisher",
        published_at=published_at,
        accessed_at=(
            accessed_at
            if accessed_at is not None
            else datetime.now(UTC)
        ),
        reliability=reliability,
    )


def test_fresh_source() -> None:
    reference = datetime(
        2026,
        1,
        10,
        tzinfo=UTC,
    )

    source = make_source(
        "fresh",
        published_at=reference - timedelta(hours=12),
        accessed_at=reference - timedelta(hours=1),
    )

    result = assess_source_freshness(
        source,
        reference_time=reference,
    )

    assert result.status == STATUS_FRESH
    assert result.freshness_score == 1.0
    assert result.age_seconds == 43200.0


def test_aging_source() -> None:
    reference = datetime(
        2026,
        1,
        31,
        tzinfo=UTC,
    )

    source = make_source(
        "aging",
        published_at=reference - timedelta(days=30),
        accessed_at=reference - timedelta(days=1),
    )

    result = assess_source_freshness(
        source,
        reference_time=reference,
    )

    assert result.status == STATUS_AGING
    assert 0.49 <= result.freshness_score <= 0.51


def test_stale_source() -> None:
    reference = datetime(
        2026,
        6,
        1,
        tzinfo=UTC,
    )

    source = make_source(
        "stale",
        published_at=reference - timedelta(days=120),
        accessed_at=reference - timedelta(days=1),
    )

    result = assess_source_freshness(
        source,
        reference_time=reference,
    )

    assert result.status == STATUS_STALE
    assert 0.0 <= result.freshness_score < 0.20


def test_unknown_publication_time() -> None:
    reference = datetime(
        2026,
        1,
        10,
        tzinfo=UTC,
    )

    source = make_source(
        "unknown",
        published_at=None,
        accessed_at=reference,
    )

    result = assess_source_freshness(
        source,
        reference_time=reference,
    )

    assert result.status == STATUS_UNKNOWN
    assert result.freshness_score == 0.0
    assert result.age_seconds is None


def test_future_publication_is_invalid() -> None:
    reference = datetime(
        2026,
        1,
        10,
        tzinfo=UTC,
    )

    source = make_source(
        "future",
        published_at=reference + timedelta(days=1),
        accessed_at=reference,
    )

    result = assess_source_freshness(
        source,
        reference_time=reference,
    )

    assert result.status == STATUS_INVALID
    assert result.freshness_score == 0.0
    assert result.age_seconds is None


def test_publication_after_access_is_invalid() -> None:
    reference = datetime(
        2026,
        1,
        10,
        tzinfo=UTC,
    )

    source = make_source(
        "invalid-order",
        published_at=reference,
        accessed_at=reference - timedelta(days=1),
    )

    result = assess_source_freshness(
        source,
        reference_time=reference,
    )

    assert result.status == STATUS_INVALID
    assert result.publication_before_access is False
    assert result.freshness_score == 0.0


def test_timezone_aware_requirement() -> None:
    reference = datetime(
        2026,
        1,
        10,
        tzinfo=UTC,
    )

    source = make_source(
        "naive",
        published_at=datetime(2026, 1, 1),
        accessed_at=reference,
    )

    try:
        assess_source_freshness(
            source,
            reference_time=reference,
        )
    except ValueError as exc:
        assert "timezone-aware" in str(exc)
    else:
        raise AssertionError(
            "naive publication timestamp must be rejected"
        )


def test_naive_reference_time_is_rejected() -> None:
    source = make_source(
        "naive-reference",
        published_at=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
        accessed_at=datetime(
            2026,
            1,
            2,
            tzinfo=UTC,
        ),
    )

    try:
        assess_source_freshness(
            source,
            reference_time=datetime(
                2026,
                1,
                10,
            ),
        )
    except ValueError as exc:
        assert "timezone-aware" in str(exc)
    else:
        raise AssertionError(
            "naive reference time must be rejected"
        )


def test_reliability_does_not_change_freshness() -> None:
    reference = datetime(
        2026,
        1,
        10,
        tzinfo=UTC,
    )

    low_reliability = make_source(
        "low",
        published_at=reference - timedelta(days=3),
        accessed_at=reference,
        reliability=0.1,
    )

    high_reliability = make_source(
        "high",
        published_at=reference - timedelta(days=3),
        accessed_at=reference,
        reliability=0.9,
    )

    first = assess_source_freshness(
        low_reliability,
        reference_time=reference,
    )

    second = assess_source_freshness(
        high_reliability,
        reference_time=reference,
    )

    assert first.freshness_score == (
        second.freshness_score
    )

    assert first.status == second.status


def test_assessment_does_not_mutate_source() -> None:
    reference = datetime(
        2026,
        1,
        10,
        tzinfo=UTC,
    )

    published_at = (
        reference - timedelta(days=3)
    )

    accessed_at = (
        reference - timedelta(days=1)
    )

    source = make_source(
        "immutable",
        published_at=published_at,
        accessed_at=accessed_at,
        reliability=0.75,
    )

    before_published = source.published_at
    before_accessed = source.accessed_at
    before_reliability = source.reliability
    before_metadata = dict(source.metadata)

    assess_source_freshness(
        source,
        reference_time=reference,
    )

    assert source.published_at == before_published
    assert source.accessed_at == before_accessed
    assert source.reliability == before_reliability
    assert source.metadata == before_metadata


def main() -> None:
    print(
        "SAHIBEX 6G-6 TIMESTAMP / "
        "FRESHNESS MODEL TEST"
    )

    tests = [
        (
            "fresh source",
            test_fresh_source,
        ),
        (
            "aging source",
            test_aging_source,
        ),
        (
            "stale source",
            test_stale_source,
        ),
        (
            "unknown publication time",
            test_unknown_publication_time,
        ),
        (
            "future publication protection",
            test_future_publication_is_invalid,
        ),
        (
            "publication/access ordering protection",
            test_publication_after_access_is_invalid,
        ),
        (
            "timezone-aware timestamp protection",
            test_timezone_aware_requirement,
        ),
        (
            "naive reference protection",
            test_naive_reference_time_is_rejected,
        ),
        (
            "reliability separation",
            test_reliability_does_not_change_freshness,
        ),
        (
            "source immutability",
            test_assessment_does_not_mutate_source,
        ),
    ]

    for name, test in tests:
        test()
        print(f"[PASS] {name}")

    print(
        "SAHIBEX 6G-6 TIMESTAMP / "
        "FRESHNESS MODEL TEST: PASS"
    )


if __name__ == "__main__":
    main()
