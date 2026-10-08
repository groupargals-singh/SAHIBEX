from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
from uuid import uuid4

from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


@dataclass(frozen=True)
class KnowledgeWriteResult:
    """Result of persisting knowledge into the SAHIBEX Knowledge Brain."""

    success: bool
    knowledge_id: str
    verified: bool
    confidence: float
    write_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True)
class KnowledgeRetrievalResult:
    """Deterministic Knowledge Brain retrieval result."""

    success: bool
    query: str
    knowledge: tuple[KnowledgeCandidate, ...]
    retrieval_id: str = field(default_factory=lambda: str(uuid4()))

    @property
    def knowledge_ids(self) -> tuple[str, ...]:
        return tuple(item.knowledge_id for item in self.knowledge)


class KnowledgeBrain:
    """SAHIBEX's persistent knowledge ownership and retrieval boundary.

    The Knowledge Brain owns durable factual/conceptual knowledge access.
    It does not grant permissions, execute protected actions, or modify
    the Constitution.
    """

    VERSION = "1.0"

    def __init__(self, *, storage: ResearchStorage) -> None:
        if not isinstance(storage, ResearchStorage):
            raise TypeError("storage must be a ResearchStorage instance.")
        self.storage = storage

    def remember(self, knowledge: KnowledgeCandidate) -> KnowledgeWriteResult:
        if not isinstance(knowledge, KnowledgeCandidate):
            raise TypeError("knowledge must be a KnowledgeCandidate.")
        self.storage.save_knowledge(knowledge)
        return KnowledgeWriteResult(
            success=True,
            knowledge_id=knowledge.knowledge_id,
            verified=knowledge.verified,
            confidence=knowledge.confidence,
        )

    def remember_many(
        self,
        knowledge_items: Iterable[KnowledgeCandidate],
    ) -> tuple[KnowledgeWriteResult, ...]:
        results: list[KnowledgeWriteResult] = []
        for item in knowledge_items:
            results.append(self.remember(item))
        return tuple(results)

    def retrieve(
        self,
        query: str,
        *,
        verified_only: bool = False,
        min_confidence: float = 0.0,
    ) -> KnowledgeRetrievalResult:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string.")
        knowledge = self.storage.retrieve_knowledge(
            query,
            verified_only=verified_only,
            min_confidence=min_confidence,
        )
        return KnowledgeRetrievalResult(
            success=True,
            query=" ".join(query.strip().split()),
            knowledge=tuple(knowledge),
        )

    def get(self, knowledge_id: str) -> KnowledgeCandidate | None:
        if not isinstance(knowledge_id, str) or not knowledge_id.strip():
            raise ValueError("knowledge_id must be a non-empty string.")
        return self.storage.get_knowledge(knowledge_id)

    def list(self, *, verified_only: bool = False) -> tuple[KnowledgeCandidate, ...]:
        return tuple(self.storage.list_knowledge(verified_only=verified_only))

    def summary(self) -> dict[str, object]:
        return {
            "version": self.VERSION,
            "persistent": True,
            "retrieval": True,
            "provenance_preserved": True,
            "verified_only_retrieval": True,
            "confidence_filtering": True,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }

    def capability_contract(self) -> dict[str, bool]:
        return {
            "persistent_knowledge": True,
            "retrieval": True,
            "confidence_filtering": True,
            "verified_only_retrieval": True,
            "execution_authority": False,
            "permission_authority": False,
            "constitution_mutation": False,
        }
