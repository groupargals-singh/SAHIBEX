from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Optional

from core.research.engine import ResearchEngine
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


@dataclass(frozen=True)
class KnowledgeMatch:
    knowledge_id: str
    statement: str
    confidence: float
    verified: bool


@dataclass(frozen=True)
class ResearchQueryResult:
    query: str
    matches: List[KnowledgeCandidate]
    verified_only: bool
    total_matches: int


class ResearchQueryEngine:
    """
    Search SAHIBEX knowledge.

    Knowledge can come from:
    - In-memory ResearchEngine
    - Persistent ResearchStorage

    By default, only verified knowledge is returned.
    """

    def __init__(
        self,
        engine: ResearchEngine,
        storage: Optional[ResearchStorage] = None,
    ) -> None:
        self.engine = engine
        self.storage = storage

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(
            text.lower().strip().split()
        )

    @classmethod
    def _words(cls, text: str) -> set[str]:
        normalized = cls._normalize(text)

        return set(
            re.findall(
                r"[a-z0-9]+",
                normalized,
            )
        )

    @classmethod
    def _score(
        cls,
        query: str,
        statement: str,
    ) -> float:
        query_words = cls._words(query)
        statement_words = cls._words(statement)

        if not query_words or not statement_words:
            return 0.0

        overlap = query_words.intersection(
            statement_words
        )

        return len(overlap) / len(query_words)

    def _load_knowledge(self) -> list[KnowledgeCandidate]:
        """
        Load knowledge from both memory and persistent storage.

        Persistent records are used when a storage backend is provided.
        Duplicate knowledge IDs are removed.
        """
        knowledge_by_id: dict[str, KnowledgeCandidate] = {}

        for knowledge in self.engine.knowledge.values():
            knowledge_by_id[
                knowledge.knowledge_id
            ] = knowledge

        if self.storage is not None:
            persisted = self.storage.list_knowledge(
                verified_only=False
            )

            for knowledge in persisted:
                knowledge_by_id[
                    knowledge.knowledge_id
                ] = knowledge

        return list(knowledge_by_id.values())

    def search(
        self,
        query: str,
        *,
        verified_only: bool = True,
        limit: int = 10,
    ) -> ResearchQueryResult:
        if not query or not query.strip():
            raise ValueError(
                "query cannot be empty"
            )

        if limit < 1:
            raise ValueError(
                "limit must be greater than zero"
            )

        candidates = []

        for knowledge in self._load_knowledge():
            if verified_only and not knowledge.verified:
                continue

            score = self._score(
                query,
                knowledge.statement,
            )

            if score <= 0:
                continue

            candidates.append(
                (
                    score,
                    knowledge.confidence,
                    knowledge,
                )
            )

        candidates.sort(
            key=lambda item: (
                item[0],
                item[1],
            ),
            reverse=True,
        )

        matches = [
            KnowledgeCandidate(
                knowledge_id=item[2].knowledge_id,
                statement=item[2].statement,
                confidence=item[2].confidence,
                verified=item[2].verified,
            )
            for item in candidates[:limit]
        ]

        return ResearchQueryResult(
            query=query,
            matches=matches,
            verified_only=verified_only,
            total_matches=len(matches),
        )
