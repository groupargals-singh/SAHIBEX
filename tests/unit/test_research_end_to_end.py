from __future__ import annotations

import tempfile
from pathlib import Path

from core.research.acquisition import (
    AcquisitionRequest,
    AcquisitionResult,
    AcquiredSource,
    ResearchAcquisitionEngine,
    ResearchAcquisitionProvider,
)
from core.research.acquisition_pipeline import (
    ResearchAcquisitionPipeline,
)
from core.research.extractor import (
    ExtractedFinding,
    ResearchExtractor,
)
from core.research.extraction_pipeline import (
    ResearchExtractionPipeline,
)
from core.research.models import ResearchDocument
from core.research.query import ResearchQueryEngine
from core.research.answer_pipeline import ResearchAnswerPipeline
from core.research.aggregator import ResearchResultAggregator


class EndToEndTestProvider(ResearchAcquisitionProvider):
    provider_name = "e2e_test"
    requires_network = False

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        source = AcquiredSource(
            source_id="src-e2e-001",
            title="SAHIBEX End-to-End Research Source",
            source_type="document",
            locator="test://sahibex/e2e",
            publisher="SAHIBEX Test Publisher",
            content=(
                "Research evidence should remain linked "
                "to its source. "
                "Verified knowledge should preserve "
                "its supporting evidence."
            ),
            metadata={
                "reliability": 0.95,
                "collected_at": "2026-09-25T00:00:00+00:00",
                "language": "en",
            },
        )

        return AcquisitionResult(
            query=request.query,
            sources=[source],
            completed=True,
            status="completed",
            metadata={
                "test_provider": True,
            },
        )


class HighConfidenceTestExtractor(ResearchExtractor):
    def extract(
        self,
        document: ResearchDocument,
    ):
        return [
            ExtractedFinding(
                claim=(
                    "Research evidence should remain linked "
                    "to its source."
                ),
                evidence_text=(
                    "Research evidence should remain linked "
                    "to its source."
                ),
                confidence=0.95,
            ),
            ExtractedFinding(
                claim=(
                    "Verified knowledge should preserve "
                    "its supporting evidence."
                ),
                evidence_text=(
                    "Verified knowledge should preserve "
                    "its supporting evidence."
                ),
                confidence=0.95,
            ),
        ]


