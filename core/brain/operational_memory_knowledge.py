from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from uuid import uuid4

from core.research.memory_object import MemoryCandidate
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


@dataclass(frozen=True)
class OperationalMemoryKnowledgeResult:
    """Operational retrieval result for the master brain."""

    success: bool
    query: str
    memories: list[MemoryCandidate]
    knowledge: list[KnowledgeCandidate]
    memory_ids: list[str]
    knowledge_ids: list[str]
    summary: str
    retrieval_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(self.query, str):
            raise TypeError("query must be a string.")
        if not self.query.strip():
            raise ValueError("query must be a non-empty string.")

        if not isinstance(self.memories, list):
            raise TypeError("memories must be a list.")

        if not isinstance(self.knowledge, list):
            raise TypeError("knowledge must be a list.")

        if not isinstance(self.memory_ids, list):
            raise TypeError("memory_ids must be a list.")

        if not isinstance(self.knowledge_ids, list):
            raise TypeError("knowledge_ids must be a list.")

        for memory_id in self.memory_ids:
            if not isinstance(memory_id, str):
                raise TypeError("every memory ID must be a string.")
            if not memory_id.strip():
                raise ValueError("memory IDs must not be empty.")

        for knowledge_id in self.knowledge_ids:
            if not isinstance(knowledge_id, str):
                raise TypeError("every knowledge ID must be a string.")
            if not knowledge_id.strip():
                raise ValueError("knowledge IDs must not be empty.")

        if len(self.memory_ids) != len(self.memories):
            raise ValueError(
                "memory_ids must correspond to the retrieved memories."
            )

        if len(self.knowledge_ids) != len(self.knowledge):
            raise ValueError(
                "knowledge_ids must correspond to the retrieved knowledge."
            )

        if not isinstance(self.summary, str):
            raise TypeError("summary must be a string.")
        if not self.summary.strip():
            raise ValueError("summary must be a non-empty string.")

        if not isinstance(self.retrieval_id, str):
            raise TypeError("retrieval_id must be a string.")
        if not self.retrieval_id.strip():
            raise ValueError("retrieval_id must be a non-empty string.")


class OperationalMemoryKnowledgeIntegration:
    """Real read-only memory and knowledge retrieval for the operational brain.

    This layer uses ResearchStorage as the single source of truth.

    It does not:
    - modify memory
    - modify knowledge
    - touch access timestamps
    - grant permissions
    - execute tools
    - execute commands
    - access credentials
    - modify the constitution
    """

    def __init__(self, storage: ResearchStorage) -> None:
        if not isinstance(storage, ResearchStorage):
            raise TypeError("storage must be a ResearchStorage instance.")

        self.storage = storage

    def retrieve(
        self,
        *,
        query: str,
        memory_type: Optional[str] = None,
        min_memory_confidence: Optional[float] = None,
        min_memory_importance: Optional[float] = None,
        verified_knowledge_only: bool = False,
        min_knowledge_confidence: float = 0.0,
    ) -> OperationalMemoryKnowledgeResult:
        if not isinstance(query, str):
            raise TypeError("query must be a string.")

        normalized_query = " ".join(query.strip().split())

        if not normalized_query:
            raise ValueError("query must be a non-empty string.")

        memories = self.storage.retrieve_memories(
            normalized_query,
            memory_type=memory_type,
            min_confidence=min_memory_confidence,
            min_importance=min_memory_importance,
        )

        knowledge = self.storage.retrieve_knowledge(
            normalized_query,
            verified_only=verified_knowledge_only,
            min_confidence=min_knowledge_confidence,
        )

        memory_ids = [memory.memory_id for memory in memories]
        knowledge_ids = [item.knowledge_id for item in knowledge]

        summary = (
            f"Retrieved {len(memories)} memory item(s) and "
            f"{len(knowledge)} knowledge item(s) for the requested context."
        )

        return OperationalMemoryKnowledgeResult(
            success=True,
            query=normalized_query,
            memories=memories,
            knowledge=knowledge,
            memory_ids=memory_ids,
            knowledge_ids=knowledge_ids,
            summary=summary,
        )
