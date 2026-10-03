from __future__ import annotations

from datetime import datetime, timezone

from core.research.models import KnowledgeCandidate


def test_knowledge_conflict_record_contract():
    from core.research.knowledge_conflict import (
        KnowledgeConflictRecord,
    )

    created_at = datetime.now(timezone.utc)

    record = KnowledgeConflictRecord(
        conflict_id="conflict-001",
        first_knowledge_id="knowledge-001",
        second_knowledge_id="knowledge-002",
        conflict_type="EXPLICIT_NEGATION",
        conflict_reason="same statement with opposite explicit negation",
        resolution_status="UNRESOLVED",
        selected_knowledge_id=None,
        evidence_score_delta=0.0,
        source_reliability_delta=0.0,
        knowledge_confidence_delta=0.0,
        resolution_reason="evidence, source reliability, and confidence are tied",
        created_at=created_at,
        metadata={"version": "6H-7"},
    )

    assert record.conflict_id == "conflict-001"
    assert record.first_knowledge_id == "knowledge-001"
    assert record.second_knowledge_id == "knowledge-002"
    assert record.conflict_type == "EXPLICIT_NEGATION"
    assert record.resolution_status == "UNRESOLVED"
    assert record.selected_knowledge_id is None
    assert record.created_at == created_at
    assert record.metadata["version"] == "6H-7"

    print("[PASS] conflict record fields")


def test_resolved_conflict_requires_selected_knowledge():
    from core.research.knowledge_conflict import (
        KnowledgeConflictRecord,
    )

    try:
        KnowledgeConflictRecord(
            conflict_id="conflict-002",
            first_knowledge_id="knowledge-001",
            second_knowledge_id="knowledge-002",
            conflict_type="LEXICAL_CONTRADICTION",
            conflict_reason="contradictory lexical term",
            resolution_status="RESOLVED",
            selected_knowledge_id=None,
            evidence_score_delta=0.5,
            source_reliability_delta=0.2,
            knowledge_confidence_delta=0.1,
            resolution_reason="stronger supporting evidence",
        )
    except ValueError:
        print("[PASS] resolved conflict selection protection")
        return

    raise AssertionError(
        "resolved conflict without selected knowledge must fail"
    )


def test_unresolved_conflict_cannot_select_knowledge():
    from core.research.knowledge_conflict import (
        KnowledgeConflictRecord,
    )

    try:
        KnowledgeConflictRecord(
            conflict_id="conflict-003",
            first_knowledge_id="knowledge-001",
            second_knowledge_id="knowledge-002",
            conflict_type="EXPLICIT_NEGATION",
            conflict_reason="opposite negation",
            resolution_status="UNRESOLVED",
            selected_knowledge_id="knowledge-001",
            evidence_score_delta=0.0,
            source_reliability_delta=0.0,
            knowledge_confidence_delta=0.0,
            resolution_reason="tie",
        )
    except ValueError:
        print("[PASS] unresolved conflict selection protection")
        return

    raise AssertionError(
        "unresolved conflict cannot select knowledge"
    )


def test_empty_conflict_id_protection():
    from core.research.knowledge_conflict import (
        KnowledgeConflictRecord,
    )

    try:
        KnowledgeConflictRecord(
            conflict_id="",
            first_knowledge_id="knowledge-001",
            second_knowledge_id="knowledge-002",
            conflict_type="EXPLICIT_NEGATION",
            conflict_reason="test",
            resolution_status="UNRESOLVED",
            selected_knowledge_id=None,
            evidence_score_delta=0.0,
            source_reliability_delta=0.0,
            knowledge_confidence_delta=0.0,
            resolution_reason="test",
        )
    except ValueError:
        print("[PASS] empty conflict ID protection")
        return

    raise AssertionError(
        "empty conflict ID must fail"
    )


def test_self_conflict_protection():
    from core.research.knowledge_conflict import (
        KnowledgeConflictRecord,
    )

    try:
        KnowledgeConflictRecord(
            conflict_id="conflict-004",
            first_knowledge_id="knowledge-001",
            second_knowledge_id="knowledge-001",
            conflict_type="EXPLICIT_NEGATION",
            conflict_reason="test",
            resolution_status="UNRESOLVED",
            selected_knowledge_id=None,
            evidence_score_delta=0.0,
            source_reliability_delta=0.0,
            knowledge_confidence_delta=0.0,
            resolution_reason="test",
        )
    except ValueError:
        print("[PASS] self conflict protection")
        return

    raise AssertionError(
        "a knowledge item cannot conflict with itself"
    )


