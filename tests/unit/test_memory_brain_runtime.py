from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.memory_brain import MemoryBrain
from core.research.models import Evidence, ResearchSource
from core.research.storage import ResearchStorage
from core.research.memory_object import MemoryCandidate


def test_memory_brain_persists_and_reactivates_interaction() -> None:
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "memory.db")
        brain = MemoryBrain(storage=storage)
        written = brain.remember_interaction(
            user_text="Remember that SAHIBEX is my Main Brain.",
            assistant_text="Stored.",
            intent="general_request",
            action="respond",
            verification_status="VERIFIED",
        )
        assert written.persisted is True
        assert written.activated is True
        matches = brain.retrieve("SAHIBEX")
        assert matches
        assert matches[0].memory_id == written.memory_id
        assert matches[0].memory_type == "conversation"
        summary = brain.summary()
        assert summary["persistent_storage"] is True
        assert summary["retrieval"] is True
        assert summary["provenance"] is True
        assert summary["grants_permission"] is False
        assert summary["executes_actions"] is False
        assert summary["modifies_constitution"] is False
        storage.close()


def test_memory_brain_supports_fact_memory_and_working_memory() -> None:
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "memory.db")
        brain = MemoryBrain(storage=storage)
        written = brain.remember(
            content="SAHIBEX uses a local cognitive engine.",
            memory_type="project_fact",
            source="user-confirmed",
            importance=0.95,
            confidence=1.0,
            tags=["sahibex", "architecture"],
            metadata={"verified_by": "user"},
            priority=0.95,
        )
        assert written.memory_id
        assert brain.working_memory.contains(written.memory_id)
        assert brain.working_memory.promote_candidates()
        restored = storage.get_memory(written.memory_id)
        assert restored is not None
        assert restored.confidence == 1.0
        assert restored.metadata["verified_by"] == "user"
        storage.close()


def test_memory_brain_capability_contract() -> None:
    contract = MemoryBrain.capability_contract()
    required = (
        "working_memory",
        "short_term_memory",
        "long_term_memory",
        "episodic_memory",
        "semantic_memory",
        "user_context_memory",
        "task_project_memory",
        "persistent_retrieval",
        "relevance_ranking",
        "conflict_detection",
        "verification",
        "consolidation",
        "permission_controlled_memory",
    )
    for key in required:
        assert contract[key] is True
    assert contract["protected_execution"] is False
    assert contract["permission_grant"] is False
    assert contract["constitution_override"] is False


def test_unverified_research_fact_is_rejected_before_persistence() -> None:
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "memory.db")
        brain = MemoryBrain(storage=storage)
        result = brain.remember(
            content="An unverified claim.",
            memory_type="research_fact",
            source="web_search",
        )
        assert result.persisted is False
        assert result.activated is False
        assert result.status == "REJECTED_UNVERIFIED_FACT"
        assert brain.retrieve("unverified claim") == []
        assert brain.working_memory.contains(result.memory_id) is False
        storage.close()


def test_verified_status_without_provenance_is_rejected() -> None:
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "memory.db")
        brain = MemoryBrain(storage=storage)
        result = brain.remember(
            content="A purported verified claim.",
            memory_type="learned_fact",
            source="research_pipeline",
            metadata={
                "verified": True,
                "verification_status": "VERIFIED",
            },
        )
        assert result.persisted is False
        assert result.status == "REJECTED_UNVERIFIED_FACT"
        assert brain.retrieve("purported verified claim") == []
        storage.close()


def test_verified_fact_with_evidence_and_source_ids_is_persisted() -> None:
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "memory.db")
        brain = MemoryBrain(storage=storage)
        storage.save_source(
            ResearchSource(
                source_id="source-1",
                title="Research source one",
                source_type="test",
                locator="https://example.com/source-1",
                reliability=0.95,
            )
        )
        storage.save_source(
            ResearchSource(
                source_id="source-2",
                title="Research source two",
                source_type="test",
                locator="https://example.com/source-2",
                reliability=0.90,
            )
        )
        storage.save_evidence(
            Evidence(
                evidence_id="claim-evidence-1",
                finding_id="finding-1",
                source_id="source-1",
                evidence_text="A fact supported by traceable evidence.",
                supports=True,
                strength=0.95,
            )
        )
        result = brain.remember(
            content="A fact supported by traceable evidence.",
            memory_type="research_fact",
            source="research_pipeline",
            confidence=0.95,
            metadata={
                "verified": True,
                "verification_status": "VERIFIED",
                "evidence_ids": ["claim-evidence-1"],
                "source_ids": ["source-1", "source-2"],
            },
        )
        assert result.persisted is True
        assert result.activated is True
        assert result.status == "PERSISTED"
        restored = storage.get_memory(result.memory_id)
        assert restored is not None
        assert restored.metadata["evidence_ids"] == ["claim-evidence-1"]
        assert restored.metadata["source_ids"] == ["source-1", "source-2"]
        storage.close()


def test_new_factual_memory_alias_cannot_bypass_provenance_gate() -> None:
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "memory.db")
        brain = MemoryBrain(storage=storage)
        result = brain.remember(
            content="An unverified scientific claim.",
            memory_type="scientific_fact",
            source="learning_pipeline",
        )
        assert result.memory_id
        assert result.persisted is False
        assert result.activated is False
        assert result.status == "REJECTED_UNVERIFIED_FACT"
        assert storage.get_memory(result.memory_id) is None
        assert brain.working_memory.contains(result.memory_id) is False
        storage.close()


