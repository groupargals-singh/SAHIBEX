from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Optional
from uuid import uuid4

from core.brain.knowledge_brain import KnowledgeBrain
from core.brain.memory_brain import MemoryBrain
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
        # Operational context must reuse both specialist trust boundaries;
        # direct storage reads would bypass factual-memory provenance checks.
        self.memory_brain = MemoryBrain(storage=storage)
        self.knowledge_brain = KnowledgeBrain(storage=storage)

    def retrieve(
        self,
        *,
        query: str,
        memory_type: Optional[str] = None,
        min_memory_confidence: Optional[float] = None,
        min_memory_importance: Optional[float] = None,
        verified_knowledge_only: bool = True,
        min_knowledge_confidence: float = 0.0,
        limit: int = 32,
    ) -> OperationalMemoryKnowledgeResult:
        if not isinstance(query, str):
            raise TypeError("query must be a string.")

        normalized_query = " ".join(query.strip().split())

        if not normalized_query:
            raise ValueError("query must be a non-empty string.")

        memories = self.memory_brain.retrieve(
            normalized_query,
            memory_type=memory_type,
            min_confidence=min_memory_confidence,
            min_importance=min_memory_importance,
            limit=limit,
        )

        knowledge_result = self.knowledge_brain.retrieve(
            normalized_query,
            verified_only=verified_knowledge_only,
            min_confidence=min_knowledge_confidence,
            freshness_query=normalized_query,
        )
        knowledge = list(knowledge_result.knowledge)

        # The storage layer intentionally supports exact-phrase matching.
        # Natural-language questions rarely occur verbatim inside a fact
        # statement, so when that returns nothing, retrieve by meaningful
        # query terms through KnowledgeBrain (which reapplies lifecycle,
        # unresolved-conflict, and verified-only trust checks).
        if not knowledge:
            stopwords = {
                "the", "why", "what", "when", "where", "who", "which", "how",
                "is", "are", "was", "were", "do", "does", "did", "need", "needs",
                "and", "or", "for", "with", "from", "that", "this", "into",
                "क्या", "है", "हैं", "हो", "क्यों", "कब", "कहाँ", "कहां", "कौन",
                "कैसे", "किस", "की", "का", "के", "में", "पर", "से", "और", "एक",
                "को", "लिए", "होता", "होती", "होते", "बताओ", "बताइए",
                "kya", "kyu", "kyon", "kab", "kahan", "kaise", "hai", "hain",
                "ko", "se", "aur", "mein", "liye",
            }
            terms = [
                token for token in re.findall(r"[\w]+", normalized_query.casefold())
                if len(token) >= 2 and token not in stopwords
            ][:8]
            candidates = {}
            for term in terms:
                partial = self.knowledge_brain.retrieve(
                    term,
                    verified_only=verified_knowledge_only,
                    min_confidence=min_knowledge_confidence,
                    # Keep the original query semantics during token fallback;
                    # otherwise a "latest news" query could bypass freshness
                    # checks when the fallback token is just "AI" or a noun.
                    freshness_query=normalized_query,
                )
                for item in partial.knowledge:
                    candidates[item.knowledge_id] = item
            knowledge = list(candidates.values())
            knowledge.sort(
                key=lambda item: (-item.confidence, item.knowledge_id)
            )
        if limit is not None:
            knowledge = knowledge[:limit]

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
