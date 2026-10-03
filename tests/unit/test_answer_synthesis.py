from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone

from core.research.answer_synthesis import (
    CONFLICTED,
    MULTI_SOURCE_SUPPORTED,
    SUPPORTED,
    UNCERTAIN,
    QualityAwareAnswerSynthesizer,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchFinding,
    ResearchSource,
)


def _source(
    source_id: str,
    source_type: str = "document",
) -> ResearchSource:
    return ResearchSource(
        source_id=source_id,
        title=f"Source {source_id}",
        source_type=source_type,
        locator=f"https://example.com/{source_id}",
        publisher="Example Publisher",
        author="Example Author",
        published_at=datetime.now(
            timezone.utc
        ),
        reliability=0.90,
        metadata={
            "provider": "test",
            "content_type": "text",
            "reliability_source": "provider",
            "reliability_version": "6G-1",
            "acquired_at": "2026-01-01T00:00:00+00:00",
            "content_hash": "abc123",
            "content_bytes": 100,
            "discovery_only": False,
            "content_is_full_document": True,
        },
    )


def _knowledge(
    knowledge_id: str,
    statement: str,
    evidence_ids: list[str],
    *,
    verified: bool = True,
    confidence: float = 0.90,
) -> KnowledgeCandidate:
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=["finding_1"],
        evidence=evidence_ids,
        confidence=confidence,
        verified=verified,
    )


def _evidence(
    evidence_id: str,
    source_id: str,
    knowledge_id: str,
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        finding_id="finding_1",
        source_id=source_id,
        evidence_text=f"Evidence for {knowledge_id}",
        supports=True,
        strength=0.90,
        metadata={
            "knowledge_id": knowledge_id,
            "evidence_strength": {
                "strength_score": 0.90,
                "version": "6G-3",
            },
        },
    )


def _confidence(
    knowledge_id: str,
    score: float,
):
    class Confidence:
        pass

    item = Confidence()
    item.knowledge_id = knowledge_id
    item.confidence_score = score
    return item


def _agreement(
    knowledge_id: str,
    score: float,
):
    class Agreement:
        pass

    item = Agreement()
    item.knowledge_id = knowledge_id
    item.agreement_score = score
    return item


def _freshness(
    source_id: str,
    score: float,
):
    class Freshness:
        pass

    item = Freshness()
    item.source_id = source_id
    item.freshness_score = score
    return item


def _ranking(
    source_id: str,
    score: float,
):
    class Ranking:
        pass

    item = Ranking()
    item.source_id = source_id
    item.ranking_score = score
    return item


def test_single_source_supported_claim():
    knowledge = _knowledge(
        "k1",
        "The system supports evidence-aware answers.",
        ["e1"],
    )

    evidence = [
        _evidence(
            "e1",
            "s1",
            "k1",
        )
    ]

    sources = [
        _source("s1")
    ]

    synthesizer = (
        QualityAwareAnswerSynthesizer()
    )

    result = synthesizer.synthesize(
        knowledge_items=[knowledge],
        evidence_items=evidence,
        sources=sources,
        confidence_assessments=[
            _confidence("k1", 0.90)
        ],
        freshness_assessments=[
            _freshness("s1", 1.0)
        ],
        source_ranking_assessments=[
            _ranking("s1", 0.90)
        ],
    )

    assert result.overall_status == SUPPORTED
    assert result.supported_claims == (
        "The system supports evidence-aware answers.",
    )


def test_multi_source_support_is_visible():
    knowledge = _knowledge(
        "k1",
        "The claim has multiple independent sources.",
        ["e1", "e2"],
    )

    evidence = [
        _evidence(
            "e1",
            "s1",
            "k1",
        ),
        _evidence(
            "e2",
            "s2",
            "k1",
        ),
    ]

    sources = [
        _source("s1"),
        _source("s2"),
    ]

    result = (
        QualityAwareAnswerSynthesizer()
        .synthesize(
            knowledge_items=[knowledge],
            evidence_items=evidence,
            sources=sources,
            confidence_assessments=[
                _confidence("k1", 0.92)
            ],
            agreement_assessments=[
                _agreement("k1", 1.0)
            ],
            freshness_assessments=[
                _freshness("s1", 1.0),
                _freshness("s2", 1.0),
            ],
            source_ranking_assessments=[
                _ranking("s1", 0.90),
                _ranking("s2", 0.88),
            ],
        )
    )

    assert (
        result.claims[0].status
        == MULTI_SOURCE_SUPPORTED
    )


