from __future__ import annotations

from datetime import datetime, timezone

from core.research.engine import ResearchEngine
from core.research.models import KnowledgeCandidate
from core.research.query import ResearchQueryEngine
from core.research.storage import ResearchStorage


def _candidate(
    knowledge_id: str,
    *,
    verified: bool = True,
    metadata: dict | None = None,
) -> KnowledgeCandidate:
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement="SAHIBEX trusted verified research fact",
        confidence=0.99,
        verified=verified,
        metadata=metadata or {},
    )


def test_explicitly_conflicted_in_memory_knowledge_is_never_retrieved() -> None:
    engine = ResearchEngine()
    candidate = _candidate(
        "memory-conflicted",
        metadata={"verification_status": "CONFLICTED"},
    )
    engine.knowledge[candidate.knowledge_id] = candidate
    query = ResearchQueryEngine(engine)

    assert query.search("trusted verified research", verified_only=True).matches == []
    assert query.search("trusted verified research", verified_only=False).matches == []


def test_persisted_conflicted_verification_history_blocks_retrieval() -> None:
    storage = ResearchStorage(":memory:")
    candidate = _candidate("persisted-conflicted")
    storage.save_knowledge(candidate)
    storage.record_knowledge_verification(
        knowledge_id=candidate.knowledge_id,
        status="CONFLICTED",
        reason="Conflicting evidence remains unresolved.",
        verified_at=datetime.now(timezone.utc),
        metadata={"test": "task8"},
    )

    query = ResearchQueryEngine(ResearchEngine(), storage=storage)
    assert query.search("trusted verified research", verified_only=True).matches == []
    assert query.search("trusted verified research", verified_only=False).matches == []
    storage.close()


def test_latest_unverified_history_cannot_be_overridden_by_stale_verified_flag() -> None:
    storage = ResearchStorage(":memory:")
    candidate = _candidate("persisted-stale-verified-flag")
    storage.save_knowledge(candidate)
    storage.record_knowledge_verification(
        knowledge_id=candidate.knowledge_id,
        status="UNVERIFIED",
        reason="Evidence was insufficient on the latest review.",
        verified_at=datetime.now(timezone.utc),
        metadata={"test": "task8"},
    )

    query = ResearchQueryEngine(ResearchEngine(), storage=storage)
    assert query.search("trusted verified research", verified_only=True).matches == []
    storage.close()


def test_legacy_verified_flag_without_lifecycle_history_is_not_verified_only_retrievable() -> None:
    storage = ResearchStorage(":memory:")
    candidate = _candidate("legacy-verified-without-history", verified=True)
    storage.save_knowledge(candidate)

    query = ResearchQueryEngine(ResearchEngine(), storage=storage)
    result = query.search("trusted verified research", verified_only=True)

    assert result.matches == []
    storage.close()


def test_in_memory_verified_flag_without_explicit_status_is_not_verified_only_retrievable() -> None:
    engine = ResearchEngine()
    candidate = _candidate("memory-legacy-verified-flag", verified=True)
    engine.knowledge[candidate.knowledge_id] = candidate

    result = ResearchQueryEngine(engine).search(
        "trusted verified research",
        verified_only=True,
    )
    assert result.matches == []


def test_in_memory_verification_timestamp_without_verified_status_is_rejected() -> None:
    engine = ResearchEngine()
    candidate = _candidate("memory-timestamp-only")
    candidate.last_verified_at = datetime.now(timezone.utc)
    engine.knowledge[candidate.knowledge_id] = candidate

    result = ResearchQueryEngine(engine).search(
        "trusted verified research",
        verified_only=True,
    )
    assert result.matches == []


def test_in_memory_explicit_verified_status_and_timestamp_are_required() -> None:
    engine = ResearchEngine()
    candidate = _candidate(
        "memory-explicit-verified",
        metadata={"verification_status": "VERIFIED"},
    )
    candidate.last_verified_at = datetime.now(timezone.utc)
    engine.knowledge[candidate.knowledge_id] = candidate

    result = ResearchQueryEngine(engine).search(
        "trusted verified research",
        verified_only=True,
    )
    assert [item.knowledge_id for item in result.matches] == [
        "memory-explicit-verified"
    ]


def test_explicit_unverified_metadata_cannot_pass_verified_only_gate() -> None:
    engine = ResearchEngine()
    candidate = _candidate(
        "memory-stale-flag",
        metadata={"verification_status": "UNVERIFIED"},
    )
    engine.knowledge[candidate.knowledge_id] = candidate

    result = ResearchQueryEngine(engine).search(
        "trusted verified research",
        verified_only=True,
    )
    assert result.matches == []

from core.research.knowledge_conflict import (
    CONFLICT_TYPE_EXPLICIT_NEGATION,
    RESOLUTION_UNRESOLVED,
    KnowledgeConflictRecord,
)


def test_unresolved_persisted_conflict_blocks_even_when_history_is_verified() -> None:
    storage = ResearchStorage(":memory:")
    candidate = _candidate("persisted-unresolved-conflict")
    counterpart = KnowledgeCandidate(
        knowledge_id="persisted-conflict-counterpart",
        statement="SAHIBEX trusted verified research fact is false",
        confidence=0.7,
        verified=False,
    )
    storage.save_knowledge(candidate)
    storage.save_knowledge(counterpart)
    storage.record_knowledge_verification(
        knowledge_id=candidate.knowledge_id,
        status="VERIFIED",
        reason="Prior verification.",
        verified_at=datetime.now(timezone.utc),
        metadata={"test": "task8"},
    )
    storage.save_knowledge_conflict(
        KnowledgeConflictRecord(
            conflict_id="task8-unresolved-conflict",
            first_knowledge_id=candidate.knowledge_id,
            second_knowledge_id=counterpart.knowledge_id,
            conflict_type=CONFLICT_TYPE_EXPLICIT_NEGATION,
            conflict_reason="Conflicting claims require review.",
            resolution_status=RESOLUTION_UNRESOLVED,
            selected_knowledge_id=None,
            evidence_score_delta=0.0,
            source_reliability_delta=0.0,
            knowledge_confidence_delta=0.0,
            resolution_reason="Insufficient evidence.",
            created_at=datetime.now(timezone.utc),
            metadata={"test": "task8"},
        )
    )

    query = ResearchQueryEngine(ResearchEngine(), storage=storage)
    assert query.search("trusted verified research", verified_only=True).matches == []
    assert query.search("trusted verified research", verified_only=False).matches == []
    storage.close()
