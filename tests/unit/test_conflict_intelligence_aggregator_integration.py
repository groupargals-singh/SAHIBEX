from __future__ import annotations

from core.research.aggregator import ResearchResultAggregator
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


def make_knowledge(
    knowledge_id: str,
    statement: str,
    confidence: float = 0.8,
    verified: bool = True,
) -> KnowledgeCandidate:
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=[],
        evidence=[],
        confidence=confidence,
        verified=verified,
    )


def make_source(
    source_id: str,
    reliability: float,
) -> ResearchSource:
    return ResearchSource(
        source_id=source_id,
        title=f"Source {source_id}",
        source_type="web",
        locator=f"https://example.com/{source_id}",
        publisher="Test Publisher",
        reliability=reliability,
    )


def make_evidence(
    evidence_id: str,
    knowledge_id: str,
    source_id: str,
    strength: float,
    supports: bool = True,
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        finding_id=f"finding-{knowledge_id}",
        source_id=source_id,
        evidence_text=f"Evidence for {knowledge_id}",
        supports=supports,
        strength=strength,
        metadata={
            "knowledge_id": knowledge_id,
        },
    )


def test_conflict_intelligence_is_exposed() -> None:
    aggregator = ResearchResultAggregator()

    first = make_knowledge(
        "k1",
        "system is enabled",
        confidence=0.80,
    )

    second = make_knowledge(
        "k2",
        "system is disabled",
        confidence=0.70,
    )

    result = aggregator.aggregate(
        [first, second],
        evidence_items=[],
        sources=[],
    )

    assert len(result.conflict_ids) == 2
    assert len(result.conflict_intelligence) == 1

    assessment = result.conflict_intelligence[0]

    assert assessment.first_knowledge_id == "k1"
    assert assessment.second_knowledge_id == "k2"
    assert assessment.conflict_type == (
        "LEXICAL_CONTRADICTION"
    )


def test_evidence_resolution_metadata_matches_resolver() -> None:
    aggregator = ResearchResultAggregator()

    first = make_knowledge(
        "k1",
        "system is enabled",
        confidence=0.80,
    )

    second = make_knowledge(
        "k2",
        "system is disabled",
        confidence=0.70,
    )

    source = make_source(
        "source-1",
        reliability=0.80,
    )

    first_evidence = make_evidence(
        "e1",
        "k1",
        "source-1",
        strength=0.90,
        supports=True,
    )

    second_evidence = make_evidence(
        "e2",
        "k2",
        "source-1",
        strength=0.20,
        supports=True,
    )

    result = aggregator.aggregate(
        [first, second],
        evidence_items=[
            first_evidence,
            second_evidence,
        ],
        sources=[source],
    )

    assert len(result.conflict_intelligence) == 1

    assessment = result.conflict_intelligence[0]

    assert assessment.resolution_status == "RESOLVED"
    assert assessment.selected_knowledge_id == "k1"
    assert assessment.evidence_score_delta > 0
    assert assessment.resolution_reason == (
        "stronger supporting evidence"
    )


def test_source_reliability_resolution_metadata() -> None:
    aggregator = ResearchResultAggregator()

    first = make_knowledge(
        "k1",
        "system is enabled",
        confidence=0.80,
    )

    second = make_knowledge(
        "k2",
        "system is disabled",
        confidence=0.80,
    )

    source_one = make_source(
        "source-1",
        reliability=0.90,
    )

    source_two = make_source(
        "source-2",
        reliability=0.30,
    )

    first_evidence = make_evidence(
        "e1",
        "k1",
        "source-1",
        strength=0.50,
        supports=True,
    )

    second_evidence = make_evidence(
        "e2",
        "k2",
        "source-2",
        strength=0.50,
        supports=True,
    )

    result = aggregator.aggregate(
        [first, second],
        evidence_items=[
            first_evidence,
            second_evidence,
        ],
        sources=[
            source_one,
            source_two,
        ],
    )

    assessment = result.conflict_intelligence[0]

    assert assessment.resolution_status == "RESOLVED"
    assert assessment.selected_knowledge_id == "k1"
    assert assessment.source_reliability_delta > 0
    assert assessment.resolution_reason == (
        "higher source reliability"
    )


def test_confidence_resolution_metadata() -> None:
    aggregator = ResearchResultAggregator()

    first = make_knowledge(
        "k1",
        "system is enabled",
        confidence=0.90,
    )

    second = make_knowledge(
        "k2",
        "system is disabled",
        confidence=0.60,
    )

    result = aggregator.aggregate(
        [first, second],
        evidence_items=[],
        sources=[],
    )

    assessment = result.conflict_intelligence[0]

    assert assessment.resolution_status == "RESOLVED"
    assert assessment.selected_knowledge_id == "k1"
    assert assessment.knowledge_confidence_delta > 0
    assert assessment.resolution_reason == (
        "higher knowledge confidence"
    )


