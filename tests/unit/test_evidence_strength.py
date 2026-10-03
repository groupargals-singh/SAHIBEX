from core.research.evidence_strength import (
    EVIDENCE_STRENGTH_VERSION,
    assess_evidence_strength,
)
from core.research.models import (
    Evidence,
    ResearchFinding,
    ResearchSource,
)


def build_test_objects():
    source = ResearchSource(
        source_id="source-001",
        title="Test Source",
        source_type="web",
        locator="https://example.com/source-001",
        publisher="Example Publisher",
        reliability=0.80,
        metadata={
            "provider": "test-provider",
            "reliability_source": "provider",
            "reliability_version": "6G-1",
        },
    )

    finding = ResearchFinding(
        finding_id="finding-001",
        document_id="document-001",
        claim="SAHIBEX research pipeline stores verified evidence.",
        evidence_text=(
            "SAHIBEX research pipeline stores verified evidence."
        ),
        confidence=0.90,
    )

    evidence = Evidence(
        evidence_id="evidence-001",
        finding_id="finding-001",
        source_id="source-001",
        evidence_text=(
            "SAHIBEX research pipeline stores verified evidence."
        ),
        supports=True,
        strength=0.90,
    )

    return source, finding, evidence


def test_evidence_strength_identity():
    source, finding, evidence = build_test_objects()

    assessment = assess_evidence_strength(
        evidence=evidence,
        finding=finding,
        source=source,
    )

    assert assessment.evidence_id == "evidence-001"


def test_evidence_strength_scores_are_bounded():
    source, finding, evidence = build_test_objects()

    assessment = assess_evidence_strength(
        evidence=evidence,
        finding=finding,
        source=source,
    )

    scores = (
        assessment.strength_score,
        assessment.directness_score,
        assessment.specificity_score,
        assessment.finding_linkage_score,
        assessment.source_linkage_score,
        assessment.extraction_confidence_score,
    )

    for score in scores:
        assert 0.0 <= score <= 1.0


def test_evidence_strength_version():
    source, finding, evidence = build_test_objects()

    assessment = assess_evidence_strength(
        evidence=evidence,
        finding=finding,
        source=source,
    )

    assert assessment.version == EVIDENCE_STRENGTH_VERSION
    assert assessment.version == "6G-3"


def test_evidence_strength_confirms_finding_and_source_linkage():
    source, finding, evidence = build_test_objects()

    assessment = assess_evidence_strength(
        evidence=evidence,
        finding=finding,
        source=source,
    )

    assert assessment.finding_linkage_score == 1.0
    assert assessment.source_linkage_score == 1.0


def test_evidence_strength_uses_extraction_confidence():
    source, finding, evidence = build_test_objects()

    assessment = assess_evidence_strength(
        evidence=evidence,
        finding=finding,
        source=source,
    )

    assert assessment.extraction_confidence_score == 0.90


def test_evidence_strength_is_not_source_reliability():
    source, finding, evidence = build_test_objects()

    assessment = assess_evidence_strength(
        evidence=evidence,
        finding=finding,
        source=source,
    )

    assert assessment.strength_score != source.reliability


def test_evidence_strength_detects_direct_matching_evidence():
    source, finding, evidence = build_test_objects()

    assessment = assess_evidence_strength(
        evidence=evidence,
        finding=finding,
        source=source,
    )

    assert assessment.directness_score == 1.0


def test_evidence_strength_lower_for_unrelated_evidence():
    source, finding, evidence = build_test_objects()

    unrelated = Evidence(
        evidence_id="evidence-002",
        finding_id="finding-001",
        source_id="source-001",
        evidence_text="Weather conditions changed significantly.",
        supports=True,
        strength=0.90,
    )

    assessment = assess_evidence_strength(
        evidence=unrelated,
        finding=finding,
        source=source,
    )

    assert assessment.directness_score < 1.0


def test_evidence_strength_rejects_wrong_types():
    source, finding, evidence = build_test_objects()

    try:
        assess_evidence_strength(
            evidence="invalid",
            finding=finding,
            source=source,
        )
    except TypeError:
        pass
    else:
        raise AssertionError("Expected TypeError")


def run():
    tests = [
        test_evidence_strength_identity,
        test_evidence_strength_scores_are_bounded,
        test_evidence_strength_version,
        test_evidence_strength_confirms_finding_and_source_linkage,
        test_evidence_strength_uses_extraction_confidence,
        test_evidence_strength_is_not_source_reliability,
        test_evidence_strength_detects_direct_matching_evidence,
        test_evidence_strength_lower_for_unrelated_evidence,
        test_evidence_strength_rejects_wrong_types,
    ]

    for test in tests:
        test()

    print("SAHIBEX EVIDENCE STRENGTH MODEL TEST: PASS")


if __name__ == "__main__":
    run()