def test_invalid_status_protection():
    from core.research.knowledge_conflict import (
        KnowledgeConflictRecord,
    )

    try:
        KnowledgeConflictRecord(
            conflict_id="conflict-005",
            first_knowledge_id="knowledge-001",
            second_knowledge_id="knowledge-002",
            conflict_type="EXPLICIT_NEGATION",
            conflict_reason="test",
            resolution_status="INVALID",
            selected_knowledge_id=None,
            evidence_score_delta=0.0,
            source_reliability_delta=0.0,
            knowledge_confidence_delta=0.0,
            resolution_reason="test",
        )
    except ValueError:
        print("[PASS] invalid resolution status protection")
        return

    raise AssertionError(
        "invalid resolution status must fail"
    )


def test_invalid_conflict_type_protection():
    from core.research.knowledge_conflict import (
        KnowledgeConflictRecord,
    )

    try:
        KnowledgeConflictRecord(
            conflict_id="conflict-006",
            first_knowledge_id="knowledge-001",
            second_knowledge_id="knowledge-002",
            conflict_type="INVALID",
            conflict_reason="test",
            resolution_status="UNRESOLVED",
            selected_knowledge_id=None,
            evidence_score_delta=0.0,
            source_reliability_delta=0.0,
            knowledge_confidence_delta=0.0,
            resolution_reason="test",
        )
    except ValueError:
        print("[PASS] invalid conflict type protection")
        return

    raise AssertionError(
        "invalid conflict type must fail"
    )


def test_score_range_protection():
    from core.research.knowledge_conflict import (
        KnowledgeConflictRecord,
    )

    try:
        KnowledgeConflictRecord(
            conflict_id="conflict-007",
            first_knowledge_id="knowledge-001",
            second_knowledge_id="knowledge-002",
            conflict_type="EXPLICIT_NEGATION",
            conflict_reason="test",
            resolution_status="UNRESOLVED",
            selected_knowledge_id=None,
            evidence_score_delta=2.0,
            source_reliability_delta=0.0,
            knowledge_confidence_delta=0.0,
            resolution_reason="test",
        )
    except ValueError:
        print("[PASS] score range protection")
        return

    raise AssertionError(
        "score delta outside allowed range must fail"
    )


def test_knowledge_objects_are_not_mutated():
    from core.research.knowledge_conflict import (
        KnowledgeConflictRecord,
    )

    first = KnowledgeCandidate(
        knowledge_id="knowledge-001",
        statement="The system is active.",
        confidence=0.8,
    )

    second = KnowledgeCandidate(
        knowledge_id="knowledge-002",
        statement="The system is not active.",
        confidence=0.7,
    )

    original_first = first
    original_second = second

    KnowledgeConflictRecord(
        conflict_id="conflict-008",
        first_knowledge_id=first.knowledge_id,
        second_knowledge_id=second.knowledge_id,
        conflict_type="EXPLICIT_NEGATION",
        conflict_reason="opposite negation",
        resolution_status="UNRESOLVED",
        selected_knowledge_id=None,
        evidence_score_delta=0.1,
        source_reliability_delta=0.1,
        knowledge_confidence_delta=0.1,
        resolution_reason="insufficient evidence",
    )

    assert first is original_first
    assert second is original_second
    assert first.verified is False
    assert second.verified is False

    print("[PASS] knowledge objects remain unchanged")


if __name__ == "__main__":
    print("SAHIBEX 6H-7 KNOWLEDGE CONFLICT TEST")

    test_knowledge_conflict_record_contract()
    test_resolved_conflict_requires_selected_knowledge()
    test_unresolved_conflict_cannot_select_knowledge()
    test_empty_conflict_id_protection()
    test_self_conflict_protection()
    test_invalid_status_protection()
    test_invalid_conflict_type_protection()
    test_score_range_protection()
    test_knowledge_objects_are_not_mutated()

    print("SAHIBEX 6H-7 KNOWLEDGE CONFLICT TEST: PASS")
