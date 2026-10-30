from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.brain.knowledge_brain import KnowledgeBrain
from core.brain.master_brain import MasterBrain
from core.research.knowledge_conflict import (
    CONFLICT_TYPE_EXPLICIT_NEGATION,
    RESOLUTION_UNRESOLVED,
    KnowledgeConflictRecord,
)
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def test_knowledge_brain_persists_and_retrieves_verified_knowledge(tmp_path: Path) -> None:
    storage = ResearchStorage(tmp_path / "knowledge.db")
    brain = KnowledgeBrain(storage=storage)

    item = KnowledgeCandidate(
        knowledge_id="k-1",
        statement="SAHIBEX is a model-independent Main Brain.",
        confidence=0.95,
        verified=True,
        findings=["architecture"],
        evidence=["local-test"],
    )

    result = brain.remember(item)
    storage.record_knowledge_verification(
        knowledge_id=item.knowledge_id,
        status="VERIFIED",
        reason="Test fixture has explicit verified lifecycle evidence.",
        verified_at=datetime.now(timezone.utc),
    )

    assert result.success is True
    assert result.knowledge_id == "k-1"
    assert brain.get("k-1") == item

    retrieved = brain.retrieve(
        "model-independent Main Brain",
        verified_only=True,
        min_confidence=0.9,
    )

    assert retrieved.success is True
    assert retrieved.knowledge_ids == ("k-1",)


def test_knowledge_brain_separates_unverified_knowledge(tmp_path: Path) -> None:
    storage = ResearchStorage(tmp_path / "knowledge.db")
    brain = KnowledgeBrain(storage=storage)

    brain.remember(
        KnowledgeCandidate(
            knowledge_id="verified",
            statement="verified knowledge item",
            confidence=0.9,
            verified=True,
        )
    )
    storage.record_knowledge_verification(
        knowledge_id="verified",
        status="VERIFIED",
        reason="Test fixture has explicit verified lifecycle evidence.",
        verified_at=datetime.now(timezone.utc),
    )
    brain.remember(
        KnowledgeCandidate(
            knowledge_id="unverified",
            statement="unverified knowledge item",
            confidence=0.95,
            verified=False,
        )
    )

    verified = brain.retrieve("knowledge item", verified_only=True)
    assert verified.knowledge_ids == ("verified",)

    all_items = brain.retrieve("knowledge item")
    assert all_items.knowledge_ids == ("unverified", "verified")


def test_stale_verified_flag_is_rejected_after_unverified_lifecycle_event(
    tmp_path: Path,
) -> None:
    storage = ResearchStorage(tmp_path / "stale-knowledge.db")
    brain = KnowledgeBrain(storage=storage)
    item = KnowledgeCandidate(
        knowledge_id="stale-verified",
        statement="Unsupported claim must not be trusted.",
        confidence=0.99,
        verified=True,
    )
    brain.remember(item)
    now = datetime.now(timezone.utc)
    storage.record_knowledge_verification(
        knowledge_id=item.knowledge_id,
        status="VERIFIED",
        reason="Earlier verification event.",
        verified_at=now,
    )
    storage.record_knowledge_verification(
        knowledge_id=item.knowledge_id,
        status="UNVERIFIED",
        reason="Latest review found insufficient supporting evidence.",
        verified_at=now + timedelta(seconds=1),
    )

    assert brain.retrieve("Unsupported claim", verified_only=True).knowledge_ids == ()
    assert brain.retrieve("Unsupported claim", verified_only=False).knowledge_ids == ()
    assert all(
        candidate.knowledge_id != item.knowledge_id
        for candidate in brain.list(verified_only=True)
    )
    storage.close()


def test_verified_flag_without_verified_lifecycle_is_not_trusted(
    tmp_path: Path,
) -> None:
    storage = ResearchStorage(tmp_path / "missing-lifecycle.db")
    brain = KnowledgeBrain(storage=storage)
    item = KnowledgeCandidate(
        knowledge_id="no-lifecycle",
        statement="Claim has no persisted verification history.",
        confidence=0.99,
        verified=True,
    )
    brain.remember(item)

    assert brain.retrieve("Claim has no persisted", verified_only=True).knowledge_ids == ()
    assert all(
        candidate.knowledge_id != item.knowledge_id
        for candidate in brain.list(verified_only=True)
    )
    storage.close()


