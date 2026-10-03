from datetime import datetime, timezone

from core.research.conflict import ResearchConflictDetector
from core.research.conflict_resolver import (
    EvidenceAwareConflictResolver,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


def knowledge(
    knowledge_id: str,
    statement: str,
    confidence: float,
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
    resolver = EvidenceAwareConflictResolver()

    safe = knowledge(
        "k1",
        "the system is safe",
        0.80,
    )

    unsafe = knowledge(
        "k2",
        "the system is unsafe",
        0.80,
    )

    conflict = detector.detect_pair(
        safe,
        unsafe,
    )

    assert conflict is not None

    # ---------------------------------------------------------
    # 1. Stronger evidence wins
    # ---------------------------------------------------------
    result = resolver.resolve(
        [conflict],
        [safe, unsafe],
        [
            evidence(
                "e1",
                "k1",
                "source-a",
                0.90,
                True,
            ),
            evidence(
                "e2",
                "k2",
                "source-b",
                0.30,
                True,
            ),
        ],
        [
            source("source-a", 0.50),
            source("source-b", 0.50),
        ],
    )

    assert result.status == "ALL_RESOLVED"
    assert result.resolved_count == 1
    assert result.unresolved_count == 0
    assert result.resolutions[0].selected_knowledge_id == "k1"
    assert result.resolutions[0].reason == (
        "stronger supporting evidence"
    )

    print("[PASS] stronger evidence resolution")

    # ---------------------------------------------------------
    # 2. Higher source reliability wins
    # ---------------------------------------------------------
    result = resolver.resolve(
        [conflict],
        [safe, unsafe],
         [
            evidence(
                "e3",
                "k1",
                "source-a",
                0.50,
                True,
            ),
            evidence(
                "e4",
                "k2",
                "source-b",
                0.50,
                True,
            ),
        ],
        [
            source("source-a", 0.95),
            source("source-b", 0.40),
        ],
    )

    assert result.status == "ALL_RESOLVED"
    assert result.resolutions[0].selected_knowledge_id == "k1"
    assert result.resolutions[0].reason == (
        "higher source reliability"
    )

    print("[PASS] source reliability resolution")

    assert result.status == "ALL_RESOLVED"
    assert result.resolutions[0].selected_knowledge_id == "k1"

    print("[PASS] source reliability resolution")

    # ---------------------------------------------------------
    # 3. Higher confidence wins when evidence/source tie
    # ---------------------------------------------------------
    high_confidence = knowledge(
        "k3",
        "the system is safe",
        0.95,
    )

    low_confidence = knowledge(
        "k4",
        "the system is unsafe",
        0.70,
    )

    conflict_2 = detector.detect_pair(
        high_confidence,
        low_confidence,
    )

    assert conflict_2 is not None

    result = resolver.resolve(
        [conflict_2],
        [high_confidence, low_confidence],
        [],
        [],
    )

    assert result.status == "ALL_RESOLVED"
    assert result.resolutions[0].selected_knowledge_id == "k3"

    print("[PASS] confidence resolution")

    # ---------------------------------------------------------
    # 4. Complete tie remains unresolved
    # ---------------------------------------------------------
    tied_a = knowledge(
        "k5",
        "the system is safe",
        0.80,
    )

    tied_b = knowledge(
        "k6",
        "the system is unsafe",
        0.80,
    )

    conflict_3 = detector.detect_pair(
        tied_a,
        tied_b,
    )

    assert conflict_3 is not None

    result = resolver.resolve(
        [conflict_3],
        [tied_a, tied_b],
        [],
        [],
    )

    assert result.status == "UNRESOLVED"
    assert result.resolved_count == 0
    assert result.unresolved_count == 1
    assert result.resolutions[0].selected_knowledge_id is None

    print("[PASS] tied conflict remains unresolved")

    # ---------------------------------------------------------
    # 5. Missing knowledge remains unresolved
    # ---------------------------------------------------------
    result = resolver.resolve(
        [conflict],
        [safe],
        [],
        [],
    )

    assert result.status == "UNRESOLVED"
    assert result.resolved_count == 0
    assert result.unresolved_count == 1

    print("[PASS] missing knowledge protection")

    # ---------------------------------------------------------
    # 6. Empty conflicts
    # ---------------------------------------------------------
    result = resolver.resolve(
        [],
        [],
        [],
        [],
    )

    assert result.status == "NO_CONFLICT"
    assert result.total_conflicts == 0
    assert result.resolved_count == 0
    assert result.unresolved_count == 0

    print("[PASS] empty conflict handling")

    print("SAHIBEX CONFLICT RESOLVER TEST: PASS")


if __name__ == "__main__":
    main()
