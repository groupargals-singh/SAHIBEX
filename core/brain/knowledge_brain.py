from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
from uuid import uuid4

from core.research.freshness import assess_query_source_freshness
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

    def _filter_trustworthy_knowledge(
        self,
        knowledge_items: Iterable[KnowledgeCandidate],
        *,
        verified_only: bool,
    ) -> tuple[KnowledgeCandidate, ...]:
        """Apply persisted verification and conflict gates at this boundary.

        The storage query's ``verified`` column is only a candidate flag; it
        must not override newer UNVERIFIED/CONFLICTED lifecycle events or an
        unresolved conflict record. Unverified candidates without a lifecycle
        history may still be listed for review when verified_only is False.
        """
        accepted: list[KnowledgeCandidate] = []
        for item in knowledge_items:
            lifecycle = self.storage.knowledge_verification_lifecycle(
                item.knowledge_id
            )
            status = str(
                lifecycle.get("verification_status", "UNVERIFIED")
            ).strip().upper()
            event_count = int(
                lifecycle.get("verification_event_count", 0) or 0
            )

            # Use the verification-aware context: the lower-level conflict
            # summary does not expose the selected claim ID needed to reject
            # resolved-but-losing candidates.
            conflict_context = self.storage.knowledge_verification_context(
                item.knowledge_id
            )
            if int(conflict_context.get("unresolved_conflict_count", 0) or 0) > 0:
                continue
            conflict_count = int(conflict_context.get("conflict_count", 0) or 0)
            selected_knowledge_id = conflict_context.get("selected_knowledge_id")
            # A resolved conflict authorizes only the selected claim. If the
            # selection is missing/ambiguous, fail closed for every involved
            # candidate instead of trusting the stale verified flag.
            if conflict_count > 0 and selected_knowledge_id != item.knowledge_id:
                continue
            if status == "CONFLICTED":
                continue
            if event_count > 0 and status != "VERIFIED":
                continue
            if verified_only and (
                item.verified is not True
                or event_count == 0
                or status != "VERIFIED"
            ):
                continue
            accepted.append(item)
        return tuple(accepted)

    def _filter_freshness_for_query(
        self,
        query: str,
        knowledge_items: Iterable[KnowledgeCandidate],
    ) -> tuple[KnowledgeCandidate, ...]:
        """Expire stale or provenance-incomplete knowledge for current queries.

        Stable facts remain reusable. Queries explicitly asking for latest,
        current, recent, or today information require persisted supporting
        evidence with trusted publication timestamps inside the query window.
        Missing evidence/source provenance fails closed.
        """
        query_gate = assess_query_source_freshness(query, ())
        if query_gate is None:
            return tuple(knowledge_items)

        accepted: list[KnowledgeCandidate] = []
        for item in knowledge_items:
            sources = {}
            try:
                for evidence_id in item.evidence:
                    evidence = self.storage.get_evidence(str(evidence_id))
                    if evidence is None or evidence.supports is not True:
                        continue
                    source = self.storage.get_source(evidence.source_id)
                    if source is not None:
                        sources[source.source_id] = source
                freshness = assess_query_source_freshness(query, list(sources.values()))
            except Exception:
                # An unreadable provenance record must not rescue stale facts.
                continue
            if freshness is not None and freshness.get("status") == "PASS":
                accepted.append(item)
        return tuple(accepted)

    def retrieve(
        self,
        query: str,
        *,
        verified_only: bool = False,
        min_confidence: float = 0.0,
        freshness_query: str | None = None,
    ) -> KnowledgeRetrievalResult:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string.")
        knowledge = self.storage.retrieve_knowledge(
            query,
            verified_only=verified_only,
            min_confidence=min_confidence,
        )
        knowledge = self._filter_trustworthy_knowledge(
            knowledge,
            verified_only=verified_only,
        )
        knowledge = self._filter_freshness_for_query(
            freshness_query or query,
            knowledge,
        )
        return KnowledgeRetrievalResult(
            success=True,
            query=" ".join(query.strip().split()),
            knowledge=knowledge,
        )

    def get(self, knowledge_id: str) -> KnowledgeCandidate | None:
        if not isinstance(knowledge_id, str) or not knowledge_id.strip():
            raise ValueError("knowledge_id must be a non-empty string.")
        return self.storage.get_knowledge(knowledge_id)

    def list(self, *, verified_only: bool = False) -> tuple[KnowledgeCandidate, ...]:
        knowledge = self.storage.list_knowledge(verified_only=verified_only)
        return self._filter_trustworthy_knowledge(
            knowledge,
            verified_only=verified_only,
        )

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