def test_research_end_to_end() -> None:
    print("SAHIBEX RESEARCH END-TO-END TEST")

    with tempfile.TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "research_e2e.db"

        # ---------------------------------------------------------
        # 1. Acquisition
        # ---------------------------------------------------------

        acquisition_provider = EndToEndTestProvider()

        acquisition_request = AcquisitionRequest(
            query="verified research evidence",
            source_type="document",
            max_sources=5,
        )

        acquisition_result = acquisition_provider.acquire(
            acquisition_request
        )

        assert acquisition_result.completed is True
        assert acquisition_result.status == "completed"
        assert len(acquisition_result.sources) == 1

        acquired_source = acquisition_result.sources[0]

        print("[PASS] acquisition")

        # ---------------------------------------------------------
        # 2. Acquisition safety boundary
        # ---------------------------------------------------------

        assert acquisition_provider.requires_network is False

        print("[PASS] acquisition safety boundary")

        # ---------------------------------------------------------
        # 3. Acquisition engine
        # ---------------------------------------------------------

        acquisition_engine = ResearchAcquisitionEngine(
            providers=[
                acquisition_provider,
            ]
        )

        assert "e2e_test" in acquisition_engine.providers()

        # ---------------------------------------------------------
        # 4. Acquisition → ingestion
        # ---------------------------------------------------------

        acquisition_pipeline = ResearchAcquisitionPipeline(
            database_path,
            acquisition_engine,
        )

        acquired_ingestion = (
            acquisition_pipeline.acquire_and_ingest(
                acquisition_request,
                provider_name="e2e_test",
            )
        )

        assert acquired_ingestion is not None
        assert acquired_ingestion.stored_count == 1
        assert acquired_ingestion.duplicate_count == 0
        assert len(acquired_ingestion.ingested) == 1

        ingestion_result = acquired_ingestion.ingested[0]

        assert ingestion_result.document_stored is True
        assert ingestion_result.duplicate is False

        document_id = ingestion_result.document_id

        print("[PASS] document ingestion")

        # ---------------------------------------------------------
        # 5. Retrieve document
        # ---------------------------------------------------------

        ingestion_pipeline = (
            acquisition_pipeline.ingestion_pipeline
        )

        research_engine = ingestion_pipeline.engine

        document = research_engine.documents.get(
            document_id
        )

        assert document is not None
        assert document.document_id == document_id
        assert (
            document.source_id
            == acquired_source.source_id
        )
        assert document.content.strip()

        # ---------------------------------------------------------
        # 6. Extraction
        # ---------------------------------------------------------

        extraction_pipeline = ResearchExtractionPipeline(
            ingestion_pipeline,
            extractor=HighConfidenceTestExtractor(),
        )

        extraction_result = (
            extraction_pipeline.extract_document(
                document
            )
        )

        assert (
            extraction_result.document_id
            == document_id
        )
        assert (
            extraction_result.source_id
            == acquired_source.source_id
        )
        assert extraction_result.extracted_count == 2
        assert len(extraction_result.findings) == 2

        print("[PASS] extraction")

        # ---------------------------------------------------------
        # 7. Finding creation
        # ---------------------------------------------------------

        for item in extraction_result.findings:
            finding = research_engine.findings.get(
                item.finding_id
            )

            assert finding is not None
            assert (
                finding.document_id
                == document_id
            )
            assert finding.claim
            assert finding.confidence == 0.95

        print("[PASS] finding creation")

        # ---------------------------------------------------------
        # 8. Evidence creation
        # ---------------------------------------------------------

        for item in extraction_result.findings:
            evidence = research_engine.evidence.get(
                item.evidence_id
            )

            assert evidence is not None
            assert (
                evidence.finding_id
                == item.finding_id
            )
            assert (
                evidence.source_id
                == acquired_source.source_id
            )
            assert evidence.supports is True
            assert evidence.strength == evidence.metadata["evidence_strength"]["strength_score"]
            assert 0.0 <= evidence.strength <= 1.0

        print("[PASS] evidence creation")

        # ---------------------------------------------------------
        # 9. Knowledge creation
        # ---------------------------------------------------------

        knowledge_items = []

        for item in extraction_result.findings:
            finding = research_engine.findings[
                item.finding_id
            ]

            knowledge_result = (
                ingestion_pipeline.create_knowledge(
                    statement=finding.claim,
                    finding_ids=[
                        item.finding_id
                    ],
                    evidence_ids=[
                        item.evidence_id
                    ],
                )
            )

            assert knowledge_result.stored is True
            assert knowledge_result.knowledge_id

            knowledge = research_engine.knowledge.get(
                knowledge_result.knowledge_id
            )

            assert knowledge is not None
            assert (
                knowledge.statement
                == finding.claim
            )

            knowledge_items.append(knowledge)

        assert len(knowledge_items) == 2

        print("[PASS] knowledge creation")

        # ---------------------------------------------------------
        # 10. Knowledge verification
        # ---------------------------------------------------------

        for knowledge in knowledge_items:
            assert knowledge.verified is False
            assert knowledge.metadata.get("verification_status") == "UNVERIFIED"
            assert knowledge.confidence >= 0.60

        print("[PASS] knowledge verification")

        # ---------------------------------------------------------
        # 11. Persistent knowledge
        # ---------------------------------------------------------

        for knowledge in knowledge_items:
            stored_knowledge = (
                ingestion_pipeline.storage.get_knowledge(
                    knowledge.knowledge_id
                )
            )

            assert stored_knowledge is not None
            assert (
                stored_knowledge.knowledge_id
                == knowledge.knowledge_id
            )
            assert stored_knowledge.verified is False
            assert stored_knowledge.metadata.get("verification_status") == "UNVERIFIED"

        print("[PASS] persistent knowledge")

        # ---------------------------------------------------------
        # 12. Query retrieval
        # ---------------------------------------------------------

        query_engine = ResearchQueryEngine(
            research_engine
        )

        query_result = query_engine.search(
            "verified knowledge supporting evidence",
            verified_only=False,
            limit=10,
        )

        assert query_result is not None
        assert query_result.total_matches >= 1
        assert len(query_result.matches) >= 1

        print("[PASS] query retrieval")

        # ---------------------------------------------------------
        # 13. Knowledge aggregation
        # ---------------------------------------------------------

        aggregator = ResearchResultAggregator()

        aggregation_result = aggregator.aggregate(
            query_result.matches,
            evidence_items=list(
                research_engine.evidence.values()
            ),
            sources=list(
                research_engine.sources.values()
            ),
            verified_only=False,
        )

        assert aggregation_result is not None
        assert aggregation_result.verified_count == 0
        assert (
            len(aggregation_result.results)
            >= 1
        )

        print("[PASS] knowledge aggregation")

        # ---------------------------------------------------------
        # 14. Answer synthesis
        # ---------------------------------------------------------

        answer_pipeline = ResearchAnswerPipeline(
            ResearchQueryEngine(research_engine)
        )

        answer_result = answer_pipeline.run(
            query=(
                "verified knowledge supporting evidence"
            ),
            verified_only=False,
            limit=10,
            evidence_items=list(
                research_engine.evidence.values()
            ),
            sources=list(
                research_engine.sources.values()
            ),
        )

        assert answer_result is not None
        assert answer_result.answer is not None
        assert answer_result.answer.answer
        # Verification of stored knowledge alone cannot override a stale or
        # low-confidence quality-aware answer assessment.
        assert answer_result.answer.verified is False
        assert answer_result.answer.status != "VERIFIED"
        assert answer_result.aggregation.answer.overall_status in {
            "STALE",
            "LOW_CONFIDENCE",
            "UNCERTAIN",
            "UNVERIFIED",
        }
        assert answer_result.answer.confidence >= 0.60

        print("[PASS] answer synthesis preserves quality gate")

        # ---------------------------------------------------------
        # 15. Answer verification
        # ---------------------------------------------------------

        assert answer_result.answer.status
        assert len(
        answer_result.answer.knowledge_ids
       ) >= 1

        print("[PASS] answer verification")

        # ---------------------------------------------------------
        # 16. Traceability
        # ---------------------------------------------------------

        trace = answer_result.traceability

        assert trace is not None
        assert trace.knowledge_count >= 1
        assert trace.evidence_count >= 1
        assert trace.source_count >= 1
        assert len(trace.traces) >= 1

        print("[PASS] traceability")

        # ---------------------------------------------------------
        # 17. Source traceability
        # ---------------------------------------------------------

        source_id = acquired_source.source_id

        assert any(
            source.source_id == source_id
            for knowledge_trace in trace.traces
            for source in knowledge_trace.sources
        )

        traced_knowledge_ids = {
            knowledge_trace.knowledge_id
            for knowledge_trace in trace.traces
        }

        acquired_knowledge_ids = {
            knowledge.knowledge_id
            for knowledge in knowledge_items
        }

        assert (
            traced_knowledge_ids
            & acquired_knowledge_ids
        )

        print("[PASS] source traceability")

        # ---------------------------------------------------------
        # 18. Duplicate protection
        # ---------------------------------------------------------

        duplicate_acquisition = (
            acquisition_pipeline.acquire_and_ingest(
                acquisition_request,
                provider_name="e2e_test",
            )
        )

        assert duplicate_acquisition is not None
        assert (
            duplicate_acquisition.stored_count
            == 0
        )
        assert (
            duplicate_acquisition.duplicate_count
            >= 1
        )
        assert len(
            duplicate_acquisition.ingested
        ) == 1

        duplicate_result = (
            duplicate_acquisition.ingested[0]
        )

        assert duplicate_result.duplicate is True
        assert (
            duplicate_result.document_stored
            is False
        )
        assert (
            duplicate_result.matched_document_id
            == document_id
        )

        print("[PASS] duplicate protection")

        # ---------------------------------------------------------
        # Cleanup
        # ---------------------------------------------------------

        acquisition_pipeline.close()

    print("SAHIBEX RESEARCH END-TO-END TEST: PASS")


if __name__ == "__main__":
    test_research_end_to_end()
