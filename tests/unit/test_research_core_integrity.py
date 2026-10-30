from __future__ import annotations

from pathlib import Path

import pytest

from core.research.engine import ResearchEngine
from core.research.models import (
    Evidence,
    ResearchDocument,
    ResearchFinding,
    ResearchSource,
)
from core.research.pipeline import ResearchIngestionPipeline


def _source(source_id: str) -> ResearchSource:
    return ResearchSource(
        source_id=source_id,
        title=f"Source {source_id}",
        source_type="web",
        locator=f"https://example.com/{source_id}",
        publisher=f"Publisher {source_id}",
        reliability=0.9,
    )


def _document(
    document_id: str,
    source_id: str,
    content: str,
    *,
    content_hash: str | None = None,
) -> ResearchDocument:
    return ResearchDocument(
        document_id=document_id,
        source_id=source_id,
        title=f"Document {document_id}",
        content=content,
        content_hash=content_hash,
    )


def test_engine_rejects_a_forged_content_hash() -> None:
    engine = ResearchEngine()
    source = _source("source-hash")
    engine.register_source(source)
    document = _document(
        "document-forged-hash",
        source.source_id,
        "The actual document content.",
        content_hash="0" * 64,
    )

    with pytest.raises(ValueError, match="content_hash does not match"):
        engine.add_document(document)

    assert document.document_id not in engine.documents


def test_ingestion_pipeline_computes_missing_hash_before_persistence(tmp_path: Path) -> None:
    database_path = tmp_path / "research.sqlite3"
    source = _source("source-missing-hash")
    document = _document(
        "document-missing-hash",
        source.source_id,
        "A document without a caller-supplied hash.",
    )

    with ResearchIngestionPipeline(database_path) as pipeline:
        result = pipeline.ingest(source, document)

        assert result.document_stored is True
        assert result.duplicate is False
        expected_hash = ResearchEngine.hash_content(document.content)
        assert document.content_hash == expected_hash

        persisted = pipeline.storage.get_document(document.document_id)
        assert persisted is not None
        assert persisted.content_hash == expected_hash


def test_ingestion_pipeline_rejects_forged_hash_before_any_persistence(tmp_path: Path) -> None:
    database_path = tmp_path / "research.sqlite3"
    source = _source("source-forged-hash")
    document = _document(
        "document-forged-hash",
        source.source_id,
        "Content whose supplied hash is forged.",
        content_hash="f" * 64,
    )

    with ResearchIngestionPipeline(database_path) as pipeline:
        with pytest.raises(ValueError, match="content_hash does not match"):
            pipeline.ingest(source, document)

        assert pipeline.storage.source_count() == 0
        assert pipeline.storage.document_count() == 0
        assert source.source_id not in pipeline.engine.sources


def test_engine_does_not_reuse_evidence_already_owned_by_another_candidate() -> None:
    engine = ResearchEngine()
    source = _source("source-evidence-reuse")
    engine.register_source(source)
    document = _document(
        "document-evidence-reuse",
        source.source_id,
        "Evidence ownership should remain stable.",
    )
    engine.add_document(document)
    finding = ResearchFinding(
        finding_id="finding-evidence-reuse",
        document_id=document.document_id,
        claim="Evidence ownership should remain stable.",
        confidence=0.9,
    )
    engine.add_finding(finding)
    evidence = Evidence(
        evidence_id="evidence-owned",
        finding_id=finding.finding_id,
        source_id=source.source_id,
        evidence_text="Evidence ownership should remain stable.",
        supports=True,
        strength=0.9,
    )
    engine.add_evidence(evidence)

    first = engine.create_knowledge_candidate(
        statement="First knowledge claim.",
        finding_id=finding.finding_id,
    )
    engine.verify_knowledge(first.knowledge_id)
    assert evidence.metadata["knowledge_id"] == first.knowledge_id

    second = engine.create_knowledge_candidate(
        statement="Second knowledge claim.",
        finding_id=finding.finding_id,
    )
    assert second.evidence == []
    assert evidence.metadata["knowledge_id"] == first.knowledge_id

    rechecked_first = engine.verify_knowledge(first.knowledge_id)
    assert rechecked_first.verified is False
    assert evidence.metadata["knowledge_id"] == first.knowledge_id


def test_pipeline_rejects_reassigning_persisted_evidence_to_another_candidate(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "research.sqlite3"
    source = _source("source-pipeline-evidence-reuse")
    document = _document(
        "document-pipeline-evidence-reuse",
        source.source_id,
        "Persisted evidence must not change owners.",
    )

    with ResearchIngestionPipeline(database_path) as pipeline:
        pipeline.ingest(source, document)
        pipeline.add_finding(
            ResearchFinding(
                finding_id="finding-pipeline-evidence-reuse",
                document_id=document.document_id,
                claim="Persisted evidence must not change owners.",
                confidence=0.9,
            )
        )
        pipeline.add_evidence(
            Evidence(
                evidence_id="evidence-pipeline-owned",
                finding_id="finding-pipeline-evidence-reuse",
                source_id=source.source_id,
                evidence_text="Persisted evidence must not change owners.",
                supports=True,
                strength=0.9,
            )
        )

        first = pipeline.create_knowledge(
            statement="First persisted knowledge claim.",
            finding_ids=["finding-pipeline-evidence-reuse"],
            evidence_ids=["evidence-pipeline-owned"],
        )
        assert first.stored is True
        persisted_evidence = pipeline.storage.get_evidence(
            "evidence-pipeline-owned"
        )
        assert persisted_evidence is not None
        assert persisted_evidence.metadata["knowledge_id"] == first.knowledge_id

        with pytest.raises(ValueError, match="already linked to knowledge candidate"):
            pipeline.create_knowledge(
                statement="Second persisted knowledge claim.",
                finding_ids=["finding-pipeline-evidence-reuse"],
                evidence_ids=["evidence-pipeline-owned"],
            )

        assert pipeline.storage.knowledge_count() == 1
        unchanged = pipeline.storage.get_evidence("evidence-pipeline-owned")
        assert unchanged is not None
        assert unchanged.metadata["knowledge_id"] == first.knowledge_id
