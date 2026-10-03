from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass


from core.research.source_ranking import (
    SOURCE_RANKING_VERSION,
    SourceRankingEngine,
)


@dataclass
class FakeSource:
    source_id: str
    reliability: float


@dataclass
class FakeQuality:
    source_id: str
    quality_score: float


@dataclass
class FakeEvidence:
    source_id: str
    strength_score: float


@dataclass
class FakeAgreement:
    source_ids: list[str]
    agreement_score: float


@dataclass
class FakeConfidence:
    knowledge_id: str
    confidence_score: float


def test_basic_ranking() -> None:
    sources = [
        FakeSource("source_a", 0.90),
        FakeSource("source_b", 0.50),
    ]

    quality = [
        FakeQuality("source_a", 0.90),
        FakeQuality("source_b", 0.50),
    ]

    evidence = [
        FakeEvidence("source_a", 0.90),
        FakeEvidence("source_b", 0.50),
    ]

    agreement = [
        FakeAgreement(
            ["source_a", "source_b"],
            1.00,
        ),
    ]

    freshness = []

    confidence = [
        FakeConfidence("knowledge_a", 0.90),
        FakeConfidence("knowledge_b", 0.50),
    ]

    result = SourceRankingEngine().rank(
        sources=sources,
        quality_assessments=quality,
        evidence_assessments=evidence,
        agreement_assessments=agreement,
        freshness_assessments=freshness,
        confidence_assessments=confidence,
        source_knowledge_map={
            "source_a": ["knowledge_a"],
            "source_b": ["knowledge_b"],
        },
    )

    assert len(result) == 2
    assert result[0].source_id == "source_a"
    assert result[0].rank == 1
    assert result[1].source_id == "source_b"
    assert result[1].rank == 2


def test_ranking_is_deterministic() -> None:
    sources = [
        FakeSource("source_b", 0.70),
        FakeSource("source_a", 0.70),
    ]

    first = SourceRankingEngine().rank(
        sources=sources,
    )

    second = SourceRankingEngine().rank(
        sources=sources,
    )

    assert first == second

    assert first[0].source_id == "source_a"
    assert first[1].source_id == "source_b"


def test_reliability_affects_ranking() -> None:
    sources = [
        FakeSource("high", 1.00),
        FakeSource("low", 0.00),
    ]

    result = SourceRankingEngine().rank(
        sources=sources,
    )

    assert result[0].source_id == "high"
    assert result[0].ranking_score > result[1].ranking_score


def test_confidence_affects_ranking() -> None:
    sources = [
        FakeSource("source_a", 0.50),
        FakeSource("source_b", 0.50),
    ]

    confidence = [
        FakeConfidence("knowledge_a", 1.00),
        FakeConfidence("knowledge_b", 0.00),
    ]

    result = SourceRankingEngine().rank(
        sources=sources,
        confidence_assessments=confidence,
        source_knowledge_map={
            "source_a": ["knowledge_a"],
            "source_b": ["knowledge_b"],
        },
    )

    assert result[0].source_id == "source_a"


def test_quality_and_evidence_are_used() -> None:
    sources = [
        FakeSource("source_a", 0.50),
        FakeSource("source_b", 0.50),
    ]

    quality = [
        FakeQuality("source_a", 1.00),
        FakeQuality("source_b", 0.00),
    ]

    evidence = [
        FakeEvidence("source_a", 1.00),
        FakeEvidence("source_b", 0.00),
    ]

    result = SourceRankingEngine().rank(
        sources=sources,
        quality_assessments=quality,
        evidence_assessments=evidence,
    )

    assert result[0].source_id == "source_a"


def test_agreement_is_used() -> None:
    sources = [
        FakeSource("source_a", 0.50),
        FakeSource("source_b", 0.50),
    ]

    agreement = [
        FakeAgreement(
            ["source_a"],
            1.00,
        ),
        FakeAgreement(
            ["source_b"],
            0.00,
        ),
    ]

    result = SourceRankingEngine().rank(
        sources=sources,
        agreement_assessments=agreement,
    )

    assert result[0].source_id == "source_a"


def test_source_input_is_not_mutated() -> None:
    sources = [
        FakeSource("source_a", 0.90),
        FakeSource("source_b", 0.40),
    ]

    original = deepcopy(sources)

    SourceRankingEngine().rank(
        sources=sources,
    )

    assert sources == original


def test_unknown_optional_signals_do_not_crash() -> None:
    sources = [
        FakeSource("source_a", 0.80),
    ]

    result = SourceRankingEngine().rank(
        sources=sources,
    )

    assert len(result) == 1
    assert result[0].source_id == "source_a"


def test_version() -> None:
    result = SourceRankingEngine().rank(
        sources=[
            FakeSource("source_a", 0.80),
        ],
    )

    assert result[0].version == SOURCE_RANKING_VERSION
    assert result[0].version == "6G-8"


def main() -> None:
    print(
        "SAHIBEX 6G-8 SOURCE RANKING TEST"
    )

    tests = [
        (
            "basic ranking",
            test_basic_ranking,
        ),
        (
            "deterministic ranking",
            test_ranking_is_deterministic,
        ),
        (
            "reliability affects ranking",
            test_reliability_affects_ranking,
        ),
        (
            "confidence affects ranking",
            test_confidence_affects_ranking,
        ),
        (
            "quality and evidence are used",
            test_quality_and_evidence_are_used,
        ),
        (
            "agreement is used",
            test_agreement_is_used,
        ),
        (
            "source immutability",
            test_source_input_is_not_mutated,
        ),
        (
            "optional signals protection",
            test_unknown_optional_signals_do_not_crash,
        ),
        (
            "version",
            test_version,
        ),
    ]

    for name, test in tests:
        test()
        print(f"[PASS] {name}")

    print(
        "SAHIBEX 6G-8 SOURCE RANKING TEST: PASS"
    )


if __name__ == "__main__":
    main()
