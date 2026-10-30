from datetime import datetime, timezone

from core.research.agreement import (
    AGREEMENT_VERSION,
    assess_multi_source_agreement,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


def knowledge(knowledge_id: str = "k1") -> KnowledgeCandidate:
    now = datetime.now(timezone.utc)
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement="the system is safe",
        findings=["finding-1"],
        evidence=[],
        confidence=0.90,
        verified=True,
        created_at=now,
        last_verified_at=now,
        metadata={},
    )


def evidence(
    evidence_id: str,
    knowledge_id: str = "k1",
    source_id: str = "source-a",
    supports: bool = True,
) -> Evidence:
    now = datetime.now(timezone.utc)
    return Evidence(
        evidence_id=evidence_id,
        finding_id="finding-1",
        source_id=source_id,
        evidence_text="the system is safe",
        supports=supports,
        strength=0.80,
        created_at=now,
        metadata={"knowledge_id": knowledge_id},
    )


def source(source_id: str) -> ResearchSource:
    return ResearchSource(
        source_id=source_id,
        title=source_id,
        source_type="test",
        locator=f"https://{source_id}.example.com/{source_id}",
        publisher=f"Publisher {source_id}",
        author=None,
        reliability=0.80,
    )


def main() -> None:
    item = knowledge()

    # 1. No evidence / no source
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[],
        sources=[],
    )
    assert result.knowledge_id == "k1"
    assert result.total_source_count == 0
    assert result.supporting_source_count == 0
    assert result.contradicting_source_count == 0
    assert result.agreement_score == 0.0
    assert result.version == AGREEMENT_VERSION
    print("[PASS] no-source agreement")

    # 2. One source cannot establish multi-source agreement
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[evidence("e1", source_id="source-a")],
        sources=[source("source-a")],
    )
    assert result.total_source_count == 1
    assert result.supporting_source_count == 1
    assert result.agreement_score == 0.0
    print("[PASS] single-source agreement")

    # 3. Two distinct supporting sources agree
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e1", source_id="source-a"),
            evidence("e2", source_id="source-b"),
        ],
        sources=[source("source-a"), source("source-b")],
    )
    assert result.total_source_count == 2
    assert result.supporting_source_count == 2
    assert result.contradicting_source_count == 0
    assert result.agreement_score == 1.0
    print("[PASS] two-source agreement")

    # 4. Three distinct supporting sources agree
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e1", source_id="source-a"),
            evidence("e2", source_id="source-b"),
            evidence("e3", source_id="source-c"),
        ],
        sources=[
            source("source-a"),
            source("source-b"),
            source("source-c"),
        ],
    )
    assert result.total_source_count == 3
    assert result.supporting_source_count == 3
    assert result.contradicting_source_count == 0
    assert result.agreement_score == 1.0
    print("[PASS] three-source agreement")

    # 5. Multiple evidences from the same source count once
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e1", source_id="source-a"),
            evidence("e2", source_id="source-a"),
            evidence("e3", source_id="source-b"),
        ],
        sources=[source("source-a"), source("source-b")],
    )
    assert result.total_source_count == 2
    assert result.supporting_source_count == 2
    assert result.agreement_score == 1.0
    print("[PASS] duplicate evidence from same source")

    # 6. Supporting and contradicting sources remain separate
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e1", source_id="source-a", supports=True),
            evidence("e2", source_id="source-b", supports=True),
            evidence("e3", source_id="source-c", supports=False),
        ],
        sources=[
            source("source-a"),
            source("source-b"),
            source("source-c"),
        ],
    )
    assert result.total_source_count == 3
    assert result.supporting_source_count == 2
    assert result.contradicting_source_count == 1
    assert result.agreement_score == 0.5
    print("[PASS] supporting and contradicting sources")

    # 7. Evidence for another knowledge candidate is ignored
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e1", knowledge_id="k2", source_id="source-a"),
            evidence("e2", knowledge_id="k2", source_id="source-b"),
        ],
        sources=[source("source-a"), source("source-b")],
    )
    assert result.total_source_count == 0
    assert result.supporting_source_count == 0
    assert result.agreement_score == 0.0
    print("[PASS] unrelated knowledge evidence ignored")

    # 8. Source reliability does not affect agreement
    low_reliability_source = ResearchSource(
        source_id="source-low",
        title="source-low",
        source_type="test",
        locator="https://publisher-low.example.com/source-low",
        publisher="Publisher Low",
        author=None,
        reliability=0.10,
    )
    high_reliability_source = ResearchSource(
        source_id="source-high",
        title="source-high",
        source_type="test",
        locator="https://publisher-high.example.com/source-high",
        publisher="Publisher High",
        author=None,
        reliability=1.00,
    )
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e1", source_id="source-low"),
            evidence("e2", source_id="source-high"),
        ],
        sources=[low_reliability_source, high_reliability_source],
    )
    assert result.total_source_count == 2
    assert result.supporting_source_count == 2
    assert result.agreement_score == 1.0
    print("[PASS] reliability separated from agreement")

    # 9. Unknown evidence source is excluded
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e-unknown", source_id="unregistered-source"),
        ],
        sources=[source("source-a")],
    )
    assert result.total_source_count == 0
    assert result.supporting_source_count == 0
    assert result.agreement_score == 0.0
    print("[PASS] unknown source excluded")

    # 10. Missing publisher and unusable hostname are excluded
    unidentified = ResearchSource(
        source_id="unidentified",
        title="Unidentified source",
        source_type="test",
        locator="not-a-valid-web-url",
        publisher="",
        author=None,
        reliability=0.80,
    )
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e-unidentified", source_id="unidentified"),
        ],
        sources=[unidentified],
    )
    assert result.total_source_count == 0
    assert result.supporting_source_count == 0
    assert result.agreement_score == 0.0
    print("[PASS] unidentifiable source excluded")

    # 11. Same publisher across different domains counts once
    shared_publisher_a = ResearchSource(
        source_id="shared-publisher-a",
        title="Publisher A page",
        source_type="test",
        locator="https://alpha.example.com/story",
        publisher="Shared Publisher",
        author=None,
        reliability=0.80,
    )
    shared_publisher_b = ResearchSource(
        source_id="shared-publisher-b",
        title="Publisher B page",
        source_type="test",
        locator="https://beta.example.com/story",
        publisher="Shared Publisher",
        author=None,
        reliability=0.80,
    )
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e-shared-a", source_id="shared-publisher-a"),
            evidence("e-shared-b", source_id="shared-publisher-b"),
        ],
        sources=[shared_publisher_a, shared_publisher_b],
    )
    assert result.total_source_count == 1
    assert result.supporting_source_count == 1
    assert result.agreement_score == 0.0
    print("[PASS] shared publisher counted once")

    # 12. Same hostname across different publisher labels counts once
    shared_domain_a = ResearchSource(
        source_id="shared-domain-a",
        title="Domain page A",
        source_type="test",
        locator="https://same.example.com/story-a",
        publisher="Publisher Label A",
        author=None,
        reliability=0.80,
    )
    shared_domain_b = ResearchSource(
        source_id="shared-domain-b",
        title="Domain page B",
        source_type="test",
        locator="https://same.example.com/story-b",
        publisher="Publisher Label B",
        author=None,
        reliability=0.80,
    )
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e-domain-a", source_id="shared-domain-a"),
            evidence("e-domain-b", source_id="shared-domain-b"),
        ],
        sources=[shared_domain_a, shared_domain_b],
    )
    assert result.total_source_count == 1
    assert result.supporting_source_count == 1
    assert result.agreement_score == 0.0
    print("[PASS] shared hostname counted once")

    # 13. Empty source registry excludes all evidence
    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e-empty-registry-a", source_id="source-a"),
            evidence("e-empty-registry-b", source_id="source-b"),
        ],
        sources=[],
    )
    assert result.total_source_count == 0
    assert result.supporting_source_count == 0
    assert result.contradicting_source_count == 0
    assert result.agreement_score == 0.0
    print("[PASS] empty source registry excludes evidence")

    # 14. Wrong knowledge type is rejected
    try:
        assess_multi_source_agreement(
            knowledge="not-knowledge",
            evidence_items=[],
            sources=[],
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "expected TypeError for invalid knowledge"
        )
    print("[PASS] invalid knowledge protection")

    # 15. Aggregator-only hosts cannot establish independent corroboration
    aggregator_sources = [
        ResearchSource(
            source_id="google-news",
            title="Google News result",
            source_type="test",
            locator="https://news.google.com/articles/example",
            publisher="",
            reliability=0.80,
        ),
        ResearchSource(
            source_id="yahoo-news",
            title="Yahoo News result",
            source_type="test",
            locator="https://news.yahoo.com/example",
            publisher="",
            reliability=0.80,
        ),
    ]

    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e-google-news", source_id="google-news"),
            evidence("e-yahoo-news", source_id="yahoo-news"),
        ],
        sources=aggregator_sources,
    )

    assert result.total_source_count == 0
    assert result.supporting_source_count == 0
    assert result.agreement_score == 0.0
    print("[PASS] aggregator-only sources excluded")

    # 16. www prefix and trailing hostname dot normalize to one domain
    normalized_sources = [
        ResearchSource(
            source_id="normalized-a",
            title="Domain variant A",
            source_type="test",
            locator="https://www.example.com/story-a",
            publisher="",
            reliability=0.80,
        ),
        ResearchSource(
            source_id="normalized-b",
            title="Domain variant B",
            source_type="test",
            locator="https://example.com./story-b",
            publisher="",
            reliability=0.80,
        ),
    ]

    result = assess_multi_source_agreement(
        knowledge=item,
        evidence_items=[
            evidence("e-normalized-a", source_id="normalized-a"),
            evidence("e-normalized-b", source_id="normalized-b"),
        ],
        sources=normalized_sources,
    )

    assert result.total_source_count == 1
    assert result.supporting_source_count == 1
    assert result.agreement_score == 0.0
    print("[PASS] normalized hostname variants counted once")
    print("SAHIBEX MULTI-SOURCE AGREEMENT TEST: PASS")


if __name__ == "__main__":
    main()
