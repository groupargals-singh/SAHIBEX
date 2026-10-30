from core.research import (
    Evidence,
    ResearchDocument,
    ResearchEngine,
    ResearchFinding,
    ResearchSource,
)


def test_research_core() -> None:
    engine = ResearchEngine()

    # Source
    source = ResearchSource(
        source_id="source_001",
        title="Example Technical Source",
        source_type="document",
        locator="https://example.com/source",
        publisher="Example Publisher",
        reliability=0.90,
    )

    engine.register_source(source)

    assert len(engine.sources) == 1

    # Document
    document = ResearchDocument(
        document_id="document_001",
        source_id="source_001",
        title="Example Research Document",
        content=(
            "SAHIBEX research systems should preserve "
            "source information and evidence."
        ),
    )

    engine.add_document(document)

    assert document.content_hash is not None
    assert len(document.content_hash) == 64

    # Finding
    finding = ResearchFinding(
        finding_id="finding_001",
        document_id="document_001",
        claim="Research information should retain source evidence.",
        evidence_text=(
            "The document explicitly connects research "
            "information with source evidence."
        ),
        confidence=0.80,
    )

    engine.add_finding(finding)

    assert len(engine.findings) == 1

    # Evidence
    evidence = Evidence(
        evidence_id="evidence_001",
        finding_id="finding_001",
        source_id="source_001",
        evidence_text=(
            "The source document contains the supporting statement."
        ),
        supports=True,
        strength=0.90,
    )

    engine.add_evidence(evidence)

    assert len(engine.evidence) == 1

    # Knowledge candidate
    knowledge = engine.create_knowledge_candidate(
        statement=(
            "SAHIBEX research knowledge should retain "
            "source-linked evidence."
        ),
        finding_id="finding_001",
    )

    assert knowledge.verified is False
    assert knowledge.confidence >= 0.60

    # Verification
    verified = engine.verify_knowledge(
        knowledge.knowledge_id
    )

    assert verified.verified is False
    assert verified.last_verified_at is None
    assert verified.metadata["verification_status"] == "UNVERIFIED"
    assert verified.metadata["supporting_source_count"] == 1
    # Result
    result = engine.create_result(
        "How should research knowledge be represented?"
    )

    assert result.completed is True
    assert result.verified is False
    assert result.source_count == 1
    assert result.document_count == 1
    assert result.finding_count == 1
    assert result.evidence_count == 1
    assert result.knowledge_count == 1

    # Summary
    summary = engine.summary()

    assert summary["sources"] == 1
    assert summary["documents"] == 1
    assert summary["findings"] == 1
    assert summary["evidence"] == 1
    assert summary["knowledge_candidates"] == 1
    assert summary["verified_knowledge"] == 0
    assert summary["verified_knowledge"] == 0

def test_evidence_cannot_claim_an_unrelated_publisher() -> None:
    import pytest

    engine = ResearchEngine()
    source_a = ResearchSource(
        source_id="source-a",
        title="Publisher A",
        source_type="web",
        locator="https://a.example/article",
        publisher="Publisher A",
        reliability=0.9,
    )
    source_b = ResearchSource(
        source_id="source-b",
        title="Publisher B",
        source_type="web",
        locator="https://b.example/article",
        publisher="Publisher B",
        reliability=0.9,
    )
    engine.register_source(source_a)
    engine.register_source(source_b)
    document = ResearchDocument(
        document_id="document-a",
        source_id="source-a",
        title="Publisher A article",
        content="A claim reported by publisher A.",
    )
    engine.add_document(document)
    finding = ResearchFinding(
        finding_id="finding-a",
        document_id="document-a",
        claim="A claim reported by publisher A.",
        confidence=0.8,
    )
    engine.add_finding(finding)

    forged_evidence = Evidence(
        evidence_id="forged-evidence",
        finding_id="finding-a",
        source_id="source-b",
        evidence_text="A claim reported by publisher A.",
        supports=True,
        strength=0.99,
    )

    with pytest.raises(ValueError, match="does not match the finding document source"):
        engine.add_evidence(forged_evidence)

    assert "forged-evidence" not in engine.evidence


def test_invalid_source_reliability() -> None:
    try:
        ResearchSource(
            source_id="bad",
            title="Bad Source",
            source_type="document",
            locator="test",
            reliability=1.5,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "invalid reliability should be rejected"
        )


def test_unknown_source_document_is_rejected() -> None:
    engine = ResearchEngine()

    document = ResearchDocument(
        document_id="document_001",
        source_id="missing_source",
        title="Unknown Source Document",
        content="Some content",
    )

    try:
        engine.add_document(document)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "document with unknown source should be rejected"
        )


def test_unverified_knowledge_without_evidence() -> None:
    engine = ResearchEngine()

    source = ResearchSource(
        source_id="source_001",
        title="Test Source",
        source_type="document",
        locator="test",
        reliability=0.80,
    )

    engine.register_source(source)

    document = ResearchDocument(
        document_id="document_001",
        source_id="source_001",
        title="Test Document",
        content="Test research content.",
    )

    engine.add_document(document)

    finding = ResearchFinding(
        finding_id="finding_001",
        document_id="document_001",
        claim="A claim without supporting evidence.",
        confidence=0.80,
    )

    engine.add_finding(finding)

    knowledge = engine.create_knowledge_candidate(
        statement="This must remain unverified.",
        finding_id="finding_001",
    )

    verified = engine.verify_knowledge(
        knowledge.knowledge_id
    )

    assert verified.verified is False


if __name__ == "__main__":
    print("SAHIBEX RESEARCH CORE TEST")

    test_research_core()
    print("[PASS] research source/document/finding/evidence pipeline")

    test_invalid_source_reliability()
    print("[PASS] source validation")

    test_unknown_source_document_is_rejected()
    print("[PASS] unknown source protection")

    test_unverified_knowledge_without_evidence()
    print("[PASS] unverified knowledge protection")

    print("SAHIBEX RESEARCH CORE TEST: PASS")
