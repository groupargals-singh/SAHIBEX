from datetime import datetime, timezone

from core.research.aggregator import ResearchResultAggregator
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


def knowledge(
    knowledge_id: str,
    statement: str,
    confidence: float = 0.8,
    verified: bool = True,
) -> KnowledgeCandidate:
    now = datetime.now(timezone.utc)

    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=[],
        evidence=[],
        confidence=confidence,
        verified=verified,
        created_at=now,
        last_verified_at=now if verified else None,
        metadata={},
    )


def source(
    source_id: str,
    reliability: float,
) -> ResearchSource:
    now = datetime.now(timezone.utc)

    return ResearchSource(
        source_id=source_id,
        title=source_id,
        source_type="test",
        locator=f"https://example.com/{source_id}",
        publisher="test",
        author=None,
        published_at=None,
        accessed_at=now,
        reliability=reliability,
        metadata={},
    )


def evidence(
    evidence_id: str,
    knowledge_id: str,
    source_id: str,
    strength: float,
) -> Evidence:
    now = datetime.now(timezone.utc)

    return Evidence(
        evidence_id=evidence_id,
        finding_id="finding-" + evidence_id,
        source_id=source_id,
        evidence_text="test evidence",
        supports=True,
        strength=strength,
        created_at=now,
        metadata={
            "knowledge_id": knowledge_id,
        },
    )


def main() -> None:
    aggregator = ResearchResultAggregator()

    safe = knowledge(
        "k1",
        "the system is safe",
        confidence=0.80,
    )

    unsafe = knowledge(
        "k2",
        "the system is unsafe",
        confidence=0.80,
    )

    unrelated = knowledge(
        "k3",
        "the system uses Python",
        confidence=0.85,
    )

    # ---------------------------------------------------------
    # 1. Resolved conflict
    # ---------------------------------------------------------
    result = aggregator.aggregate(
        [safe, unsafe, unrelated],
        evidence_items=[
            evidence(
                "e1",
                "k1",
                "source-a",
                0.90,
            ),
            evidence(
                "e2",
                "k2",
                "source-b",
                0.20,
            ),
        ],
        sources=[
            source("source-a", 0.80),
            source("source-b", 0.80),
        ],
    )

    assert result.status == "CONFLICT_RESOLVED"
    assert result.conflict_count == 1
    assert result.resolved_conflict_count == 1
    assert result.unresolved_conflict_count == 0
    assert result.resolved_knowledge_ids == ["k1"]

    result_ids = {
        item.knowledge_id
        for item in result.results
    }

    assert "k1" in result_ids
    assert "k2" not in result_ids
    assert "k3" in result_ids

    print("[PASS] resolved conflict aggregation")

    # ---------------------------------------------------------
    # 2. Unresolved conflict
    # ---------------------------------------------------------
    tied_a = knowledge(
        "k4",
        "the system is safe",
        confidence=0.80,
    )

    tied_b = knowledge(
        "k5",
        "the system is unsafe",
        confidence=0.80,
    )

    result = aggregator.aggregate(
        [tied_a, tied_b],
    )

    assert result.status == "CONFLICT_UNRESOLVED"
    assert result.conflict_count == 1
    assert result.resolved_conflict_count == 0
    assert result.unresolved_conflict_count == 1
    assert result.results == []

    print("[PASS] unresolved conflict protection")

    # ---------------------------------------------------------
    # 3. Mixed resolved + unresolved conflicts
    # ---------------------------------------------------------
    safe_2 = knowledge(
        "k6",
        "the system is safe",
        confidence=0.90,
    )

    unsafe_2 = knowledge(
        "k7",
        "the system is unsafe",
        confidence=0.90,
    )

    active = knowledge(
        "k8",
        "the service is active",
        confidence=0.80,
    )

    inactive = knowledge(
        "k9",
        "the service is inactive",
        confidence=0.80,
    )

    result = aggregator.aggregate(
        [safe_2, unsafe_2, active, inactive],
        evidence_items=[
            evidence(
                "e6",
                "k6",
                "source-good",
                0.90,
            ),
            evidence(
                "e7",
                "k7",
                "source-weak",
                0.20,
            ),
        ],
        sources=[
            source("source-good", 0.90),
            source("source-weak", 0.30),
        ],
    )

    assert result.status == "PARTIALLY_RESOLVED"
    assert result.resolved_conflict_count == 1
    assert result.unresolved_conflict_count == 1
    assert result.resolved_knowledge_ids == ["k6"]

    result_ids = {
        item.knowledge_id
        for item in result.results
    }

    assert "k6" in result_ids
    assert "k7" not in result_ids
    assert "k8" not in result_ids
    assert "k9" not in result_ids

    print("[PASS] mixed resolution handling")

    # ---------------------------------------------------------
    # 4. No conflict remains normal
    # ---------------------------------------------------------
    result = aggregator.aggregate(
        [unrelated],
    )

    assert result.status == "VERIFIED"
    assert result.conflict_count == 0
    assert result.resolved_conflict_count == 0
    assert result.unresolved_conflict_count == 0
    assert len(result.results) == 1

    print("[PASS] normal aggregation preserved")

    # ---------------------------------------------------------
    # 5. Conflict metadata is preserved
    # ---------------------------------------------------------
    assert result.conflict_ids == []

    result = aggregator.aggregate(
        [safe, unsafe],
        evidence_items=[
            evidence(
                "e8",
                "k1",
                "source-a",
                0.90,
            ),
            evidence(
                "e9",
                "k2",
                "source-b",
                0.20,
            ),
        ],
        sources=[
            source("source-a", 0.80),
            source("source-b", 0.80),
        ],
    )

    assert result.conflict_ids == ["k1", "k2"]
    assert result.resolved_knowledge_ids == ["k1"]

    print("[PASS] conflict metadata preserved")

    # ---------------------------------------------------------
    # 6. Limit remains enforced
    # ---------------------------------------------------------
    a = knowledge(
        "k10",
        "system uses Python",
        confidence=0.90,
    )

    b = knowledge(
        "k11",
        "system uses SQLite",
        confidence=0.80,
    )

    result = aggregator.aggregate(
        [a, b],
        limit=1,
    )

    assert len(result.results) == 1
    assert result.results[0].knowledge_id == "k10"

    print("[PASS] result limit preserved")

    print(
        "SAHIBEX RESOLUTION-AWARE AGGREGATOR TEST: PASS"
    )


if __name__ == "__main__":
    main()
