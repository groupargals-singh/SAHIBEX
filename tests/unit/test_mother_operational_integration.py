from __future__ import annotations

from tempfile import TemporaryDirectory
from pathlib import Path

from core.brain.master_brain import MasterBrain
from core.brain.mother_operational_integration import (
    MotherOperationalIntegration,
)
from core.research.memory_object import MemoryCandidate
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "sahibex_test.db"

        storage = ResearchStorage(database_path)

        integration = MotherOperationalIntegration(
            storage=storage,
        )

        # ---------------------------------------------------------
        # 1. Existing Mother Operational Integration
        # ---------------------------------------------------------
        result = integration.process_approved_request(
            objective="SAHIBEX",
            intent="explain",
            provider="mock",
        )

        # Mock provider echoes the prompt; the quality gate must reject it.
        assert result.success is False
        assert result.verification_status == "QUALITY_REJECTED"
        assert result.provider == "mock"

        print("[PASS] mother operational integration")

        # ---------------------------------------------------------
        # 2. Seed real Memory
        # ---------------------------------------------------------
        storage.save_memory(
            MemoryCandidate(
                memory_id="memory-master-brain",
                content=(
                    "SAHIBEX is the user's Mother Brain architecture."
                ),
                memory_type="fact",
                source="test",
                importance=1.0,
                confidence=1.0,
            )
        )

        # ---------------------------------------------------------
        # 3. Verify real Memory retrieval
        # ---------------------------------------------------------
        memory_result = integration.process_approved_request(
            objective="SAHIBEX",
            intent="explain",
            provider="mock",
        )

        assert memory_result.success is False
        assert memory_result.verification_status == "QUALITY_REJECTED"
        assert "memory-master-brain" in memory_result.memory_ids

        print("[PASS] real memory retrieval")

        # ---------------------------------------------------------
        # 4. Seed real Knowledge
        # ---------------------------------------------------------
        storage.save_knowledge(
            KnowledgeCandidate(
                knowledge_id="knowledge-mother-brain",
                statement="SAHIBEX",
                findings=[
                    "SAHIBEX is the Mother Brain architecture."
                ],
                evidence=[
                    "SAHIBEX project architecture specification."
                ],
                confidence=1.0,
                verified=True,
                metadata={
                    "source": "test",
                },
            )
        )

        # ---------------------------------------------------------
        # 5. Verify real Knowledge retrieval
        # ---------------------------------------------------------
        knowledge_result = integration.process_approved_request(
            objective="SAHIBEX",
            intent="explain",
            provider="mock",
        )

        assert knowledge_result.success is False
        assert knowledge_result.verification_status == "QUALITY_REJECTED"
        assert (
            "knowledge-mother-brain"
            in knowledge_result.knowledge_ids
        )

        print("[PASS] real knowledge retrieval")

        # ---------------------------------------------------------
        # 6. Inject SAME operational integration into MasterBrain
        # ---------------------------------------------------------
        brain = MasterBrain(
            mother_operational=integration,
        )

        # ---------------------------------------------------------
        # 7. Real MasterBrain request
        # ---------------------------------------------------------
        master_result = brain.process(
            "SAHIBEX"
        )

        assert master_result.success is False
        assert master_result.verification_status == "QUALITY_REJECTED"

        operational_metadata = (
            master_result.metadata[
                "mother_operational_integration"
            ]
        )

        assert operational_metadata["success"] is False
        assert (
            operational_metadata["verification_status"]
            == "QUALITY_REJECTED"
        )
        assert operational_metadata["provider"] == "mock"

        # ---------------------------------------------------------
        # 8. Memory must survive MasterBrain flow
        # ---------------------------------------------------------
        assert (
            "memory-master-brain"
            in operational_metadata["memory_ids"]
        )

        # ---------------------------------------------------------
        # 9. Knowledge must survive MasterBrain flow
        # ---------------------------------------------------------
        assert (
            "knowledge-mother-brain"
            in operational_metadata["knowledge_ids"]
        )

        print(
            "[PASS] Master Brain → Memory + Knowledge → Operational flow"
        )

    print(
        "SAHIBEX MASTER BRAIN MEMORY + KNOWLEDGE FLOW TEST: PASS"
    )


if __name__ == "__main__":
    main()
