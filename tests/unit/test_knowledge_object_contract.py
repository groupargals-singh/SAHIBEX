from datetime import datetime, timezone

from core.research.models import KnowledgeCandidate


def test_required_fields() -> None:
    knowledge = KnowledgeCandidate(
        knowledge_id="knowledge_001",
        statement="SAHIBEX preserves verified research knowledge.",
    )

    assert knowledge.knowledge_id == "knowledge_001"
    assert knowledge.statement == (
        "SAHIBEX preserves verified research knowledge."
    )


def test_default_collections_and_state() -> None:
    knowledge = KnowledgeCandidate(
        knowledge_id="knowledge_002",
        statement="Knowledge has explicit verification state.",
    )

    assert knowledge.findings == []
    assert knowledge.evidence == []
    assert knowledge.confidence == 0.0
    assert knowledge.verified is False
    assert knowledge.last_verified_at is None
    assert knowledge.metadata == {}


def test_linked_findings_and_evidence() -> None:
    knowledge = KnowledgeCandidate(
        knowledge_id="knowledge_003",
        statement="Knowledge links findings and evidence.",
        findings=["finding_001", "finding_002"],
        evidence=["evidence_001", "evidence_002"],
    )

    assert knowledge.findings == [
        "finding_001",
        "finding_002",
    ]
    assert knowledge.evidence == [
        "evidence_001",
        "evidence_002",
    ]


def test_confidence_range() -> None:
    low = KnowledgeCandidate(
        knowledge_id="knowledge_004",
        statement="Low confidence knowledge.",
        confidence=0.0,
    )

    high = KnowledgeCandidate(
        knowledge_id="knowledge_005",
        statement="High confidence knowledge.",
        confidence=1.0,
    )

    assert low.confidence == 0.0
    assert high.confidence == 1.0


def test_timestamps_and_metadata() -> None:
    created_at = datetime.now(timezone.utc)
    verified_at = datetime.now(timezone.utc)

    knowledge = KnowledgeCandidate(
        knowledge_id="knowledge_006",
        statement="Knowledge retains lifecycle metadata.",
        created_at=created_at,
        last_verified_at=verified_at,
        metadata={"contract_version": "6H-1"},
    )

    assert knowledge.created_at == created_at
    assert knowledge.last_verified_at == verified_at
    assert knowledge.metadata["contract_version"] == "6H-1"


def test_empty_knowledge_id_is_rejected() -> None:
    try:
        KnowledgeCandidate(
            knowledge_id="",
            statement="Valid statement.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty knowledge_id should be rejected"
        )


def test_empty_statement_is_rejected() -> None:
    try:
        KnowledgeCandidate(
            knowledge_id="knowledge_007",
            statement="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty knowledge statement should be rejected"
        )


def test_invalid_confidence_is_rejected() -> None:
    for value in (-0.01, 1.01):
        try:
            KnowledgeCandidate(
                knowledge_id="knowledge_008",
                statement="Invalid confidence.",
                confidence=value,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"confidence {value} should be rejected"
            )


def test_verified_state_can_be_represented() -> None:
    verified_at = datetime.now(timezone.utc)

    knowledge = KnowledgeCandidate(
        knowledge_id="knowledge_009",
        statement="Verified knowledge.",
        confidence=0.90,
        verified=True,
        last_verified_at=verified_at,
    )

    assert knowledge.verified is True
    assert knowledge.confidence == 0.90
    assert knowledge.last_verified_at == verified_at


def main() -> None:
    print("SAHIBEX 6H-1 KNOWLEDGE OBJECT CONTRACT TEST")

    test_required_fields()
    print("[PASS] required fields")

    test_default_collections_and_state()
    print("[PASS] default state")

    test_linked_findings_and_evidence()
    print("[PASS] finding/evidence links")

    test_confidence_range()
    print("[PASS] confidence range")

    test_timestamps_and_metadata()
    print("[PASS] timestamps and metadata")

    test_empty_knowledge_id_is_rejected()
    print("[PASS] empty knowledge ID protection")

    test_empty_statement_is_rejected()
    print("[PASS] empty statement protection")

    test_invalid_confidence_is_rejected()
    print("[PASS] confidence validation")

    test_verified_state_can_be_represented()
    print("[PASS] verification state")

    print("SAHIBEX 6H-1 KNOWLEDGE OBJECT CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
