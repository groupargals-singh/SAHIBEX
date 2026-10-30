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
    utc_now,
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
        # The incoming source may be a duplicate URL/content candidate while
        # the canonical persisted document belongs to an earlier source ID.
        # Register both identities before restoring the canonical document;
        # otherwise ResearchEngine.add_document raises "unknown source" after
        # a valid persistent deduplication match.
        if source.source_id not in self.engine.sources:
            self.engine.register_source(source)

        document_source_id = document.source_id
        if document_source_id not in self.engine.sources:
            canonical_source = self.storage.get_source(document_source_id)
            if canonical_source is None and document_source_id == source.source_id:
                canonical_source = source
            if canonical_source is None:
                raise ValueError(
                    "canonical document source is missing from persistent storage: "
                    f"{document_source_id}"
                )
            self.engine.register_source(canonical_source)

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

        # Canonicalize the content fingerprint before deduplication or any
        # persistent writes. A missing hash is filled in; a caller-supplied
        # mismatched hash is rejected so it cannot spoof document identity.
        expected_hash = ResearchEngine.hash_content(document.content)
        if not document.content_hash:
            document.content_hash = expected_hash
        elif document.content_hash != expected_hash:
            raise ValueError(
                "document.content_hash does not match document content"
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
        Create, link, verify, and persist a knowledge candidate
        from multiple findings and their evidence.
        """
        if not finding_ids:
            raise ValueError(
                "At least one finding_id is required."
            )

        normalized_ids = list(dict.fromkeys(finding_ids))

        for finding_id in normalized_ids:
            if finding_id not in self.engine.findings:
                raise ValueError(f"unknown finding: {finding_id}")

        selected_evidence_ids = (
            list(dict.fromkeys(evidence_ids))
            if evidence_ids is not None
            else None
        )

        # Validate all explicitly selected evidence before creating
        # a candidate or modifying stored metadata.
        if selected_evidence_ids is not None:
            # Validate existence and finding linkage for the complete set
            # before checking ownership. This keeps malformed requests from
            # being masked by an earlier evidence-ownership error.
            for evidence_id in selected_evidence_ids:
                evidence = self.engine.evidence.get(evidence_id)
                if evidence is None:
                    raise KeyError(
                        f"Unknown evidence: {evidence_id}"
                    )
                if evidence.finding_id not in normalized_ids:
                    raise ValueError(
                        f"Evidence {evidence_id} does not belong "
                        "to the supplied findings."
                    )

            for evidence_id in selected_evidence_ids:
                evidence = self.engine.evidence[evidence_id]
                linked_knowledge_id = (evidence.metadata or {}).get(
                    "knowledge_id"
                )
                if linked_knowledge_id:
                    raise ValueError(
                        f"Evidence {evidence_id} is already linked to "
                        f"knowledge candidate {linked_knowledge_id}."
                    )

        knowledge = self.engine.create_knowledge_candidate(
            statement=statement,
            finding_ids=normalized_ids,
            confidence=confidence,
        )

        if selected_evidence_ids is None:
            selected_evidence_ids = list(knowledge.evidence)
        else:
            # Keep candidate evidence aligned with the explicitly
            # selected evidence used by this knowledge record.
            knowledge.evidence = selected_evidence_ids

        # The engine initially estimates confidence from every unlinked
        # evidence item attached to the findings. If this call explicitly
        # selected a subset, that estimate can include evidence which is
        # not actually linked to this candidate. Recompute against the
        # exact candidate evidence set so unselected evidence cannot inflate
        # confidence or affect later verification decisions.
        if confidence is None and evidence_ids is not None:
            evidence_by_finding: dict[str, list[Evidence]] = {
                finding_id: [] for finding_id in normalized_ids
            }
            for evidence_id in selected_evidence_ids:
                selected_evidence = self.engine.evidence[evidence_id]
                evidence_by_finding[selected_evidence.finding_id].append(
                    selected_evidence
                )

            finding_scores = [
                self.engine._calculate_confidence(
                    self.engine.findings[finding_id],
                    evidence_by_finding[finding_id],
                )
                for finding_id in normalized_ids
            ]
            knowledge.confidence = round(
                sum(finding_scores) / len(finding_scores),
                4,
            )

        for evidence_id in selected_evidence_ids:
            evidence = self.engine.evidence[evidence_id]
            evidence.metadata["knowledge_id"] = knowledge.knowledge_id
            self.storage.save_evidence(evidence)

        self.engine.verify_knowledge(knowledge.knowledge_id)
        knowledge = self.engine.knowledge[knowledge.knowledge_id]
        self.storage.save_knowledge(knowledge)

        # Record the outcome; inconsistent or missing status fails closed.
        raw_status = str(
            knowledge.metadata.get("verification_status", "UNVERIFIED")
        ).upper()

        if raw_status == "CONFLICTED":
            verification_status = "CONFLICTED"
        elif raw_status == "VERIFIED" and knowledge.verified:
            verification_status = "VERIFIED"
        else:
            verification_status = "UNVERIFIED"

        reason = str(
            knowledge.metadata.get("verification_reason", "")
        ).strip()
        if not reason:
            reason = f"Research verification outcome: {verification_status}."

        self.storage.record_knowledge_verification(
            knowledge_id=knowledge.knowledge_id,
            status=verification_status,
            reason=reason,
            verified_at=knowledge.last_verified_at or utc_now(),
            metadata={
                "candidate_verified": bool(knowledge.verified),
                "confidence": knowledge.confidence,
                "agreement_version": knowledge.metadata.get("agreement_version"),
                "independent_source_count": knowledge.metadata.get(
                    "independent_source_count", 0
                ),
                "supporting_source_count": knowledge.metadata.get(
                    "supporting_source_count", 0
                ),
                "contradicting_source_count": knowledge.metadata.get(
                    "contradicting_source_count", 0
                ),
            },
        )

        return KnowledgeResult(
            knowledge_id=knowledge.knowledge_id,
            verified=knowledge.verified,
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
