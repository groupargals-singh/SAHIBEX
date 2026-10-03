from datetime import datetime, timezone

from core.research.conflict import ResearchConflictDetector
from core.research.conflict_intelligence import (
    CONFLICT_TYPE_EXPLICIT_NEGATION,
    CONFLICT_TYPE_LEXICAL_CONTRADICTION,
    RESOLUTION_RESOLVED,
    RESOLUTION_UNRESOLVED,
    ResearchConflictIntelligence,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


def knowledge(
    knowledge_id: str,
    statement: str,
    confidence: float = 0.80,
) -> KnowledgeCandidate:
    now = datetime.now(timezone.utc)

    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=[],
        evidence=[],
        confidence=confidence,
        verified=True,
        created_at=now,
        last_verified_at=now,
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
    supports: bool = True,
) -> Evidence:
    now = datetime.now(timezone.utc)

    return Evidence(
        evidence_id=evidence_id,
        finding_id="finding-" + evidence_id,
        source_id=source_id,
        evidence_text="test evidence",
        supports=supports,
        strength=strength,
        created_at=now,
        metadata={
            "knowledge_id": knowledge_id,
        },
    )


def main() -> None:
    detector = ResearchConflictDetector()
    intelligence = ResearchConflictIntelligence(
        detector=detector,
    )

    # =========================================================
    # 1. Explicit negation classification
    # =========================================================

    positive = knowledge(
        "k1",
        "the system is safe",
    )

    negated = knowledge(
        "k2",
        "the system is not safe",
    )

    result = intelligence.analyze(
        [positive, negated],
    )

    assert result.status == "UNRESOLVED"
    assert result.total_conflicts == 1
    assert result.unresolved_count == 1

    assessment = result.assessments[0]

    assert (
        assessment.conflict_type
        == CONFLICT_TYPE_EXPLICIT_NEGATION
    )

    assert (
        assessment.resolution_status
        == RESOLUTION_UNRESOLVED
    )

    assert assessment.selected_knowledge_id is None

    assert assessment.evidence_score_delta == 0.0
    assert assessment.source_reliability_delta == 0.0
    assert assessment.knowledge_confidence_delta == 0.0

    print(
        "[PASS] explicit negation classification"
    )

    # =========================================================
    # 2. Lexical contradiction classification
    # =========================================================

    enabled = knowledge(
        "k3",
        "network access is enabled",
    )

    disabled = knowledge(
        "k4",
        "network access is disabled",
    )

    result = intelligence.analyze(
        [enabled, disabled],
    )

    assert result.status == "UNRESOLVED"
    assert result.total_conflicts == 1

    assessment = result.assessments[0]

    assert (
        assessment.conflict_type
        == CONFLICT_TYPE_LEXICAL_CONTRADICTION
    )

    assert (
        assessment.resolution_status
        == RESOLUTION_UNRESOLVED
    )

    print(
        "[PASS] lexical contradiction classification"
    )

    # =========================================================
    # 3. Stronger evidence resolves conflict
    # =========================================================

    safe = knowledge(
        "k5",
        "the system is safe",
        confidence=0.80,
    )

    unsafe = knowledge(
        "k6",
        "the system is unsafe",
        confidence=0.80,
    )

    conflict = detector.detect_pair(
        safe,
        unsafe,
    )

    assert conflict is not None

    result = intelligence.analyze(
        [safe, unsafe],
        [
            evidence(
                "e1",
                "k5",
                "source-a",
                0.90,
                True,
            ),
            evidence(
                "e2",
                "k6",
                "source-b",
                0.30,
                True,
            ),
        ],
        [
            source(
                "source-a",
                0.50,
            ),
            source(
                "source-b",
                0.50,
            ),
        ],
    )

    assert result.status == "ALL_RESOLVED"
    assert result.resolved_count == 1
    assert result.unresolved_count == 0

    assessment = result.assessments[0]

    assert (
        assessment.resolution_status
        == RESOLUTION_RESOLVED
    )

    assert (
        assessment.selected_knowledge_id
        == "k5"
    )

    assert (
        assessment.evidence_score_delta
        == 0.60
    )

    assert (
        assessment.source_reliability_delta
        == 0.0
    )

    assert (
        assessment.knowledge_confidence_delta
        == 0.0
    )

    assert (
        assessment.resolution_reason
        == "stronger supporting evidence"
    )

    print(
        "[PASS] evidence-based resolution"
    )

    # =========================================================
    # 4. Source reliability resolves conflict
    # =========================================================

    safe = knowledge(
        "k7",
        "the system is safe",
        confidence=0.80,
    )

    unsafe = knowledge(
        "k8",
        "the system is unsafe",
        confidence=0.80,
    )

    result = intelligence.analyze(
        [safe, unsafe],
        [
            evidence(
                "e3",
                "k7",
                "source-a",
                0.50,
                True,
            ),
            evidence(
                "e4",
                "k8",
                "source-b",
                0.50,
                True,
            ),
        ],
        [
            source(
                "source-a",
                0.95,
            ),
            source(
                "source-b",
                0.40,
            ),
        ],
    )

    assert result.status == "ALL_RESOLVED"
    assert result.resolved_count == 1

    assessment = result.assessments[0]

    assert (
        assessment.selected_knowledge_id
        == "k7"
    )

    assert (
        assessment.evidence_score_delta
        == 0.0
    )

    assert (
        assessment.source_reliability_delta
        == 0.55
    )

    assert (
        assessment.resolution_reason
        == "higher source reliability"
    )

    print(
        "[PASS] source reliability resolution"
    )

    # =========================================================
    # 5. Knowledge confidence resolves conflict
    # =========================================================

    high = knowledge(
        "k9",
        "the system is safe",
        confidence=0.95,
    )

    low = knowledge(
        "k10",
        "the system is unsafe",
        confidence=0.70,
    )

    result = intelligence.analyze(
        [high, low],
    )

    assert result.status == "ALL_RESOLVED"
    assert result.resolved_count == 1

    assessment = result.assessments[0]

    assert (
        assessment.selected_knowledge_id
        == "k9"
    )

    assert (
        assessment.knowledge_confidence_delta
        == 0.25
    )

    assert (
        assessment.resolution_reason
        == "higher knowledge confidence"
    )

    print(
        "[PASS] confidence resolution"
    )

    # =========================================================
    # 6. Complete tie remains unresolved
    # =========================================================

    tied_a = knowledge(
        "k11",
        "the system is safe",
        confidence=0.80,
    )

    tied_b = knowledge(
        "k12",
        "the system is unsafe",
        confidence=0.80,
    )

    result = intelligence.analyze(
        [tied_a, tied_b],
    )

    assert result.status == "UNRESOLVED"
    assert result.resolved_count == 0
    assert result.unresolved_count == 1

    assessment = result.assessments[0]

    assert (
        assessment.resolution_status
        == RESOLUTION_UNRESOLVED
    )

    assert (
        assessment.selected_knowledge_id
        is None
    )

    assert (
        assessment.resolution_reason
        == (
            "evidence, source reliability, "
            "and confidence are tied"
        )
    )

    print(
        "[PASS] unresolved tie protection"
    )

    # =========================================================
    # 7. Unknown semantic relationship is not conflict
    # =========================================================

    python = knowledge(
        "k13",
        "the system uses Python",
    )

    sqlite = knowledge(
        "k14",
        "the system uses SQLite",
    )

    result = intelligence.analyze(
        [python, sqlite],
    )

    assert result.status == "NO_CONFLICT"
    assert result.total_conflicts == 0
    assert result.assessments == []

    print(
        "[PASS] unknown semantic relationship remains "
        "non-conflict"
    )

    # =========================================================
    # 8. Multiple conflicts
    # =========================================================

    k15 = knowledge(
        "k15",
        "network access is enabled",
        confidence=0.90,
    )

    k16 = knowledge(
        "k16",
        "network access is disabled",
        confidence=0.80,
    )

    k17 = knowledge(
        "the-placeholder",
        "the system is safe",
        confidence=0.80,
    )

    k18 = knowledge(
        "k18",
        "the system is unsafe",
        confidence=0.70,
    )

    result = intelligence.analyze(
        [k15, k16, k17, k18],
    )

    assert result.total_conflicts == 2
    assert result.resolved_count == 2
    assert result.unresolved_count == 0
    assert result.status == "ALL_RESOLVED"

    assert len(result.assessments) == 2

    print(
        "[PASS] multiple conflict analysis"
    )

    # =========================================================
    # 9. Missing knowledge protection
    # =========================================================

    missing_conflict = detector.detect_pair(
        positive,
        negated,
    )

    assert missing_conflict is not None

    # The intelligence layer normally receives complete
    # knowledge sets, so directly test the lower-level
    # resolver contract through assess_pair.
    missing_result = intelligence.assess_pair(
        missing_conflict,
        [positive],
        [],
        [],
    )

    assert (
        missing_result.resolution_status
        == RESOLUTION_UNRESOLVED
    )

    assert (
        missing_result.selected_knowledge_id
        is None
    )

    assert (
        missing_result.resolution_reason
        == "knowledge candidate missing"
    )

    print(
        "[PASS] missing knowledge protection"
    )

    # =========================================================
    # 10. No mutation of knowledge
    # =========================================================

    original_positive_statement = positive.statement
    original_negated_statement = negated.statement

    intelligence.analyze(
        [positive, negated],
    )

    assert (
        positive.statement
        == original_positive_statement
    )

    assert (
        negated.statement
        == original_negated_statement
    )

    print(
        "[PASS] knowledge immutability"
    )

    # =========================================================
    # 11. No mutation of evidence
    # =========================================================

    evidence_item = evidence(
        "e5",
        "k5",
        "source-a",
        0.70,
        True,
    )

    original_metadata = dict(
        evidence_item.metadata
    )
    original_strength = evidence_item.strength

    intelligence.analyze(
        [safe, unsafe],
        [evidence_item],
        [source("source-a", 0.80)],
    )

    assert (
        evidence_item.metadata
        == original_metadata
    )

    assert (
        evidence_item.strength
        == original_strength
    )

    print(
        "[PASS] evidence immutability"
    )

    # =========================================================
    # 12. No mutation of sources
    # =========================================================

    source_item = source(
        "source-x",
        0.80,
    )

    original_reliability = source_item.reliability
    original_metadata = dict(
        source_item.metadata
    )

    intelligence.analyze(
        [safe, unsafe],
        [],
        [source_item],
    )

    assert (
        source_item.reliability
        == original_reliability
    )

    assert (
        source_item.metadata
        == original_metadata
    )

    print(
        "[PASS] source immutability"
    )

    # =========================================================
    # Final
    # =========================================================

    print(
        "SAHIBEX 6G-5 CONFLICT INTELLIGENCE TEST: PASS"
    )


if __name__ == "__main__":
    main()
