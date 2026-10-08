from pathlib import Path

from core.brain.knowledge_brain import KnowledgeBrain
from core.brain.master_brain import MasterBrain
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