def test_unresolved_conflict_is_not_silently_supported():
    knowledge = _knowledge(
        "k1",
        "This claim has conflicting evidence.",
        ["e1"],
    )

    evidence = [
        _evidence(
            "e1",
            "s1",
            "k1",
        )
    ]

    sources = [
        _source("s1")
    ]

    class Conflict:
        pass

    conflict = Conflict()
    conflict.first_knowledge_id = "k1"
    conflict.second_knowledge_id = "k2"
    conflict.resolution_status = "UNRESOLVED"

    result = (
        QualityAwareAnswerSynthesizer()
        .synthesize(
            knowledge_items=[knowledge],
            evidence_items=evidence,
            sources=sources,
            confidence_assessments=[
                _confidence("k1", 0.95)
            ],
            freshness_assessments=[
                _freshness("s1", 1.0)
            ],
            conflict_assessments=[
                conflict
            ],
        )
    )

    assert result.overall_status == CONFLICTED
    assert (
        "This claim has conflicting evidence."
        in result.conflicted_claims
    )


def test_unverified_claim_is_not_presented_as_supported():
    knowledge = _knowledge(
        "k1",
        "This claim is not verified.",
        ["e1"],
        verified=False,
        confidence=0.50,
    )

    evidence = [
        _evidence(
            "e1",
            "s1",
            "k1",
        )
    ]

    sources = [
        _source("s1")
    ]

    result = (
        QualityAwareAnswerSynthesizer()
        .synthesize(
            knowledge_items=[knowledge],
            evidence_items=evidence,
            sources=sources,
            confidence_assessments=[
                _confidence("k1", 0.50)
            ],
            freshness_assessments=[
                _freshness("s1", 1.0)
            ],
        )
    )

    assert result.overall_status == "UNVERIFIED"
    assert not result.claims[0].supported


def test_input_objects_are_not_mutated():
    knowledge = _knowledge(
        "k1",
        "Immutable claim.",
        ["e1"],
    )

    evidence = [
        _evidence(
            "e1",
            "s1",
            "k1",
        )
    ]

    sources = [
        _source("s1")
    ]

    knowledge_before = deepcopy(
        knowledge
    )
    evidence_before = deepcopy(
        evidence
    )
    sources_before = deepcopy(
        sources
    )

    result = (
        QualityAwareAnswerSynthesizer()
        .synthesize(
            knowledge_items=[knowledge],
            evidence_items=evidence,
            sources=sources,
            confidence_assessments=[
                _confidence("k1", 0.90)
            ],
            freshness_assessments=[
                _freshness("s1", 1.0)
            ],
            source_ranking_assessments=[
                _ranking("s1", 0.90)
            ],
        )
    )

    assert result is not None
    assert knowledge == knowledge_before
    assert evidence == evidence_before
    assert sources == sources_before


def test_deterministic_synthesis():
    knowledge = _knowledge(
        "k1",
        "Deterministic claim.",
        ["e1"],
    )

    evidence = [
        _evidence(
            "e1",
            "s1",
            "k1",
        )
    ]

    sources = [
        _source("s1")
    ]

    synthesizer = (
        QualityAwareAnswerSynthesizer()
    )

    kwargs = {
        "knowledge_items": [knowledge],
        "evidence_items": evidence,
        "sources": sources,
        "confidence_assessments": [
            _confidence("k1", 0.91)
        ],
        "freshness_assessments": [
            _freshness("s1", 1.0)
        ],
        "source_ranking_assessments": [
            _ranking("s1", 0.90)
        ],
    }

    first = synthesizer.synthesize(
        **kwargs
    )

    second = synthesizer.synthesize(
        **kwargs
    )

    assert first == second


def test_version():
    from core.research.answer_synthesis import (
        ANSWER_SYNTHESIS_VERSION,
    )

    result = (
        QualityAwareAnswerSynthesizer()
        .synthesize(
            knowledge_items=[],
            evidence_items=[],
            sources=[],
        )
    )

    assert (
        result.version
        == ANSWER_SYNTHESIS_VERSION
    )


def main():
    print(
        "SAHIBEX 6G-9 QUALITY-AWARE ANSWER "
        "SYNTHESIS TEST"
    )

    tests = [
        (
            "single-source supported claim",
            test_single_source_supported_claim,
        ),
        (
            "multi-source support",
            test_multi_source_support_is_visible,
        ),
        (
            "unresolved conflict protection",
            test_unresolved_conflict_is_not_silently_supported,
        ),
        (
            "unverified claim protection",
            test_unverified_claim_is_not_presented_as_supported,
        ),
        (
            "input immutability",
            test_input_objects_are_not_mutated,
        ),
        (
            "deterministic synthesis",
            test_deterministic_synthesis,
        ),
        (
            "version",
            test_version,
        ),
    ]

    for name, test in tests:
        test()
        print(
            f"[PASS] {name}"
        )

    print(
        "SAHIBEX 6G-9 QUALITY-AWARE ANSWER "
        "SYNTHESIS TEST: PASS"
    )


if __name__ == "__main__":
    main()
