from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from typing import Any, Dict, Tuple

from core.research.models import KnowledgeCandidate


@dataclass(frozen=True)
class KnowledgeDuplicateResult:
    statement_a: str
    statement_b: str
    normalized_a: str
    normalized_b: str
    similarity_score: float
    is_duplicate: bool


@dataclass(frozen=True)
class KnowledgeMergePlan:
    primary_knowledge_id: str
    duplicate_knowledge_id: str
    primary_statement: str
    duplicate_statement: str
    similarity_score: float
    safe_to_merge: bool


@dataclass(frozen=True)
class KnowledgeMergeResult:
    merged: bool
    safe_to_merge: bool
    knowledge: KnowledgeCandidate | None
    similarity_score: float


class KnowledgeDuplicateDetector:
    """
    Deterministic duplicate/similarity detector for knowledge statements.

    This component only detects duplicates and creates merge plans.
    It does not mutate knowledge objects, evidence, findings, links,
    storage, or verification state.
    """

    DUPLICATE_SIMILARITY = 1.0

    @staticmethod
    def _normalize(statement: str) -> str:
        if not isinstance(statement, str):
            raise ValueError("statement must be a string")

        normalized = statement.strip().lower()
        normalized = re.sub(r"\s+", " ", normalized)

        if not normalized:
            raise ValueError("statement cannot be empty")

        return normalized

    @classmethod
    def _similarity(
        cls,
        normalized_a: str,
        normalized_b: str,
    ) -> float:
        if normalized_a == normalized_b:
            return 1.0

        score = SequenceMatcher(
            None,
            normalized_a,
            normalized_b,
        ).ratio()

        return round(score, 6)

    def compare(
        self,
        statement_a: str,
        statement_b: str,
    ) -> KnowledgeDuplicateResult:
        normalized_a = self._normalize(statement_a)
        normalized_b = self._normalize(statement_b)

        similarity_score = self._similarity(
            normalized_a,
            normalized_b,
        )

        is_duplicate = (
            normalized_a == normalized_b
            and similarity_score == self.DUPLICATE_SIMILARITY
        )

        return KnowledgeDuplicateResult(
            statement_a=statement_a,
            statement_b=statement_b,
            normalized_a=normalized_a,
            normalized_b=normalized_b,
            similarity_score=similarity_score,
            is_duplicate=is_duplicate,
        )

    def plan_merge(
        self,
        primary_knowledge_id: str,
        duplicate_knowledge_id: str,
        primary_statement: str,
        duplicate_statement: str,
    ) -> KnowledgeMergePlan:
        if not isinstance(primary_knowledge_id, str):
            raise ValueError("primary_knowledge_id must be a string")

        if not isinstance(duplicate_knowledge_id, str):
            raise ValueError("duplicate_knowledge_id must be a string")

        if not primary_knowledge_id.strip():
            raise ValueError(
                "primary_knowledge_id cannot be empty"
            )

        if not duplicate_knowledge_id.strip():
            raise ValueError(
                "duplicate_knowledge_id cannot be empty"
            )

        if primary_knowledge_id == duplicate_knowledge_id:
            raise ValueError(
                "primary and duplicate knowledge IDs cannot be the same"
            )

        result = self.compare(
            primary_statement,
            duplicate_statement,
        )

        return KnowledgeMergePlan(
            primary_knowledge_id=primary_knowledge_id,
            duplicate_knowledge_id=duplicate_knowledge_id,
            primary_statement=primary_statement,
            duplicate_statement=duplicate_statement,
            similarity_score=result.similarity_score,
            safe_to_merge=result.is_duplicate,
        )


class KnowledgeMergeService:
    """
    Non-destructive knowledge merge service.

    A merge only creates a new KnowledgeCandidate representing the
    merged result. The original primary and duplicate objects are
    never mutated.

    This service does not:
    - delete knowledge
    - modify persistent storage
    - modify findings in storage
    - modify evidence in storage
    - migrate graph links
    - change the original knowledge objects
    """

    def __init__(
        self,
        detector: KnowledgeDuplicateDetector | None = None,
    ) -> None:
        self.detector = detector or KnowledgeDuplicateDetector()

    @staticmethod
    def _merge_unique(
        first: list[str],
        second: list[str],
    ) -> list[str]:
        merged: list[str] = []

        for item in first + second:
            if item not in merged:
                merged.append(item)

        return merged

    @staticmethod
    def _merge_metadata(
        primary: Dict[str, Any],
        duplicate: Dict[str, Any],
    ) -> Dict[str, Any]:
        merged = dict(primary)

        for key, value in duplicate.items():
            if key not in merged:
                merged[key] = value

        return merged

    @staticmethod
    def _merge_confidence(
        primary: float,
        duplicate: float,
    ) -> float:
        return max(primary, duplicate)

    @staticmethod
    def _merge_verified(
        primary: KnowledgeCandidate,
        duplicate: KnowledgeCandidate,
    ) -> bool:
        return primary.verified and duplicate.verified

    @staticmethod
    def _merge_last_verified_at(
        primary: KnowledgeCandidate,
        duplicate: KnowledgeCandidate,
    ):
        timestamps = [
            value
            for value in (
                primary.last_verified_at,
                duplicate.last_verified_at,
            )
            if value is not None
        ]

        if not timestamps:
            return None

        return max(timestamps)

    def merge(
        self,
        primary: KnowledgeCandidate,
        duplicate: KnowledgeCandidate,
    ) -> KnowledgeMergeResult:
        if not isinstance(primary, KnowledgeCandidate):
            raise TypeError(
                "primary must be a KnowledgeCandidate"
            )

        if not isinstance(duplicate, KnowledgeCandidate):
            raise TypeError(
                "duplicate must be a KnowledgeCandidate"
            )

        if primary.knowledge_id == duplicate.knowledge_id:
            raise ValueError(
                "primary and duplicate knowledge IDs cannot be the same"
            )

        comparison = self.detector.compare(
            primary.statement,
            duplicate.statement,
        )

        if not comparison.is_duplicate:
            return KnowledgeMergeResult(
                merged=False,
                safe_to_merge=False,
                knowledge=None,
                similarity_score=comparison.similarity_score,
            )

        merged = KnowledgeCandidate(
            knowledge_id=primary.knowledge_id,
            statement=primary.statement,
            findings=self._merge_unique(
                primary.findings,
                duplicate.findings,
            ),
            evidence=self._merge_unique(
                primary.evidence,
                duplicate.evidence,
            ),
            confidence=self._merge_confidence(
                primary.confidence,
                duplicate.confidence,
            ),
            verified=self._merge_verified(
                primary,
                duplicate,
            ),
            created_at=min(
                primary.created_at,
                duplicate.created_at,
            ),
            last_verified_at=self._merge_last_verified_at(
                primary,
                duplicate,
            ),
            metadata=self._merge_metadata(
                primary.metadata,
                duplicate.metadata,
            ),
        )

        return KnowledgeMergeResult(
            merged=True,
            safe_to_merge=True,
            knowledge=merged,
            similarity_score=comparison.similarity_score,
        )


__all__: Tuple[str, ...] = (
    "KnowledgeDuplicateResult",
    "KnowledgeMergePlan",
    "KnowledgeMergeResult",
    "KnowledgeDuplicateDetector",
    "KnowledgeMergeService",
)
