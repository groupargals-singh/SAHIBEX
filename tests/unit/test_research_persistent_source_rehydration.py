from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.models import ResearchDocument, ResearchSource
from core.research.pipeline import ResearchIngestionPipeline


def test_persistent_duplicate_rehydrates_canonical_source_into_engine():
    with TemporaryDirectory() as folder:
        database = Path(folder) / "research.db"
        body = "The same publisher text is seen again after a restart."
        first_source = ResearchSource(
            source_id="source-original",
            title="Original source",
            source_type="web",
            locator="https://publisher.example/original",
            publisher="Publisher A",
            reliability=0.9,
        )
        first_doc = ResearchDocument(
            document_id="doc-shared",
            source_id=first_source.source_id,
            title="Shared article",
            content=body,
        )
        with ResearchIngestionPipeline(database) as pipeline:
            pipeline.ingest(first_source, first_doc)

        duplicate_source = ResearchSource(
            source_id="source-reseen",
            title="Re-seen source",
            source_type="web",
            locator="https://publisher.example/reseen",
            publisher="Publisher A",
            reliability=0.9,
        )
        duplicate_doc = ResearchDocument(
            document_id="doc-shared",
            source_id=duplicate_source.source_id,
            title="Shared article",
            content=body,
        )
        with ResearchIngestionPipeline(database) as pipeline:
            result = pipeline.ingest(duplicate_source, duplicate_doc)
            assert result.duplicate is True
            assert "source-original" in pipeline.engine.sources
            assert "source-reseen" in pipeline.engine.sources
            assert "doc-shared" in pipeline.engine.documents
            assert pipeline.engine.documents["doc-shared"].source_id == "source-original"
