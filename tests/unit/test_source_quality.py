from __future__ import annotations

from datetime import datetime, timezone

from core.research.models import ResearchSource
from core.research.source_quality import (
    SOURCE_QUALITY_VERSION,
    assess_source_quality,
    assess_source_quality_from_metadata,
)


def build_source(
    *,
    source_type: str = "web",
    metadata: dict | None = None,
) -> ResearchSource:
    return ResearchSource(
        source_id="source_quality_001",
        title="SAHIBEX Source Quality Test",
        source_type=source_type,
        locator="https://example.com/source-quality",
        publisher="Example Publisher",
        author="Example Author",
        published_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        reliability=0.75,
        metadata=metadata or {},
    )


def main() -> None:
    source = build_source(
        metadata={
            "provider": "test-provider",
            "provider_name": "test-provider",
            "content_type": "text/plain",
            "content_hash": "abc123",
            "content_bytes": 128,
            "acquired_at": "2026-01-01T00:00:00+00:00",
            "discovery_only": False,
            "content_is_full_document": True,
            "reliability_source": "provider",
            "reliability_method": "provider_declared_default",
            "reliability_version": "6G-1",
        }
    )

    assessment = assess_source_quality(source)

    assert assessment.source_id == source.source_id
    print("[PASS] source identity preserved")

    assert 0.0 <= assessment.quality_score <= 1.0
    print("[PASS] quality score bounded")

    assert 0.0 <= assessment.provenance_score <= 1.0
    print("[PASS] provenance score bounded")

    assert 0.0 <= assessment.authority_score <= 1.0
    print("[PASS] authority score bounded")

    assert 0.0 <= assessment.metadata_completeness_score <= 1.0
    print("[PASS] metadata completeness bounded")

    assert 0.0 <= assessment.acquisition_integrity_score <= 1.0
    print("[PASS] acquisition integrity bounded")

    assert assessment.version == SOURCE_QUALITY_VERSION
    print("[PASS] quality contract version")

    assert source.reliability == 0.75
    print("[PASS] reliability remains independent")

    document = build_source(
        source_type="document",
        metadata={
            "provider": "LocalDocumentResearchProvider",
            "provider_name": "document",
            "content_hash": "document-hash",
            "content_bytes": 512,
            "acquired_at": "2026-01-01T00:00:00+00:00",
            "discovery_only": False,
            "content_is_full_document": True,
            "content_type": "text/plain",
            "reliability_source": "provider",
            "reliability_version": "6G-1",
        },
    )

    document_assessment = assess_source_quality(document)

    assert document_assessment.authority_score == 1.0
    print("[PASS] document authority characteristic")

    sparse = build_source(
        metadata={}
    )

    sparse_assessment = assess_source_quality(sparse)

    assert (
        sparse_assessment.quality_score
        < assessment.quality_score
    )
    print("[PASS] incomplete metadata lowers quality")

    wrapper_assessment = assess_source_quality_from_metadata(
        source_id="wrapper_001",
        title="Wrapper Test",
        source_type="api",
        locator="https://example.com/api",
        publisher="Example API",
        reliability=0.80,
        metadata={
            "provider": "test-api",
            "content_type": "application/json",
            "content_hash": "hash",
            "content_bytes": 64,
            "acquired_at": "2026-01-01T00:00:00+00:00",
            "discovery_only": False,
            "content_is_api_result": True,
        },
    )

    assert wrapper_assessment.source_id == "wrapper_001"
    assert wrapper_assessment.authority_score == 0.90
    print("[PASS] metadata wrapper")

    print("SAHIBEX SOURCE QUALITY SCORING TEST: PASS")


if __name__ == "__main__":
    main()
