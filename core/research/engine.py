from __future__ import annotations

from hashlib import sha256
from typing import Dict, Optional
from core.research.agreement import (
    AGREEMENT_VERSION,
    _source_groups,
    assess_multi_source_agreement,
)

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

        expected_hash = self.hash_content(document.content)
        if not document.content_hash:
            document.content_hash = expected_hash
        elif document.content_hash != expected_hash:
            raise ValueError(
                "document.content_hash does not match document content"
            )

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

        # Evidence provenance must match the source of the document from
        # which its finding was extracted. Otherwise a caller could attach
        # one finding to an unrelated publisher and falsely inflate the
        # independent-source agreement count.
        finding = self.findings[evidence.finding_id]
        document = self.documents.get(finding.document_id)
        if document is None:
            raise ValueError(
                f"unknown document for finding: {finding.finding_id}"
            )
        if evidence.source_id != document.source_id:
            raise ValueError(
                "evidence.source_id does not match the finding document source"
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
        finding_id: Optional[str] = None,
        confidence: Optional[float] = None,
        *,
        finding_ids: Optional[list[str]] = None,
    ) -> KnowledgeCandidate:
        """
        Create an unverified knowledge candidate from one or more findings.
        Supports the legacy finding_id argument.
        """
        if finding_ids is not None and finding_id is not None:
            raise ValueError(
                "Pass finding_id or finding_ids, not both."
            )

        requested_ids = (
            finding_ids if finding_ids is not None
            else ([finding_id] if finding_id is not None else [])
        )

        normalized_ids = list(dict.fromkeys(requested_ids))
        if not normalized_ids:
            raise ValueError("At least one finding_id is required.")

        unknown_ids = [
            item for item in normalized_ids
            if item not in self.findings
        ]
        if unknown_ids:
            raise ValueError(
                f"unknown finding: {unknown_ids[0]}"
            )

        # Evidence already assigned to another knowledge candidate must
        # not be silently reused. Metadata stores a single knowledge_id, so
        # reuse would invalidate the previous candidate's provenance.
        related_evidence = [
            item for item in self.evidence.values()
            if item.finding_id in normalized_ids
            and not (item.metadata or {}).get("knowledge_id")
        ]

        if confidence is None:
            scores = []
            for current_id in normalized_ids:
                current_finding = self.findings[current_id]
                current_evidence = [
                    item for item in related_evidence
                    if item.finding_id == current_id
                ]
                scores.append(
                    self._calculate_confidence(
                        current_finding,
                        current_evidence,
                    )
                )
            confidence = sum(scores) / len(scores)

        candidate = KnowledgeCandidate(
            knowledge_id=new_id("knowledge"),
            statement=statement,
            findings=normalized_ids,
            evidence=[
                item.evidence_id for item in related_evidence
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
        """Verify knowledge using evidence and independent source agreement."""
        if knowledge_id not in self.knowledge:
            raise ValueError(f"unknown knowledge: {knowledge_id}")

        candidate = self.knowledge[knowledge_id]

        # Never retain stale verification results or source counts.
        candidate.verified = False
        candidate.last_verified_at = None
        candidate.metadata["verification_status"] = "UNVERIFIED"
        candidate.metadata["verification_reason"] = (
            "Insufficient independent supporting sources."
        )
        candidate.metadata["agreement_version"] = AGREEMENT_VERSION
        candidate.metadata["independent_source_count"] = 0
        candidate.metadata["supporting_source_count"] = 0
        candidate.metadata["strong_supporting_source_count"] = 0
        candidate.metadata["contradicting_source_count"] = 0
        candidate.metadata["agreement_score"] = 0.0

        evidence_items = []

        for evidence_id in candidate.evidence:
            evidence = self.evidence.get(evidence_id)
            if evidence is None:
                continue

            # Evidence must belong to one of this candidate's findings.
            if evidence.finding_id not in candidate.findings:
                continue

            # Do not silently reassign evidence already linked elsewhere.
            linked_id = (evidence.metadata or {}).get("knowledge_id")
            if linked_id not in (None, knowledge_id):
                continue

            evidence.metadata["knowledge_id"] = knowledge_id
            evidence_items.append(evidence)

        candidate.metadata["verification_status"] = "UNVERIFIED"
        candidate.metadata["verification_reason"] = (
            "Insufficient independent supporting sources."
        )

        if not evidence_items:
            candidate.metadata["verification_reason"] = (
                "No valid evidence is linked to this candidate."
            )
            return candidate

        supporting = [
            item for item in evidence_items if item.supports
        ]
        contradicting = [
            item for item in evidence_items if not item.supports
        ]

        # Strength must be evaluated per independent source group. A strong
        # article from one publisher must not make a weak second publisher
        # look independently verified. Unidentifiable sources cannot boost
        # support strength because they are excluded from source grouping.
        source_groups = _source_groups(self.sources.values())
        support_strength_by_group: dict[str, float] = {}
        for item in supporting:
            group_id = source_groups.get(item.source_id)
            if group_id is None:
                continue
            support_strength_by_group[group_id] = max(
                support_strength_by_group.get(group_id, 0.0),
                item.strength,
            )

        support_strength = max(
            support_strength_by_group.values(),
            default=0.0,
        )
        strong_supporting_source_count = sum(
            strength >= 0.70
            for strength in support_strength_by_group.values()
        )
        conflict_strength = max(
            (item.strength for item in contradicting),
            default=0.0,
        )

        assessment = assess_multi_source_agreement(
            knowledge=candidate,
            evidence_items=evidence_items,
            sources=list(self.sources.values()),
        )

        candidate.metadata["agreement_version"] = assessment.version
        candidate.metadata["independent_source_count"] = (
            assessment.total_source_count
        )
        candidate.metadata["supporting_source_count"] = (
            assessment.supporting_source_count
        )
        candidate.metadata["strong_supporting_source_count"] = (
            strong_supporting_source_count
        )
        candidate.metadata["contradicting_source_count"] = (
            assessment.contradicting_source_count
        )
        candidate.metadata["agreement_score"] = (
            assessment.agreement_score
        )

        # Conflicting source groups require further review.
        if assessment.contradicting_source_count > 0:
            candidate.metadata["verification_status"] = "CONFLICTED"
            candidate.metadata["verification_reason"] = (
                "Contradictory source evidence requires review."
            )
            return candidate

        if assessment.supporting_source_count < 2:
            candidate.metadata["verification_reason"] = (
                "At least two independent supporting source groups "
                "are required."
            )
            return candidate

        if assessment.total_source_count < 2:
            candidate.metadata["verification_reason"] = (
                "Independent source corroboration is insufficient."
            )
            return candidate

        if strong_supporting_source_count < 2:
            candidate.metadata["verification_reason"] = (
                "At least two independent source groups must each have "
                "supporting evidence strength of 0.70 or higher."
            )
            return candidate

        if conflict_strength >= support_strength:
            candidate.metadata["verification_status"] = "CONFLICTED"
            candidate.metadata["verification_reason"] = (
                "Contradictory evidence is as strong as or stronger "
                "than supporting evidence."
            )
            return candidate

        if candidate.confidence < 0.60:
            candidate.metadata["verification_reason"] = (
                "Candidate confidence is below 0.60."
            )
            return candidate

        candidate.verified = True
        candidate.last_verified_at = utc_now()
        candidate.metadata["verification_status"] = "VERIFIED"
        candidate.metadata["verification_reason"] = (
            "Independent supporting sources passed the verification "
            "checks with no identified contradictory source group."
        )

        return candidate

    def create_result(self, query: str) -> ResearchResult:
        """
        Create a snapshot of current research state.
        """

        if not query.strip():
            raise ValueError("query cannot be empty")
        for knowledge_id in list(self.knowledge):
            self.verify_knowledge(knowledge_id)

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