def test_verified_fact_with_provenance_is_retrievable() -> None:
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "memory.db")
        brain = MemoryBrain(storage=storage)

        storage.save_source(
            ResearchSource(
                source_id="trusted-source",
                title="Trusted test source",
                source_type="test",
                locator="https://example.com/trusted",
                reliability=0.95,
            )
        )
        storage.save_evidence(
            Evidence(
                evidence_id="trusted-evidence",
                finding_id="trusted-finding",
                source_id="trusted-source",
                evidence_text="SAHIBEX verified retrieval regression test.",
                supports=True,
                strength=0.95,
            )
        )

        result = brain.remember(
            content="SAHIBEX verified retrieval regression test.",
            memory_type="research_fact",
            source="research_pipeline",
            confidence=0.95,
            metadata={
                "verified": True,
                "verification_status": "VERIFIED",
                "evidence_ids": ["trusted-evidence"],
                "source_ids": ["trusted-source"],
            },
        )

        assert result.persisted is True
        matches = brain.retrieve("SAHIBEX verified retrieval regression test")
        assert any(item.memory_id == result.memory_id for item in matches)

        storage.close()


def test_verified_memory_survives_storage_restart_with_provenance_and_recall(tmp_path) -> None:
    database = tmp_path / "verified-memory-restart.db"
    storage = ResearchStorage(database)
    brain = MemoryBrain(storage=storage)
    storage.save_source(
        ResearchSource(
            source_id="restart-trusted-source",
            title="Restart provenance test source",
            source_type="test",
            locator="https://example.com/restart-provenance",
            reliability=0.97,
        )
    )
    storage.save_evidence(
        Evidence(
            evidence_id="restart-trusted-evidence",
            finding_id="restart-trusted-finding",
            source_id="restart-trusted-source",
            evidence_text="Verified memory must survive a process restart with its evidence links.",
            supports=True,
            strength=0.97,
        )
    )
    written = brain.remember(
        content="Verified memory restart provenance acceptance marker.",
        memory_type="research_fact",
        source="research_pipeline",
        confidence=0.97,
        metadata={
            "verified": True,
            "verification_status": "VERIFIED",
            "evidence_ids": ["restart-trusted-evidence"],
            "source_ids": ["restart-trusted-source"],
        },
    )
    assert written.persisted is True
    memory_id = written.memory_id
    storage.close()

    # A new storage/brain instance simulates a real process restart.
    restarted_storage = ResearchStorage(database)
    restarted_brain = MemoryBrain(storage=restarted_storage)
    matches = restarted_brain.retrieve("restart provenance acceptance marker")
    assert any(item.memory_id == memory_id for item in matches)
    restored = restarted_storage.get_memory(memory_id)
    assert restored is not None
    assert restored.metadata["verification_status"] == "VERIFIED"
    assert restored.metadata["evidence_ids"] == ["restart-trusted-evidence"]
    assert restored.metadata["source_ids"] == ["restart-trusted-source"]
    verification = restarted_storage.get_memory_verification(memory_id)
    assert verification is not None
    assert verification["status"] == "VERIFIED"
    assert verification["evidence_id"] == "restart-trusted-evidence"
    assert verification["reason"]
    restarted_storage.close()


def test_legacy_factual_memory_without_registry_is_not_retrievable() -> None:
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "memory.db")
        brain = MemoryBrain(storage=storage)

        legacy = MemoryCandidate(
            memory_id="legacy-unverified-fact",
            content="Legacy fact without a verification registry record.",
            memory_type="research_fact",
            source="legacy_import",
            metadata={
                "verified": True,
                "verification_status": "VERIFIED",
                "evidence_ids": ["legacy-evidence"],
                "source_ids": ["legacy-source"],
            },
        )
        storage.save_memory(legacy)

        assert storage.get_memory(legacy.memory_id) is not None
        assert brain.retrieve(
            "Legacy fact without a verification registry record"
        ) == []

        storage.close()


def test_conflicted_factual_memory_is_not_retrievable() -> None:
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "memory.db")
        brain = MemoryBrain(storage=storage)

        storage.save_source(
            ResearchSource(
                source_id="conflict-source",
                title="Conflict test source",
                source_type="test",
                locator="https://example.com/conflict",
                reliability=0.90,
            )
        )
        storage.save_evidence(
            Evidence(
                evidence_id="conflict-evidence",
                finding_id="conflict-finding",
                source_id="conflict-source",
                evidence_text="SAHIBEX unresolved conflict retrieval test.",
                supports=True,
                strength=0.90,
            )
        )

        result = brain.remember(
            content="SAHIBEX unresolved conflict retrieval test.",
            memory_type="research_fact",
            source="research_pipeline",
            confidence=0.90,
            metadata={
                "verified": True,
                "verification_status": "VERIFIED",
                "evidence_ids": ["conflict-evidence"],
                "source_ids": ["conflict-source"],
            },
        )
        assert result.persisted is True

        storage.record_memory_verification(
            memory_id=result.memory_id,
            status="CONFLICTED",
            evidence_id="conflict-evidence",
            reason="Regression test: conflicting evidence remains unresolved.",
        )

        assert brain.retrieve(
            "SAHIBEX unresolved conflict retrieval test"
        ) == []

        storage.close()
