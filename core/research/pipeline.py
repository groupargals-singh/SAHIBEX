from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.research.deduplication import DocumentDeduplicator
from core.research.engine import ResearchEngine
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchDocument,
    ResearchFinding,
    ResearchSource,
)
from core.research.source_registry import SourceRegistry
from core.research.storage import ResearchStorage


@dataclass(frozen=True)
class IngestionResult:
    source_id: str
    document_id: str
    source_registered: bool
    document_stored: bool
    duplicate: bool
    matched_document_id: Optional[str]
    content_hash: str


@dataclass(frozen=True)
class FindingResult:
    finding_id: str
    document_id: str
    stored: bool


@dataclass(frozen=True)
class EvidenceResult:
    evidence_id: str
    finding_id: str
    source_id: str
    stored: bool


@dataclass(frozen=True)
class KnowledgeResult:
    knowledge_id: str
    verified: bool
    confidence: float
    stored: bool


class ResearchIngestionPipeline:
    """
    Controlled research pipeline.

    Source/document flow:

        Source
          ↓
        Registry
          ↓
        Deduplication
          ↓
        Persistent Storage
          ↓
        Research Engine

    Evidence flow:

        Document
          ↓
        Finding
          ↓
        Evidence
          ↓
        Knowledge Candidate
          ↓
        Verification
          ↓
        Persistent Storage
    """

    def __init__(
        self,
        database_path: Path | str,
        *,
        source_registry: Optional[SourceRegistry] = None,
        deduplicator: Optional[DocumentDeduplicator] = None,
        engine: Optional[ResearchEngine] = None,
    ) -> None:
        self.registry = (
            source_registry
            if source_registry is not None
            else SourceRegistry()
        )

        self.deduplicator = (
            deduplicator
            if deduplicator is not None
            else DocumentDeduplicator()
        )

        self.engine = (
            engine
            if engine is not None
            else ResearchEngine()
        )

        self.storage = ResearchStorage(database_path)

    def _ensure_engine_registration(
        self,
        *,
        source: ResearchSource,
        document: ResearchDocument,
    ) -> None:
        """
        Rehydrate persisted research objects into the runtime engine.

        Persistent storage is authoritative across pipeline restarts,
        while ResearchEngine owns the current in-memory execution state.
        Duplicate ingestion must therefore restore the matching source
        and document into the engine before downstream extraction.
        """
        if source.source_id not in self.engine.sources:
            self.engine.register_source(source)

        if document.document_id not in self.engine.documents:
            self.engine.add_document(document)

    def ingest(
        self,
        source: ResearchSource,
        document: ResearchDocument,
    ) -> IngestionResult:
        if document.source_id != source.source_id:
            raise ValueError(
                "document.source_id must match source.source_id"
            )

        source_result = self.registry.register(source)

        stored_source = self.storage.get_source(
            source.source_id
        )

        if stored_source is None:
            self.storage.save_source(source)

        dedup_result = self.deduplicator.check(
            document.document_id,
            document.content,
        )

        persistent_match = self.storage.find_document_by_hash(
            document.content_hash
        )

        if persistent_match is not None:
            self._ensure_engine_registration(
                source=source,
                document=persistent_match,
            )

            return IngestionResult(
                source_id=source.source_id,
                document_id=document.document_id,
                source_registered=source_result.is_new,
                document_stored=False,
                duplicate=True,
                matched_document_id=persistent_match.document_id,
                content_hash=document.content_hash,
            )

        if dedup_result.is_duplicate:
            return IngestionResult(
                source_id=source.source_id,
                document_id=document.document_id,
                source_registered=source_result.is_new,
                document_stored=False,
                duplicate=True,
                matched_document_id=dedup_result.matched_document_id,
                content_hash=document.content_hash,
            )

        self.storage.save_document(document)

        self.deduplicator.register(
            document.document_id,
            document.content,
        )

        self.engine.register_source(source)
        self.engine.add_document(document)

        return IngestionResult(
            source_id=source.source_id,
            document_id=document.document_id,
            source_registered=source_result.is_new,
            document_stored=True,
            duplicate=False,
            matched_document_id=None,
            content_hash=document.content_hash,
        )

    def add_finding(
        self,
        finding: ResearchFinding,
    ) -> FindingResult:
        document = self.engine.documents.get(
            finding.document_id
        )

        if document is None:
            raise KeyError(
                f"Unknown document: {finding.document_id}"
            )

        self.engine.add_finding(finding)
        self.storage.save_finding(finding)

        return FindingResult(
            finding_id=finding.finding_id,
            document_id=finding.document_id,
            stored=True,
        )

    def add_evidence(
        self,
        evidence: Evidence,
    ) -> EvidenceResult:
        finding = self.engine.findings.get(
            evidence.finding_id
        )

        if finding is None:
            raise KeyError(
                f"Unknown finding: {evidence.finding_id}"
            )

        source = self.engine.sources.get(
            evidence.source_id
        )

        if source is None:
            raise KeyError(
                f"Unknown source: {evidence.source_id}"
            )

        self.engine.add_evidence(evidence)
        self.storage.save_evidence(evidence)

        return EvidenceResult(
            evidence_id=evidence.evidence_id,
            finding_id=evidence.finding_id,
            source_id=evidence.source_id,
            stored=True,
        )

    def create_knowledge(
        self,
        statement: str,
        finding_ids: list[str],
        evidence_ids: list[str] | None = None,
        confidence: float | None = None,
    ) -> KnowledgeResult:
        """
        Create, link, verify, and persist a knowledge candidate.

        Knowledge is created from a finding and its related evidence.

        After the knowledge ID exists, the supporting evidence is explicitly
        linked back to that knowledge through:

            evidence.metadata["knowledge_id"]

        This creates the bidirectional relationship needed by downstream
        answer synthesis and traceability:

            Knowledge -> Evidence -> Source
        """

        if not finding_ids:
            raise ValueError(
                "At least one finding_id is required."
            )

        finding_id = finding_ids[0]

        knowledge = self.engine.create_knowledge_candidate(
            statement=statement,
            finding_id=finding_id,
            confidence=confidence,
        )

        # ---------------------------------------------------------
        # Link the evidence used by this knowledge candidate
        # back to the generated knowledge ID.
        # ---------------------------------------------------------

        selected_evidence_ids = (
            list(evidence_ids)
            if evidence_ids is not None
            else list(knowledge.evidence)
        )

        for evidence_id in selected_evidence_ids:
            evidence = self.engine.evidence.get(
                evidence_id
            )

            if evidence is None:
                raise KeyError(
                    f"Unknown evidence: {evidence_id}"
                )

            evidence.metadata["knowledge_id"] = (
                knowledge.knowledge_id
            )

            self.storage.save_evidence(evidence)

        # Refresh the knowledge object from the engine.
        knowledge = self.engine.knowledge[
            knowledge.knowledge_id
        ]

        # ---------------------------------------------------------
        # Verify knowledge using the existing ResearchEngine
        # verification authority.
        # ---------------------------------------------------------

        verified = self.engine.verify_knowledge(
            knowledge.knowledge_id
        )

        knowledge = self.engine.knowledge[
            knowledge.knowledge_id
        ]

        # ---------------------------------------------------------
        # Persist the final knowledge state.
        # ---------------------------------------------------------

        self.storage.save_knowledge(knowledge)

        return KnowledgeResult(
            knowledge_id=knowledge.knowledge_id,
            verified=verified,
            confidence=knowledge.confidence,
            stored=True,
        )

    def close(self) -> None:
        self.storage.close()

    def __enter__(self) -> "ResearchIngestionPipeline":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()
