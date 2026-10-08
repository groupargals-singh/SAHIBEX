from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.memory_brain import MemoryBrain
from core.research.storage import ResearchStorage


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
