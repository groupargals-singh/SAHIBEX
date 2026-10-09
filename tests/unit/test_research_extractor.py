from core.research.extractor import ResearchExtractor
from core.research.models import ResearchDocument


def main() -> None:
    extractor = ResearchExtractor()

    document = ResearchDocument(
        document_id="doc-extractor-001",
        source_id="src-extractor-001",
        title="Extractor Test Document",
        content=(
            "Research systems should preserve evidence. "
            "Evidence should remain linked to its source. "
            "Verification should happen before knowledge is trusted."
        ),
    )

    findings = extractor.extract(document)

    assert len(findings) == 3

    assert findings[0].claim == (
        "Research systems should preserve evidence."
    )
    assert findings[0].evidence_text == (
        "Research systems should preserve evidence."
    )
    assert findings[0].confidence == 0.50

    assert findings[1].claim == (
        "Evidence should remain linked to its source."
    )

    assert findings[2].claim == (
        "Verification should happen before knowledge is trusted."
    )

    # Whitespace normalization must not create empty findings.
    whitespace_document = ResearchDocument(
        document_id="doc-extractor-002",
        source_id="src-extractor-001",
        title="Whitespace Test Document",
        content="   One valid statement.   ",
    )

    whitespace_findings = extractor.extract(whitespace_document)

    assert len(whitespace_findings) == 1
    assert whitespace_findings[0].claim == "One valid statement."

    # Hostile/overlong pages must not amplify into unbounded finding writes.
    dense_document = ResearchDocument(
        document_id="doc-extractor-dense",
        source_id="src-extractor-001",
        title="Dense Page Test",
        content=("Sentence one. " * 5_000),
    )
    dense_findings = extractor.extract(dense_document)
    assert len(dense_findings) == extractor.MAX_FINDINGS
    assert all(item.truncated for item in dense_findings)

    oversized_document = ResearchDocument(
        document_id="doc-extractor-oversized",
        source_id="src-extractor-001",
        title="Oversized Page Test",
        content=("Valid statement. " * 20_000),
    )
    oversized_findings = extractor.extract(oversized_document)
    assert len(oversized_findings) <= extractor.MAX_FINDINGS
    assert all(item.truncated for item in oversized_findings)

    print("SAHIBEX RESEARCH EXTRACTOR TEST")
    print("[PASS] deterministic sentence extraction")
    print("[PASS] claim/evidence preservation")
    print("[PASS] extraction confidence boundary")
    print("[PASS] whitespace normalization")
    print("SAHIBEX RESEARCH EXTRACTOR TEST: PASS")


if __name__ == "__main__":
    main()
