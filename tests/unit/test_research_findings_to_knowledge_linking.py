from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.models import Evidence, ResearchDocument, ResearchFinding, ResearchSource
from core.research.pipeline import ResearchIngestionPipeline


def _setup_pipeline(root: Path) -> ResearchIngestionPipeline:
    pipeline = ResearchIngestionPipeline(root / "finding-knowledge.db")
    source = ResearchSource(
        source_id="source-linking-test",
        title="Linking test source",
        source_type="web",
        locator="https://linking.example.test/report",
        publisher="Linking Test Publisher",
        reliability=0.9,
    )
    document = ResearchDocument(
        document_id="document-linking-test",
        source_id=source.source_id,
        title="Linking test document",
        content="The research finding used for the linking regression test.",
    )
    pipeline.ingest(source, document)
    finding = ResearchFinding(
        finding_id="finding-linking-test",
        document_id=document.document_id,
        claim="The research finding used for the linking regression test.",
        confidence=0.9,
    )
    pipeline.add_finding(finding)
    pipeline.add_evidence(Evidence(
        evidence_id="evidence-selected-weak",
        finding_id=finding.finding_id,
        source_id=source.source_id,
        evidence_text="Selected evidence has low support strength.",
        supports=True,
        strength=0.1,
    ))
    pipeline.add_evidence(Evidence(
        evidence_id="evidence-unselected-strong",
        finding_id=finding.finding_id,
        source_id=source.source_id,
        evidence_text="Unselected evidence has high support strength.",
        supports=True,
        strength=1.0,
    ))
    return pipeline


def test_explicit_evidence_selection_controls_knowledge_confidence():
    with TemporaryDirectory() as temp_dir:
        pipeline = _setup_pipeline(Path(temp_dir))
        try:
            result = pipeline.create_knowledge(
                statement="The research finding used for the linking regression test.",
                finding_ids=["finding-linking-test"],
                evidence_ids=["evidence-selected-weak"],
            )
            candidate = pipeline.engine.knowledge[result.knowledge_id]

            # (finding confidence 0.9 + selected evidence strength 0.1) / 2.
            assert candidate.confidence == 0.5
            assert candidate.findings == ["finding-linking-test"]
            assert candidate.evidence == ["evidence-selected-weak"]
            assert pipeline.engine.evidence["evidence-selected-weak"].metadata[
                "knowledge_id"
            ] == result.knowledge_id
            assert "knowledge_id" not in pipeline.engine.evidence[
                "evidence-unselected-strong"
            ].metadata
        finally:
            pipeline.close()


def test_knowledge_linking_rejects_unknown_finding_without_side_effects():
    with TemporaryDirectory() as temp_dir:
        pipeline = ResearchIngestionPipeline(Path(temp_dir) / "unknown.db")
        try:
            before = len(pipeline.engine.knowledge)
            try:
                pipeline.create_knowledge(
                    statement="Must not be linked.",
                    finding_ids=["missing-finding"],
                )
            except ValueError as exc:
                assert "unknown finding" in str(exc)
            else:
                raise AssertionError("unknown finding should be rejected")
            assert len(pipeline.engine.knowledge) == before
        finally:
            pipeline.close()
