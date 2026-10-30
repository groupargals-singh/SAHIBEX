from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.research.aggregator import (
    ResearchResultAggregator,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)
from core.research.freshness import (
    STATUS_AGING,
    STATUS_FRESH,
    STATUS_INVALID,
    STATUS_STALE,
    STATUS_UNKNOWN,
)


REFERENCE_TIME = datetime(
    2026,
    1,
    1,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_source(
    source_id: str,
    published_at,
    *,
    accessed_at=None,
    reliability: float = 0.8,
) -> ResearchSource:
    if accessed_at is None:
        accessed_at = (
            published_at
            if published_at is not None
            else REFERENCE_TIME
        )

    return ResearchSource(
        source_id=source_id,
        title=f"Source {source_id}",
        source_type="web",
        locator=f"https://example.com/{source_id}",
        publisher="Example Publisher",
        published_at=published_at,
        accessed_at=accessed_at,
        reliability=reliability,
    )


def make_knowledge(
    knowledge_id: str,
) -> KnowledgeCandidate:
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=f"Statement {knowledge_id}",
        confidence=0.9,
        verified=True,
    )


def test_freshness_aggregator_integration() -> None:
    fresh_source = make_source(
        "source_fresh",
        REFERENCE_TIME - timedelta(hours=12),
    )

    aging_source = make_source(
        "source_aging",
        REFERENCE_TIME - timedelta(days=30),
    )

    stale_source = make_source(
        "source_stale",
        REFERENCE_TIME - timedelta(days=120),
    )

    unknown_source = make_source(
        "source_unknown",
        None,
    )

    invalid_source = make_source(
        "source_invalid",
        REFERENCE_TIME + timedelta(days=1),
        accessed_at=REFERENCE_TIME,
    )

    sources = [
        fresh_source,
        aging_source,
        stale_source,
        unknown_source,
        invalid_source,
    ]

    knowledge = [
        make_knowledge("knowledge_1"),
    ]

    evidence = [
        Evidence(
            evidence_id="evidence_1",
            finding_id="finding_1",
            source_id="source_fresh",
            evidence_text="Supporting evidence",
            supports=True,
            strength=0.9,
            metadata={
                "knowledge_id": "knowledge_1",
            },
        ),
    ]

    aggregator = ResearchResultAggregator()

    result = aggregator.aggregate(
        knowledge,
        verified_only=True,
        limit=10,
        evidence_items=evidence,
        sources=sources,
        reference_time=REFERENCE_TIME,
    )

    assessments = {
        item.source_id: item
        for item in result.freshness_assessments
    }

    assert len(assessments) == 5
    print("[PASS] freshness assessment count")

    assert (
        assessments["source_fresh"].status
        == STATUS_FRESH
    )
    print("[PASS] fresh source integration")

    assert (
        assessments["source_aging"].status
        == STATUS_AGING
    )
    print("[PASS] aging source integration")

    assert (
        assessments["source_stale"].status
        == STATUS_STALE
    )
    print("[PASS] stale source integration")

    assert (
        assessments["source_unknown"].status
        == STATUS_UNKNOWN
    )
    print("[PASS] unknown publication integration")

    assert (
        assessments["source_invalid"].status
        == STATUS_INVALID
    )
    print("[PASS] invalid timestamp integration")

    assert (
        assessments["source_fresh"].freshness_score
        == 1.0
    )
    print("[PASS] freshness score integration")

    assert (
        assessments["source_fresh"].reference_time
        == REFERENCE_TIME
    )
    print("[PASS] deterministic reference time")

    assert result.results
    assert result.results[0].knowledge_id == "knowledge_1"
    print("[PASS] aggregation selection unchanged")

    assert result.agreement_assessments
    print("[PASS] 6G-5 agreement remains available")

    assert result.conflict_intelligence == []
    print("[PASS] 6G-5 conflict intelligence remains available")

    assert fresh_source.published_at == (
        REFERENCE_TIME - timedelta(hours=12)
    )
    assert fresh_source.reliability == 0.8
    print("[PASS] source immutability")


def test_freshness_does_not_change_ranking() -> None:
    old_source = make_source(
        "source_old",
        REFERENCE_TIME - timedelta(days=120),
    )

    new_source = make_source(
        "source_new",
        REFERENCE_TIME - timedelta(hours=12),
    )

    knowledge = [
        make_knowledge("knowledge_a"),
        make_knowledge("knowledge_b"),
    ]

    evidence = [
        Evidence(
            evidence_id="evidence_a",
            finding_id="finding_a",
            source_id="source_old",
            evidence_text="Old source evidence",
            supports=True,
            strength=0.9,
            metadata={
                "knowledge_id": "knowledge_a",
            },
        ),
        Evidence(
            evidence_id="evidence_b",
            finding_id="finding_b",
            source_id="source_new",
            evidence_text="New source evidence",
            supports=True,
            strength=0.9,
            metadata={
                "knowledge_id": "knowledge_b",
            },
        ),
    ]

    aggregator = ResearchResultAggregator()

    result = aggregator.aggregate(
        knowledge,
        verified_only=True,
        limit=10,
        evidence_items=evidence,
        sources=[
            old_source,
            new_source,
        ],
        reference_time=REFERENCE_TIME,
    )

    selected_ids = [
        item.knowledge_id
        for item in result.results
    ]

    assert selected_ids == [
        "knowledge_a",
        "knowledge_b",
    ]

    print(
        "[PASS] freshness does not alter ranking"
    )


if __name__ == "__main__":
    print(
        "SAHIBEX 6G-6 FRESHNESS AGGREGATOR "
        "INTEGRATION TEST"
    )

    test_freshness_aggregator_integration()
    test_freshness_does_not_change_ranking()

    print(
        "SAHIBEX 6G-6 FRESHNESS AGGREGATOR "
        "INTEGRATION TEST: PASS"
    )