def test_unresolved_conflict_is_preserved() -> None:
    aggregator = ResearchResultAggregator()

    first = make_knowledge(
        "k1",
        "system is enabled",
        confidence=0.80,
    )

    second = make_knowledge(
        "k2",
        "system is disabled",
        confidence=0.80,
    )

    source_one = make_source(
        "source-1",
        reliability=0.80,
    )

    source_two = make_source(
        "source-2",
        reliability=0.80,
    )

    first_evidence = make_evidence(
        "e1",
        "k1",
        "source-1",
        strength=0.50,
        supports=True,
    )

    second_evidence = make_evidence(
        "e2",
        "k2",
        "source-2",
        strength=0.50,
        supports=True,
    )

    result = aggregator.aggregate(
        [first, second],
        evidence_items=[
            first_evidence,
            second_evidence,
        ],
        sources=[
            source_one,
            source_two,
        ],
    )

    assessment = result.conflict_intelligence[0]

    assert assessment.resolution_status == "UNRESOLVED"
    assert assessment.selected_knowledge_id is None
    assert assessment.resolution_reason == (
        "evidence, source reliability, and confidence are tied"
    )

    assert result.resolved_conflict_count == 0
    assert result.unresolved_conflict_count == 1


def test_agreement_remains_available_with_conflict_intelligence() -> None:
    aggregator = ResearchResultAggregator()

    first = make_knowledge(
        "k1",
        "system is enabled",
        confidence=0.80,
    )

    second = make_knowledge(
        "k2",
        "system is disabled",
        confidence=0.80,
    )

    source_one = make_source(
        "source-1",
        reliability=0.80,
    )

    source_two = make_source(
        "source-2",
        reliability=0.80,
    )

    first_evidence = make_evidence(
        "e1",
        "k1",
        "source-1",
        strength=0.70,
        supports=True,
    )

    second_evidence = make_evidence(
        "e2",
        "k2",
        "source-2",
        strength=0.70,
        supports=True,
    )

    result = aggregator.aggregate(
        [first, second],
        evidence_items=[
            first_evidence,
            second_evidence,
        ],
        sources=[
            source_one,
            source_two,
        ],
    )

    assert len(result.agreement_assessments) == 2
    assert len(result.conflict_intelligence) == 1
    assert len(result.conflict_ids) == 2


def test_conflict_intelligence_does_not_mutate_inputs() -> None:
    aggregator = ResearchResultAggregator()

    first = make_knowledge(
        "k1",
        "system is enabled",
        confidence=0.80,
    )

    second = make_knowledge(
        "k2",
        "system is disabled",
        confidence=0.70,
    )

    source = make_source(
        "source-1",
        reliability=0.80,
    )

    evidence_one = make_evidence(
        "e1",
        "k1",
        "source-1",
        strength=0.90,
        supports=True,
    )

    evidence_two = make_evidence(
        "e2",
        "k2",
        "source-1",
        strength=0.20,
        supports=True,
    )

    original_first_confidence = first.confidence
    original_second_confidence = second.confidence
    original_evidence_one_strength = evidence_one.strength
    original_evidence_two_strength = evidence_two.strength
    original_source_reliability = source.reliability

    aggregator.aggregate(
        [first, second],
        evidence_items=[
            evidence_one,
            evidence_two,
        ],
        sources=[source],
    )

    assert first.confidence == original_first_confidence
    assert second.confidence == original_second_confidence
    assert evidence_one.strength == (
        original_evidence_one_strength
    )
    assert evidence_two.strength == (
        original_evidence_two_strength
    )
    assert source.reliability == (
        original_source_reliability
    )


def main() -> None:
    print(
        "SAHIBEX 6G-5 CONFLICT INTELLIGENCE "
        "AGGREGATOR INTEGRATION TEST"
    )

    tests = [
        (
            "conflict intelligence is exposed",
            test_conflict_intelligence_is_exposed,
        ),
        (
            "evidence resolution metadata",
            test_evidence_resolution_metadata_matches_resolver,
        ),
        (
            "source reliability resolution metadata",
            test_source_reliability_resolution_metadata,
        ),
        (
            "confidence resolution metadata",
            test_confidence_resolution_metadata,
        ),
        (
            "unresolved conflict protection",
            test_unresolved_conflict_is_preserved,
        ),
        (
            "agreement remains available",
            test_agreement_remains_available_with_conflict_intelligence,
        ),
        (
            "input immutability",
            test_conflict_intelligence_does_not_mutate_inputs,
        ),
    ]

    for name, test in tests:
        test()
        print(f"[PASS] {name}")

    print(
        "SAHIBEX 6G-5 CONFLICT INTELLIGENCE "
        "AGGREGATOR INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
