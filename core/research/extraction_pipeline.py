from __future__ import annotations

from dataclasses import dataclass
from typing import List

from core.research.extractor import ExtractedFinding, ResearchExtractor
from core.research.models import (
    Evidence,
    ResearchDocument,
    ResearchFinding,
    new_id,
    utc_now,
)
from core.research.pipeline import ResearchIngestionPipeline
from core.research.evidence_strength import (
    assess_evidence_strength,
)

@dataclass(frozen=True)
class ExtractedFindingResult:
    finding_id: str
    evidence_id: str
    document_id: str
    source_id: str
    finding_stored: bool
    evidence_stored: bool


@dataclass(frozen=True)
class ExtractionPipelineResult:
    document_id: str
    source_id: str
    extracted_count: int
    findings: List[ExtractedFindingResult]


class ResearchExtractionPipeline:
    """
    Controlled bridge from document extraction into the
    existing research finding/evidence/knowledge pipeline.

    Flow:

        ResearchDocument
              ↓
        ResearchExtractor
              ↓
        ExtractedFinding
              ↓
        ResearchFinding
              ↓
        Evidence
              ↓
        Knowledge Candidate
              ↓
        Existing Verification Engine

    This class does not implement independent truth verification.
    Verification authority remains inside ResearchEngine.
    """

    def __init__(
        self,
        pipeline: ResearchIngestionPipeline,
        *,
        extractor: ResearchExtractor | None = None,
    ) -> None:
        if not isinstance(pipeline, ResearchIngestionPipeline):
            raise TypeError(
                "pipeline must be a ResearchIngestionPipeline"
            )

        self.pipeline = pipeline
        self.extractor = (
            extractor
            if extractor is not None
            else ResearchExtractor()
        )

    def extract_document(
        self,
        document: ResearchDocument,
    ) -> ExtractionPipelineResult:
        """
        Extract candidate findings and store their evidence.

        This method does NOT create knowledge.
        """
        if not isinstance(document, ResearchDocument):
            raise TypeError(
                "document must be a ResearchDocument"
            )

        registered_document = self.pipeline.engine.documents.get(
            document.document_id
        )
        if registered_document is None:
            raise KeyError(
                f"Unknown document: {document.document_id}"
            )

        # A matching document ID is not sufficient proof of identity: callers
        # can construct a second object with the same ID but different content
        # or source. Always bind extraction to the canonical ingested document.
        if document.source_id != registered_document.source_id:
            raise ValueError(
                "document.source_id does not match the registered document"
            )
        if document.content != registered_document.content:
            raise ValueError(
                "document content does not match the registered document"
            )

        # Use the engine's canonical instance for downstream processing.
        document = registered_document
        source_id = document.source_id

        if source_id not in self.pipeline.engine.sources:
            raise KeyError(
                f"Unknown source: {source_id}"
            )

        extracted = self.extractor.extract(document)

        results: List[ExtractedFindingResult] = []

        for item in extracted:
            finding = self._build_finding(
                document=document,
                extracted=item,
            )

            finding_result = self.pipeline.add_finding(
                finding
            )

            evidence = self._build_evidence(
                finding=finding,
                source_id=source_id,
                extracted=item,
            )

            source = self.pipeline.engine.sources.get(
                source_id
            )

            if source is None:
                raise KeyError(
                    f"Unknown source: {source_id}"
                )

            strength_assessment = assess_evidence_strength(
                evidence=evidence,
                finding=finding,
                source=source,
            )

            # Persist the canonical structural evidence-strength score
            # used by ResearchEngine verification. This remains a
            # structural evidence score, not a truth claim.
            evidence.strength = strength_assessment.strength_score
            evidence.metadata["evidence_strength"] = {
                "strength_score": strength_assessment.strength_score,
                "directness_score": (
                    strength_assessment.directness_score
                ),
                "specificity_score": (
                    strength_assessment.specificity_score
                ),
                "finding_linkage_score": (
                    strength_assessment.finding_linkage_score
                ),
                "source_linkage_score": (
                    strength_assessment.source_linkage_score
                ),
                "extraction_confidence_score": (
                    strength_assessment.extraction_confidence_score
                ),
                "version": strength_assessment.version,
            }

            evidence_result = self.pipeline.add_evidence(
                evidence
            )

            results.append(
                ExtractedFindingResult(
                    finding_id=finding_result.finding_id,
                    evidence_id=evidence_result.evidence_id,
                    document_id=document.document_id,
                    source_id=source_id,
                    finding_stored=finding_result.stored,
                    evidence_stored=evidence_result.stored,
                )
            )

        return ExtractionPipelineResult(
            document_id=document.document_id,
            source_id=source_id,
            extracted_count=len(extracted),
            findings=results,
        )

    def extract_and_verify(
        self,
        document: ResearchDocument,
    ) -> ExtractionPipelineResult:
        """
        Extract findings and evidence, then create and verify
        knowledge through the existing research pipeline.

        The method deliberately delegates knowledge creation and
        verification to ResearchIngestionPipeline.create_knowledge().
        """
        result = self.extract_document(document)

        for item in result.findings:
            finding = self.pipeline.engine.findings[
                item.finding_id
            ]

            self.pipeline.create_knowledge(
                statement=finding.claim,
                finding_ids=[item.finding_id],
                evidence_ids=[item.evidence_id],
            )

        return result

    @staticmethod
    def _build_finding(
        *,
        document: ResearchDocument,
        extracted: ExtractedFinding,
    ) -> ResearchFinding:
        return ResearchFinding(
            finding_id=new_id("finding"),
            document_id=document.document_id,
            claim=extracted.claim,
            evidence_text=extracted.evidence_text,
            confidence=extracted.confidence,
            created_at=utc_now(),
            metadata={
                "extraction": True,
                "extractor": "ResearchExtractor",
                "truncated": extracted.truncated,
            },
        )

    @staticmethod
    def _build_evidence(
        *,
        finding: ResearchFinding,
        source_id: str,
        extracted: ExtractedFinding,
    ) -> Evidence:
        return Evidence(
            evidence_id=new_id("evidence"),
            finding_id=finding.finding_id,
            source_id=source_id,
            evidence_text=extracted.evidence_text,
            supports=True,
            strength=extracted.confidence,
            created_at=utc_now(),
            metadata={
                "extraction": True,
                "finding_id": finding.finding_id,
            },
        )
