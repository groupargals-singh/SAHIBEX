from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone

from core.research.aggregator import (
    ResearchResultAggregator,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


def _build_fixture():
    now = datetime.now(timezone.utc)

    sources = [
        ResearchSource(
            source_id="source_a",
            title="Source A",
            source_type="document",
            locator="https://example.com/a",
            publisher="Publisher A",
            published_at=now - timedelta(hours=2),
            reliability=0.95,
            metadata={
                "provider": "test",
                "provider_name": "test",
                "content_type": "document",
                "acquired_at": now.isoformat(),
                "content_hash": "hash-a",
                "content_bytes": 1000,
                "discovery_only": False,
                "content_is_full_document": True,
                "reliability_source": "provider",
                "reliability_version": "6G-1",
            },
        ),
        ResearchSource(
            source_id="source_b",
            title="Source B",
            source_type="web",
            locator="https://example.com/b",
            publisher="Publisher B",
            published_at=now - timedelta(days=5),
            reliability=0.60,
            metadata={
                "provider": "test",
                "provider_name": "test",
                "content_type": "web",
                "acquired_at": now.isoformat(),
                "content_hash": "hash-b",
                "content_bytes": 800,
                "discovery_only": False,
                "content_is_full_document": True,
                "reliability_source": "provider",
                "reliability_version": "6G-1",
            },
        ),
    ]

    knowledge_a = KnowledgeCandidate(
        knowledge_id="knowledge_a",
        statement="The system supports feature A.",
        findings=["finding_a"],
        confidence=0.90,
        verified=True,
    )

    knowledge_b = KnowledgeCandidate(
        knowledge_id="knowledge_b",
        statement="The system supports feature B.",
        findings=["finding_b"],
        confidence=0.60,
        verified=True,
    )

    evidence_a = Evidence(
        evidence_id="evidence_a",
        finding_id="finding_a",
        source_id="source_a",
        evidence_text=(
            "The system supports feature A."
        ),
        supports=True,
        strength=0.90,
        metadata={
            "knowledge_id": "knowledge_a",
            "evidence_strength": {
                "strength_score": 0.90,
                "directness_score": 0.90,
                "specificity_score": 0.90,
                "finding_linkage_score": 0.90,
                "source_linkage_score": 0.90,
                "extraction_confidence_score": 0.90,
                "version": "6G-3",
            },
        },
    )

    evidence_b = Evidence(
        evidence_id="evidence_b",
        finding_id="finding_b",
        source_id="source_b",
        evidence_text=(
            "The system supports feature B."
        ),
        supports=True,
        strength=0.60,
        metadata={
            "knowledge_id": "knowledge_b",
            "evidence_strength": {
                "strength_score": 0.60,
                "directness_score": 0.60,
                "specificity_score": 0.60,
                "finding_linkage_score": 0.60,
                "source_linkage_score": 0.60,
                "extraction_confidence_score": 0.60,
                "version": "6G-3",
            },
        },
    )

    return (
        now,
        sources,
        [knowledge_a, knowledge_b],
        [evidence_a, evidence_b],
    )


def test_source_ranking_is_exposed() -> None:
    now, sources, knowledge, evidence = (
        _build_fixture()
    )

    result = ResearchResultAggregator().aggregate(
        knowledge,
        verified_only=False,
        evidence_items=evidence,
        sources=sources,
        reference_time=now,
    )

    assert len(
        result.source_ranking_assessments
    ) == 2

    assert (
        result.source_ranking_assessments[0]
        .rank
        == 1
    )

    assert (
        result.source_ranking_assessments[1]
        .rank
        == 2
    )


def test_source_ranking_is_deterministic() -> None:
    now, sources, knowledge, evidence = (
        _build_fixture()
    )

    aggregator = ResearchResultAggregator()

    first = aggregator.aggregate(
        knowledge,
        verified_only=False,
        evidence_items=evidence,
        sources=sources,
        reference_time=now,
    )

    second = aggregator.aggregate(
        knowledge,
        verified_only=False,
        evidence_items=evidence,
        sources=sources,
        reference_time=now,
    )

    assert (
        first.source_ranking_assessments
        == second.source_ranking_assessments
    )


def test_source_a_is_ranked_above_source_b() -> None:
    now, sources, knowledge, evidence = (
        _build_fixture()
    )

    result = ResearchResultAggregator().aggregate(
        knowledge,
        verified_only=False,
        evidence_items=evidence,
        sources=sources,
        reference_time=now,
    )

    rankings = (
        result.source_ranking_assessments
    )

    assert rankings[0].source_id == "source_a"
    assert rankings[1].source_id == "source_b"

    assert (
        rankings[0].ranking_score
        > rankings[1].ranking_score
    )


def test_source_knowledge_mapping_is_correct() -> None:
    now, sources, knowledge, evidence = (
        _build_fixture()
    )

    aggregator = ResearchResultAggregator()

    mapping = (
        aggregator._source_knowledge_map(
            knowledge_items=knowledge,
            evidence_items=evidence,
            sources=sources,
        )
    )

    assert mapping == {
        "source_a": ["knowledge_a"],
        "source_b": ["knowledge_b"],
    }


def test_6g7_confidence_remains_available() -> None:
    now, sources, knowledge, evidence = (
        _build_fixture()
    )

    result = ResearchResultAggregator().aggregate(
        knowledge,
        verified_only=False,
        evidence_items=evidence,
        sources=sources,
        reference_time=now,
    )

    assert len(
        result.confidence_assessments
    ) == 2

    knowledge_ids = {
        item.knowledge_id
        for item in result.confidence_assessments
    }

    assert knowledge_ids == {
        "knowledge_a",
        "knowledge_b",
    }


def test_existing_knowledge_selection_is_unchanged() -> None:
    now, sources, knowledge, evidence = (
        _build_fixture()
    )

    result = ResearchResultAggregator().aggregate(
        knowledge,
        verified_only=False,
        limit=2,
        evidence_items=evidence,
        sources=sources,
        reference_time=now,
    )

    selected_ids = [
        item.knowledge_id
        for item in result.results
    ]

    assert selected_ids == [
        "knowledge_a",
        "knowledge_b",
    ]


def test_input_objects_are_not_mutated() -> None:
    now, sources, knowledge, evidence = (
        _build_fixture()
    )

    sources_before = deepcopy(sources)
    knowledge_before = deepcopy(knowledge)
    evidence_before = deepcopy(evidence)

    ResearchResultAggregator().aggregate(
        knowledge,
        verified_only=False,
        evidence_items=evidence,
        sources=sources,
        reference_time=now,
    )

    assert sources == sources_before
    assert knowledge == knowledge_before
    assert evidence == evidence_before


def test_previous_intelligence_layers_remain_available() -> None:
    now, sources, knowledge, evidence = (
        _build_fixture()
    )

    result = ResearchResultAggregator().aggregate(
        knowledge,
        verified_only=False,
        evidence_items=evidence,
        sources=sources,
        reference_time=now,
    )

    assert len(
        result.agreement_assessments
    ) == 2

    assert (
        len(result.freshness_assessments)
        == 2
    )

    assert (
        len(result.confidence_assessments)
        == 2
    )

    assert (
        len(result.source_ranking_assessments)
        == 2
    )


def main() -> None:
    print(
        "SAHIBEX 6G-8 SOURCE RANKING "
        "AGGREGATOR INTEGRATION TEST"
    )

    tests = [
        (
            "source ranking is exposed",
            test_source_ranking_is_exposed,
        ),
        (
            "source ranking is deterministic",
            test_source_ranking_is_deterministic,
        ),
        (
            "source A ranked above source B",
            test_source_a_is_ranked_above_source_b,
        ),
        (
            "source knowledge mapping is correct",
            test_source_knowledge_mapping_is_correct,
        ),
        (
            "6G-7 confidence remains available",
            test_6g7_confidence_remains_available,
        ),
        (
            "existing knowledge selection is unchanged",
            test_existing_knowledge_selection_is_unchanged,
        ),
        (
            "input objects are not mutated",
            test_input_objects_are_not_mutated,
        ),
        (
            "previous intelligence layers remain available",
            test_previous_intelligence_layers_remain_available,
        ),
    ]

    for name, test in tests:
        test()
        print(f"[PASS] {name}")

    print(
        "SAHIBEX 6G-8 SOURCE RANKING "
        "AGGREGATOR INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
