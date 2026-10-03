from core.research.deduplication import DocumentDeduplicator


def main() -> None:
    dedup = DocumentDeduplicator()

    original = """
    SAHIBEX research systems verify evidence
    before creating trusted knowledge.
    """

    result = dedup.register("doc-001", original)

    assert result.is_duplicate is False
    assert result.matched_document_id is None
    assert result.content_hash
    assert result.normalized_hash

    exact_duplicate = dedup.check(
        "doc-002",
        original,
    )

    assert exact_duplicate.is_duplicate is True
    assert exact_duplicate.matched_document_id == "doc-001"

    formatting_duplicate = """
        sahibex research systems verify evidence
        before creating trusted knowledge.
    """

    formatting_result = dedup.check(
        "doc-003",
        formatting_duplicate,
    )

    assert formatting_result.is_duplicate is True
    assert formatting_result.matched_document_id == "doc-001"

    new_document = """
    SAHIBEX uses verification and audit
    controls for protected actions.
    """

    new_result = dedup.register(
        "doc-004",
        new_document,
    )

    assert new_result.is_duplicate is False
    assert new_result.matched_document_id is None
    assert dedup.count() == 2

    assert dedup.contains(original) is True
    assert dedup.contains(new_document) is True

    assert dedup.find_document(original) == "doc-001"
    assert dedup.find_document(new_document) == "doc-004"

    try:
        dedup.check("doc-empty", "")
    except ValueError:
        pass
    else:
        raise AssertionError("Empty document was not rejected")

    try:
        dedup.check("", "valid content")
    except ValueError:
        pass
    else:
        raise AssertionError("Empty document ID was not rejected")

    summary = dedup.summary()

    assert summary["registered_documents"] == 2
    assert summary["exact_hashes"] == 2
    assert summary["normalized_hashes"] == 2

    dedup.clear()

    assert dedup.count() == 0
    assert dedup.contains(new_document) is False

    print("SAHIBEX DOCUMENT DEDUPLICATION TEST")
    print("[PASS] first document registration")
    print("[PASS] exact duplicate detection")
    print("[PASS] normalized duplicate detection")
    print("[PASS] new document registration")
    print("[PASS] document lookup")
    print("[PASS] invalid document protection")
    print("[PASS] invalid document ID protection")
    print("[PASS] deduplication summary")
    print("[PASS] registry clear")
    print("SAHIBEX DOCUMENT DEDUPLICATION TEST: PASS")


if __name__ == "__main__":
    main()