def test_unresolved_conflict_is_rejected_by_knowledge_brain(
    tmp_path: Path,
) -> None:
    storage = ResearchStorage(tmp_path / "conflicted-knowledge.db")
    brain = KnowledgeBrain(storage=storage)
    item = KnowledgeCandidate(
        knowledge_id="conflict-claim-a",
        statement="The system is online.",
        confidence=0.99,
        verified=True,
    )
    counterpart = KnowledgeCandidate(
        knowledge_id="conflict-claim-b",
        statement="The system is not online.",
        confidence=0.8,
        verified=False,
    )
    brain.remember(item)
    brain.remember(counterpart)
    storage.record_knowledge_verification(
        knowledge_id=item.knowledge_id,
        status="VERIFIED",
        reason="Earlier verification before conflict was recorded.",
        verified_at=datetime.now(timezone.utc),
    )
    storage.save_knowledge_conflict(
        KnowledgeConflictRecord(
            conflict_id="knowledge-brain-unresolved-conflict",
            first_knowledge_id=item.knowledge_id,
            second_knowledge_id=counterpart.knowledge_id,
            conflict_type=CONFLICT_TYPE_EXPLICIT_NEGATION,
            conflict_reason="Contradictory claims need review.",
            resolution_status=RESOLUTION_UNRESOLVED,
            selected_knowledge_id=None,
            evidence_score_delta=0.0,
            source_reliability_delta=0.0,
            knowledge_confidence_delta=0.0,
            resolution_reason="Evidence is insufficient to resolve the claims.",
            created_at=datetime.now(timezone.utc),
            metadata={"test": "task20-unsupported-knowledge"},
        )
    )

    assert brain.retrieve("system is online", verified_only=True).knowledge_ids == ()
    assert brain.retrieve("system is online", verified_only=False).knowledge_ids == ()
    assert all(
        candidate.knowledge_id != item.knowledge_id
        for candidate in brain.list(verified_only=True)
    )
    storage.close()


def test_resolved_conflict_excludes_non_selected_claim_from_retrieval(
    tmp_path: Path,
) -> None:
    from core.research.conflict_intelligence import ResearchConflictIntelligence

    storage = ResearchStorage(tmp_path / "resolved-conflict.db")
    brain = KnowledgeBrain(storage=storage)
    winner = KnowledgeCandidate(
        knowledge_id="resolved-winner",
        statement="The system is online.",
        confidence=0.95,
        verified=True,
    )
    loser = KnowledgeCandidate(
        knowledge_id="resolved-loser",
        statement="The system is not online.",
        confidence=0.60,
        verified=True,
    )
    brain.remember(winner)
    brain.remember(loser)
    now = datetime.now(timezone.utc)
    for item in (winner, loser):
        storage.record_knowledge_verification(
            knowledge_id=item.knowledge_id,
            status="VERIFIED",
            reason="Verified before the contradictory report arrived.",
            verified_at=now,
        )

    result = ResearchConflictIntelligence().analyze(
        knowledge_items=[winner, loser],
    )
    assert result.resolved_count == 1
    assessment = result.assessments[0]
    assert assessment.selected_knowledge_id == winner.knowledge_id
    storage.save_conflict_assessment(assessment)

    retrieved_ids = tuple(
        item.knowledge_id for item in brain.list(verified_only=True)
    )
    assert winner.knowledge_id in retrieved_ids
    assert loser.knowledge_id not in retrieved_ids

    from core.research.engine import ResearchEngine
    from core.research.query import ResearchQueryEngine

    query_engine = ResearchQueryEngine(
        engine=ResearchEngine(),
        storage=storage,
    )
    assert query_engine._passes_verification_gate(
        winner, verified_only=True
    ) is True
    assert query_engine._passes_verification_gate(
        loser, verified_only=True
    ) is False
    storage.close()


def test_knowledge_brain_capability_contract_has_no_authority() -> None:
    brain = KnowledgeBrain(storage=ResearchStorage(":memory:"))
    contract = brain.capability_contract()

    assert contract["persistent_knowledge"] is True
    assert contract["retrieval"] is True
    assert contract["execution_authority"] is False
    assert contract["permission_authority"] is False
    assert contract["constitution_mutation"] is False


def test_master_brain_owns_knowledge_brain_on_shared_storage() -> None:
    brain = MasterBrain()
    assert isinstance(brain.knowledge_brain, KnowledgeBrain)
    assert brain.knowledge_brain.storage is brain.mother_operational.storage
