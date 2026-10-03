from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.operational_memory_knowledge import (
    OperationalMemoryKnowledgeIntegration,
    OperationalMemoryKnowledgeResult,
)
from core.research.memory_object import MemoryCandidate
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def build_storage(database_path: Path) -> ResearchStorage:
    storage = ResearchStorage(database_path)

    storage.save_memory(
        MemoryCandidate(
            memory_id="memory-python",
            content="User is building SAHIBEX with Python.",
            memory_type="project",
            source="user",
            importance=0.9,
            confidence=1.0,
            tags=["sahibex", "python", "development"],
            metadata={"project": "SAHIBEX"},
        )
    )

    storage.save_memory(
        MemoryCandidate(
            memory_id="memory-termux",
            content="User develops SAHIBEX in Termux.",
            memory_type="environment",
            source="user",
            importance=0.8,
            confidence=0.95,
            tags=["sahibex", "termux"],
            metadata={"project": "SAHIBEX"},
        )
    )

    storage.save_memory(
        MemoryCandidate(
            memory_id="memory-trading",
            content="Quantum-bot is a trading specialist brain.",
            memory_type="project",
            source="user",
            importance=0.7,
            confidence=0.9,
            tags=["quantum-bot", "trading"],
            metadata={"project": "quantum-bot"},
        )
    )

    storage.save_knowledge(
        KnowledgeCandidate(
            knowledge_id="knowledge-python",
            statement="SAHIBEX uses Python as its primary implementation language.",
            confidence=0.95,
            verified=True,
            metadata={"topic": "SAHIBEX"},
        )
    )

    storage.save_knowledge(
        KnowledgeCandidate(
            knowledge_id="knowledge-termux",
            statement="SAHIBEX is developed in the Termux environment.",
            confidence=0.9,
            verified=True,
            metadata={"topic": "SAHIBEX"},
        )
    )

    storage.save_knowledge(
        KnowledgeCandidate(
            knowledge_id="knowledge-unverified",
            statement="SAHIBEX may eventually support additional environments.",
            confidence=0.5,
            verified=False,
            metadata={"topic": "SAHIBEX"},
        )
    )

    return storage


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "research.sqlite3"

        storage = build_storage(database_path)
        integration = OperationalMemoryKnowledgeIntegration(storage)

        result = integration.retrieve(query="SAHIBEX")

        assert isinstance(result, OperationalMemoryKnowledgeResult)
        assert result.success is True

        assert result.query == "SAHIBEX"

        assert result.memory_ids == [
            "memory-python",
            "memory-termux",
        ]

        assert result.knowledge_ids == [
            "knowledge-python",
            "knowledge-termux",
            "knowledge-unverified",
        ]

        assert len(result.memories) == 2
        assert len(result.knowledge) == 3

        verified_result = integration.retrieve(
            query="SAHIBEX",
            verified_knowledge_only=True,
        )

        assert verified_result.knowledge_ids == [
            "knowledge-python",
            "knowledge-termux",
        ]

        python_result = integration.retrieve(query="Python")

        assert python_result.memory_ids == ["memory-python"]
        assert python_result.knowledge_ids == ["knowledge-python"]

        filtered_result = integration.retrieve(
            query="SAHIBEX",
            min_memory_confidence=0.98,
        )

        assert filtered_result.memory_ids == ["memory-python"]

        empty_result = integration.retrieve(
            query="does-not-exist",
        )

        assert empty_result.success is True
        assert empty_result.memory_ids == []
        assert empty_result.knowledge_ids == []
        assert empty_result.memories == []
        assert empty_result.knowledge == []

        second_result = integration.retrieve(query="SAHIBEX")

        assert second_result.retrieval_id != result.retrieval_id
        assert second_result.memory_ids == result.memory_ids
        assert second_result.knowledge_ids == result.knowledge_ids

        try:
            integration.retrieve(query="")
        except ValueError:
            pass
        else:
            raise AssertionError("Empty query must be rejected.")

        try:
            integration.retrieve(query="   ")
        except ValueError:
            pass
        else:
            raise AssertionError("Whitespace-only query must be rejected.")

        assert not hasattr(
            OperationalMemoryKnowledgeIntegration,
            "touch_memory",
        )

        assert not hasattr(
            OperationalMemoryKnowledgeIntegration,
            "grant_permission",
        )

        assert not hasattr(
            OperationalMemoryKnowledgeKnowledgeIntegration
            if False
            else OperationalMemoryKnowledgeIntegration,
            "execute_tool",
        )

    print(
        "SAHIBEX 6O-4 REAL MEMORY KNOWLEDGE RETRIEVAL TEST: PASS"
    )


if __name__ == "__main__":
    main()
