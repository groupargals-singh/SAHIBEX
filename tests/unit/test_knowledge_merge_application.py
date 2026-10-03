from core.research.knowledge_merge import (
    KnowledgeMergeService,
)
from core.research.models import KnowledgeCandidate


def build_knowledge(
    knowledge_id: str,
    statement: str,
    *,
    findings=None,
    evidence=None,
    confidence=0.0,
    verified=False,
    metadata=None,
):
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=list(findings or []),
        evidence=list(evidence or []),
        confidence=confidence,
        verified=verified,
        metadata=dict(metadata or {}),
    )


def main() -> None:
    print("SAHIBEX 6H-6B SAFE KNOWLEDGE MERGE TEST")

    service = KnowledgeMergeService()

    primary = build_knowledge(
        "knowledge_001",
        "Python is a programming language.",
        findings=["finding_001"],
        evidence=["evidence_001"],
        confidence=0.70,
        verified=True,
        metadata={"primary": "yes"},
    )

    duplicate = build_knowledge(
        "knowledge_002",
        "Python   is a programming language.",
        findings=["finding_002"],
        evidence=["evidence_002"],
        confidence=0.80,
        verified=True,
        metadata={"duplicate": "yes"},
    )

    # 1. Safe exact/normalized duplicate merge
    result = service.merge(primary, duplicate)

    assert result.merged is True
    assert result.safe_to_merge is True
    assert result.knowledge.knowledge_id == "knowledge_001"
    assert result.knowledge.statement == primary.statement
    assert result.knowledge.findings == [
        "finding_001",
        "finding_002",
    ]
    assert result.knowledge.evidence == [
        "evidence_001",
        "evidence_002",
    ]
    assert result.knowledge.confidence == 0.80
    assert result.knowledge.verified is True
    print("[PASS] safe duplicate merge")

    # 2. Primary object must remain unchanged
    assert primary.findings == ["finding_001"]
    assert primary.evidence == ["evidence_001"]
    assert primary.confidence == 0.70
    assert primary.metadata == {"primary": "yes"}
    print("[PASS] primary object is not mutated")

    # 3. Duplicate object must remain unchanged
    assert duplicate.findings == ["finding_002"]
    assert duplicate.evidence == ["evidence_002"]
    assert duplicate.confidence == 0.80
    assert duplicate.metadata == {"duplicate": "yes"}
    print("[PASS] duplicate object is not mutated")

    # 4. Duplicate findings/evidence must not be repeated
    duplicate_overlap = build_knowledge(
        "knowledge_003",
        "Python is a programming language.",
        findings=["finding_001", "finding_003"],
        evidence=["evidence_001", "evidence_003"],
        confidence=0.75,
        verified=True,
    )

    overlap_result = service.merge(primary, duplicate_overlap)

    assert overlap_result.knowledge.findings == [
        "finding_001",
        "finding_003",
    ]
    assert overlap_result.knowledge.evidence == [
        "evidence_001",
        "evidence_003",
    ]
    print("[PASS] duplicate links are removed")

    # 5. Metadata is merged without mutating either source
    metadata_result = service.merge(
        primary,
        duplicate,
    )

    assert metadata_result.knowledge.metadata == {
        "primary": "yes",
        "duplicate": "yes",
    }
    print("[PASS] metadata merge")

    # 6. Different knowledge must not merge
    different = build_knowledge(
        "knowledge_004",
        "The Earth orbits the Sun.",
        findings=["finding_004"],
        evidence=["evidence_004"],
        confidence=0.90,
        verified=True,
    )

    unsafe_result = service.merge(primary, different)

    assert unsafe_result.merged is False
    assert unsafe_result.safe_to_merge is False
    assert unsafe_result.knowledge is None
    print("[PASS] unrelated knowledge is rejected")

    # 7. Similar but non-identical knowledge must not merge
    similar = build_knowledge(
        "knowledge_005",
        "Python is a popular programming language.",
        findings=["finding_005"],
        evidence=["evidence_005"],
        confidence=0.90,
        verified=True,
    )

    similar_result = service.merge(primary, similar)

    assert similar_result.merged is False
    assert similar_result.safe_to_merge is False
    assert similar_result.knowledge is None
    print("[PASS] similar knowledge is not automatically merged")

    # 8. Self-merge protection
    try:
        service.merge(primary, primary)
    except ValueError:
        pass
    else:
        raise AssertionError("self merge should be rejected")
    print("[PASS] self merge protection")

    # 9. Type protection
    try:
        service.merge(primary, object())
    except TypeError:
        pass
    else:
        raise AssertionError(
            "non-KnowledgeCandidate duplicate should be rejected"
        )
    print("[PASS] knowledge type protection")

    # 10. Empty knowledge statement remains protected
    try:
        invalid = build_knowledge(
            "knowledge_006",
            "",
        )
        service.merge(primary, invalid)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty knowledge statement should be rejected"
        )
    print("[PASS] invalid knowledge protection")

    print("SAHIBEX 6H-6B SAFE KNOWLEDGE MERGE TEST: PASS")


if __name__ == "__main__":
    main()
