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

    @staticmethod
    def _metadata_verification_status(
        knowledge: KnowledgeCandidate,
    ) -> str:
        metadata = getattr(knowledge, "metadata", {}) or {}
        return str(
            metadata.get("verification_status", "")
        ).strip().upper()

    @staticmethod
    def _metadata_has_unresolved_conflict(
        knowledge: KnowledgeCandidate,
    ) -> bool:
        metadata = getattr(knowledge, "metadata", {}) or {}
        conflict_status = str(
            metadata.get("conflict_status", "")
        ).strip().upper()
        try:
            unresolved_count = int(
                metadata.get("unresolved_conflict_count", 0) or 0
            )
        except (TypeError, ValueError):
            # Malformed conflict metadata must not be treated as safe.
            return True

        return (
            conflict_status in {"UNRESOLVED", "CONFLICTED"}
            or unresolved_count > 0
        )

    def _passes_verification_gate(
        self,
        knowledge: KnowledgeCandidate,
        *,
        verified_only: bool,
    ) -> bool:
        """
        Reject explicitly conflicted knowledge in every retrieval mode.

        Verified-only retrieval requires an explicit VERIFIED status and,
        when persistent storage is configured, at least one persisted VERIFIED
        lifecycle event. A legacy candidate flag without lifecycle evidence is
        never sufficient to enter a verified-only result set.
        """
        status = self._metadata_verification_status(knowledge)

        if status in {"CONFLICTED", "REJECTED", "INVALID"}:
            return False

        if self._metadata_has_unresolved_conflict(knowledge):
            return False

        if not verified_only:
            # Explicit exploratory retrieval may include UNVERIFIED records,
            # but never records explicitly marked conflicted/rejected.
            if self.storage is not None:
                conflict_context = self.storage.knowledge_verification_context(
                    knowledge.knowledge_id
                )
                if isinstance(conflict_context, dict):
                    conflict_status = str(
                        conflict_context.get("conflict_status", "")
                    ).strip().upper()
                    try:
                        unresolved_count = int(
                            conflict_context.get(
                                "unresolved_conflict_count", 0
                            ) or 0
                        )
                    except (TypeError, ValueError):
                        return False
                    conflict_count = int(
                        conflict_context.get("conflict_count", 0) or 0
                    )
                    selected_knowledge_id = conflict_context.get(
                        "selected_knowledge_id"
                    )
                    if (
                        conflict_status in {"UNRESOLVED", "CONFLICTED"}
                        or unresolved_count > 0
                        or (
                            conflict_count > 0
                            and selected_knowledge_id != knowledge.knowledge_id
                        )
                    ):
                        return False
                lifecycle = self.storage.knowledge_verification_lifecycle(
                    knowledge.knowledge_id
                )
                if isinstance(lifecycle, dict) and str(
                    lifecycle.get("verification_status", "")
                ).strip().upper() == "CONFLICTED":
                    return False
            return True

        if not knowledge.verified:
            return False

        # If a status is present, it must agree with the verified flag.
        if status and status != "VERIFIED":
            return False

        if self.storage is not None:
            lifecycle = self.storage.knowledge_verification_lifecycle(
                knowledge.knowledge_id
            )
            if not isinstance(lifecycle, dict):
                return False
            event_count = int(
                lifecycle.get("verification_event_count", 0) or 0
            )
            lifecycle_status = str(
                lifecycle.get("verification_status", "")
            ).strip().upper()
            if event_count <= 0 or lifecycle_status != "VERIFIED":
                return False
        elif (
            status != "VERIFIED"
            or getattr(knowledge, "last_verified_at", None) is None
        ):
            # In-memory candidates have no persisted event store. Require both
            # explicit VERIFIED metadata and a real verification timestamp;
            # the legacy boolean alone is never sufficient.
            return False

        if self.storage is not None:
            conflict_context = self.storage.knowledge_verification_context(
                knowledge.knowledge_id
            )
            if isinstance(conflict_context, dict):
                conflict_status = str(
                    conflict_context.get("conflict_status", "")
                ).strip().upper()
                try:
                    unresolved_count = int(
                        conflict_context.get(
                            "unresolved_conflict_count", 0
                        ) or 0
                    )
                except (TypeError, ValueError):
                    return False
                conflict_count = int(
                    conflict_context.get("conflict_count", 0) or 0
                )
                selected_knowledge_id = conflict_context.get(
                    "selected_knowledge_id"
                )
                if (
                    conflict_status in {"UNRESOLVED", "CONFLICTED"}
                    or unresolved_count > 0
                    or (
                        conflict_count > 0
                        and selected_knowledge_id != knowledge.knowledge_id
                    )
                ):
                    return False

        return True

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
        _include_blocked_for_audit: bool = False,
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
            if (
                not _include_blocked_for_audit
                and not self._passes_verification_gate(
                    knowledge,
                    verified_only=verified_only,
                )
            ):
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
