from __future__ import annotations

from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def make_knowledge(
    knowledge_id: str,
    statement: str,
    *,
    confidence: float = 0.8,
    verified: bool = False,
) -> KnowledgeCandidate:
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        confidence=confidence,
        verified=verified,
    )


def test_exact_statement_retrieval() -> None:
    storage = ResearchStorage(":memory:")

    storage.save_knowledge(
        make_knowledge(
            "knowledge-python",
            "Python is a programming language.",
        )
    )

    results = storage.retrieve_knowledge("Python")

    assert len(results) == 1
    assert results[0].knowledge_id == "knowledge-python"

    storage.close()


def test_case_insensitive_retrieval() -> None:
    storage = ResearchStorage(":memory:")

    storage.save_knowledge(
        make_knowledge(
            "knowledge-python",
            "Python is a programming language.",
        )
    )

    results = storage.retrieve_knowledge("python")

    assert len(results) == 1
    assert results[0].knowledge_id == "knowledge-python"

    storage.close()


def test_partial_statement_retrieval() -> None:
    storage = ResearchStorage(":memory:")

    storage.save_knowledge(
        make_knowledge(
            "knowledge-python",
            "Python is a high level programming language.",
        )
    )

    results = storage.retrieve_knowledge("programming language")

    assert len(results) == 1
    assert results[0].knowledge_id == "knowledge-python"

    storage.close()


def test_multiple_knowledge_retrieval() -> None:
    storage = ResearchStorage(":memory:")

    storage.save_knowledge(
        make_knowledge(
            "knowledge-python",
            "Python is a programming language.",
        )
    )

    storage.save_knowledge(
        make_knowledge(
            "knowledge-python-web",
            "Python is widely used for web development.",
        )
    )

    storage.save_knowledge(
        make_knowledge(
            "knowledge-rust",
            "Rust is a systems programming language.",
        )
    )

    results = storage.retrieve_knowledge("Python")

    ids = {item.knowledge_id for item in results}

    assert ids == {
        "knowledge-python",
        "knowledge-python-web",
    }

    storage.close()


def test_verified_filter() -> None:
    storage = ResearchStorage(":memory:")

    storage.save_knowledge(
        make_knowledge(
            "knowledge-verified",
            "Python is widely used.",
            verified=True,
        )
    )

    storage.save_knowledge(
        make_knowledge(
            "knowledge-unverified",
            "Python may be used elsewhere.",
            verified=False,
        )
    )

    results = storage.retrieve_knowledge(
        "Python",
        verified_only=True,
    )

    assert len(results) == 1
    assert results[0].knowledge_id == "knowledge-verified"

    storage.close()


def test_confidence_filter() -> None:
    storage = ResearchStorage(":memory:")

    storage.save_knowledge(
        make_knowledge(
            "knowledge-high",
            "Python is popular.",
            confidence=0.9,
        )
    )

    storage.save_knowledge(
        make_knowledge(
            "knowledge-low",
            "Python is useful.",
            confidence=0.4,
        )
    )

    results = storage.retrieve_knowledge(
        "Python",
        min_confidence=0.8,
    )

    ids = {item.knowledge_id for item in results}

    assert ids == {"knowledge-high"}

    storage.close()


def test_result_order_is_deterministic() -> None:
    storage = ResearchStorage(":memory:")

    storage.save_knowledge(
        make_knowledge(
            "knowledge-b",
            "Python B knowledge.",
            confidence=0.7,
        )
    )

    storage.save_knowledge(
        make_knowledge(
            "knowledge-a",
            "Python A knowledge.",
            confidence=0.7,
        )
    )

    results = storage.retrieve_knowledge("Python")

    assert [item.knowledge_id for item in results] == [
        "knowledge-a",
        "knowledge-b",
    ]

    storage.close()


def test_empty_query_protection() -> None:
    storage = ResearchStorage(":memory:")

    try:
        storage.retrieve_knowledge("")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty retrieval query was accepted"
        )

    storage.close()


def test_no_match_returns_empty_list() -> None:
    storage = ResearchStorage(":memory:")

    storage.save_knowledge(
        make_knowledge(
            "knowledge-python",
            "Python is a programming language.",
        )
    )

    results = storage.retrieve_knowledge(
        "quantum mechanics"
    )

    assert results == []

    storage.close()


def test_retrieval_survives_restart() -> None:
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        first_storage = ResearchStorage(tmp.name)

        first_storage.save_knowledge(
            make_knowledge(
                "knowledge-python",
                "Python is a programming language.",
            )
        )

        first_storage.close()

        second_storage = ResearchStorage(tmp.name)

        results = second_storage.retrieve_knowledge(
            "Python"
        )

        assert len(results) == 1
        assert results[0].knowledge_id == "knowledge-python"

        second_storage.close()


def run() -> None:
    print(
        "SAHIBEX 6H-9 KNOWLEDGE RETRIEVAL TEST"
    )

    tests = [
        (
            "exact statement retrieval",
            test_exact_statement_retrieval,
        ),
        (
            "case insensitive retrieval",
            test_case_insensitive_retrieval,
        ),
        (
            "partial statement retrieval",
            test_partial_statement_retrieval,
        ),
        (
            "multiple knowledge retrieval",
            test_multiple_knowledge_retrieval,
        ),
        (
            "verified filter",
            test_verified_filter,
        ),
        (
            "confidence filter",
            test_confidence_filter,
        ),
        (
            "deterministic result order",
            test_result_order_is_deterministic,
        ),
        (
            "empty query protection",
            test_empty_query_protection,
        ),
        (
            "no match returns empty list",
            test_no_match_returns_empty_list,
        ),
        (
            "retrieval survives restart",
            test_retrieval_survives_restart,
        ),
    ]

    for label, test in tests:
        test()
        print(f"[PASS] {label}")

    print(
        "SAHIBEX 6H-9 KNOWLEDGE RETRIEVAL TEST: PASS"
    )


if __name__ == "__main__":
    run()
