from __future__ import annotations

from hashlib import sha256
from typing import Dict, Optional

from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchDocument,
    ResearchFinding,
    ResearchResult,
    ResearchSource,
    new_id,
    utc_now,
)


class ResearchEngine:
    """
    Deterministic research-core engine.

    This first version does not access the Internet.
    It provides the controlled internal research pipeline
    that later Internet/tool connectors will use.
    """

    def __init__(self) -> None:
        self.sources: Dict[str, ResearchSource] = {}
        self.documents: Dict[str, ResearchDocument] = {}
        self.findings: Dict[str, ResearchFinding] = {}
        self.evidence: Dict[str, Evidence] = {}
        self.knowledge: Dict[str, KnowledgeCandidate] = {}

    @staticmethod
    def hash_content(content: str) -> str:
        """
        Create a stable SHA-256 content fingerprint.
        """
        if not content or not content.strip():
            raise ValueError("content cannot be empty")

        normalized = content.strip().encode("utf-8")
        return sha256(normalized).hexdigest()

    def register_source(self, source: ResearchSource) -> ResearchSource:
        """
        Register a research source.
        """
        if source.source_id in self.sources:
            raise ValueError(f"source already exists: {source.source_id}")

        self.sources[source.source_id] = source
        return source

    def add_document(self, document: ResearchDocument) -> ResearchDocument:
        """
        Add a document after ensuring its source exists.
        """
        if document.source_id not in self.sources:
            raise ValueError(
                f"unknown source: {document.source_id}"
            )

        if document.document_id in self.documents:
            raise ValueError(
                f"document already exists: {document.document_id}"
            )

        if not document.content_hash:
            document.content_hash = self.hash_content(document.content)

        self.documents[document.document_id] = document
        return document

    def add_finding(self, finding: ResearchFinding) -> ResearchFinding:
        """
        Add an extracted finding after ensuring its document exists.
        """
        if finding.document_id not in self.documents:
            raise ValueError(
                f"unknown document: {finding.document_id}"
            )

        if finding.finding_id in self.findings:
            raise ValueError(
                f"finding already exists: {finding.finding_id}"
            )

        self.findings[finding.finding_id] = finding
        return finding

    def add_evidence(self, evidence: Evidence) -> Evidence:
        """
        Add evidence after validating finding and source references.
        """
        if evidence.finding_id not in self.findings:
            raise ValueError(
                f"unknown finding: {evidence.finding_id}"
            )

        if evidence.source_id not in self.sources:
            raise ValueError(
                f"unknown source: {evidence.source_id}"
            )

        if evidence.evidence_id in self.evidence:
            raise ValueError(
                f"evidence already exists: {evidence.evidence_id}"
            )

        self.evidence[evidence.evidence_id] = evidence
        return evidence

    def create_knowledge_candidate(
        self,
        statement: str,
        finding_id: str,
        confidence: Optional[float] = None,
    ) -> KnowledgeCandidate:
        """
        Create a knowledge candidate from a finding and its evidence.

        It is not automatically marked verified.
        """

        if finding_id not in self.findings:
            raise ValueError(
                f"unknown finding: {finding_id}"
            )

        finding = self.findings[finding_id]

        related_evidence = [
            item
            for item in self.evidence.values()
            if item.finding_id == finding_id
        ]

        if confidence is None:
            confidence = self._calculate_confidence(
                finding,
                related_evidence,
            )

        candidate = KnowledgeCandidate(
            knowledge_id=new_id("knowledge"),
            statement=statement,
            findings=[finding_id],
            evidence=[
                item.evidence_id
                for item in related_evidence
            ],
            confidence=confidence,
            verified=False,
        )

        self.knowledge[candidate.knowledge_id] = candidate

        return candidate

    @staticmethod
    def _calculate_confidence(
        finding: ResearchFinding,
        evidence: list[Evidence],
    ) -> float:
        """
        Conservative confidence calculation.

        Finding confidence is combined with supporting evidence.
        Contradicting evidence reduces confidence.
        """

        score = finding.confidence

        if not evidence:
            return round(score, 4)

        supporting = [
            item.strength
            for item in evidence
            if item.supports
        ]

        contradicting = [
            item.strength
            for item in evidence
            if not item.supports
        ]

        if supporting:
            support_score = sum(supporting) / len(supporting)
            score = (score + support_score) / 2.0

        if contradicting:
            conflict_score = sum(contradicting) / len(contradicting)
            score -= conflict_score * 0.5

        return round(max(0.0, min(1.0, score)), 4)

    def verify_knowledge(self, knowledge_id: str) -> KnowledgeCandidate:
        """
        Verify a knowledge candidate only when it has evidence.

        This is intentionally conservative.
        """

        if knowledge_id not in self.knowledge:
            raise ValueError(
                f"unknown knowledge: {knowledge_id}"
            )

        candidate = self.knowledge[knowledge_id]

        if not candidate.evidence:
            candidate.verified = False
            return candidate

        evidence_items = [
            self.evidence[item_id]
            for item_id in candidate.evidence
            if item_id in self.evidence
        ]

        if not evidence_items:
            candidate.verified = False
            return candidate

        supporting = [
            item for item in evidence_items
            if item.supports
        ]

        contradicting = [
            item for item in evidence_items
            if not item.supports
        ]

        # Require meaningful support and no equally strong conflict.
        support_strength = max(
            (item.strength for item in supporting),
            default=0.0,
        )

        conflict_strength = max(
            (item.strength for item in contradicting),
            default=0.0,
        )

        candidate.verified = (
            support_strength >= 0.70
            and support_strength > conflict_strength
            and candidate.confidence >= 0.60
        )

        if candidate.verified:
            candidate.last_verified_at = utc_now()

        return candidate

    def create_result(self, query: str) -> ResearchResult:
        """
        Create a snapshot of current research state.
        """

        if not query.strip():
            raise ValueError("query cannot be empty")

        result = ResearchResult(
            research_id=new_id("research"),
            query=query,
            sources=list(self.sources.values()),
            documents=list(self.documents.values()),
            findings=list(self.findings.values()),
            evidence=list(self.evidence.values()),
            knowledge=list(self.knowledge.values()),
            completed=True,
            verified=any(
                item.verified
                for item in self.knowledge.values()
            ),
        )

        return result

    def summary(self) -> dict:
        """
        Return safe non-secret engine statistics.
        """

        return {
            "sources": len(self.sources),
            "documents": len(self.documents),
            "findings": len(self.findings),
            "evidence": len(self.evidence),
            "knowledge_candidates": len(self.knowledge),
            "verified_knowledge": sum(
                1
                for item in self.knowledge.values()
                if item.verified
            ),
        }
