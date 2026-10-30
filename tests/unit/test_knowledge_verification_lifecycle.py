from __future__ import annotations

from datetime import datetime, timezone
import tempfile

from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def make_knowledge(
    knowledge_id: str,
    statement: str,
    *,
    confidence: float = 0.9,
    verified: bool = False,
) -> KnowledgeCandidate:
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        confidence=confidence,
        verified=verified,
    )


def test_initial_verification_state() -> None:
    knowledge = make_knowledge(
        "knowledge-a",
        "The system is online.",
    )

    storage = ResearchStorage(":memory:")

    storage.save_knowledge(knowledge)

    context = storage.knowledge_verification_lifecycle(
        "knowledge-a"
    )

    assert context["knowledge_id"] == "knowledge-a"
    assert context["verification_status"] == "UNVERIFIED"
    assert context["verification_event_count"] == 0
    assert context["last_verification_status"] is None

    storage.close()


def test_verified_state_is_recorded() -> None:
    knowledge = make_knowledge(
        "knowledge-a",
        "The system is online.",
        verified=True,
    )

    storage = ResearchStorage(":memory:")

    storage.save_knowledge(knowledge)

    storage.record_knowledge_verification(
        knowledge_id="knowledge-a",
        status="VERIFIED",
        reason="Evidence supports the knowledge.",
        verified_at=datetime.now(timezone.utc),
        metadata={"source": "verification-test"},
    )

    context = storage.knowledge_verification_lifecycle(
        "knowledge-a"
    )

    assert context["knowledge_id"] == "knowledge-a"
    assert context["verification_status"] == "VERIFIED"
    assert context["verification_event_count"] == 1
    assert context["last_verification_status"] == "VERIFIED"

    storage.close()


def test_unverified_state_is_recorded() -> None:
    knowledge = make_knowledge(
        "knowledge-a",
        "The system is online.",
    )

    storage = ResearchStorage(":memory:")

    storage.save_knowledge(knowledge)

    storage.record_knowledge_verification(
        knowledge_id="knowledge-a",
        status="UNVERIFIED",
        reason="Evidence is insufficient.",
        verified_at=datetime.now(timezone.utc),
    )

    context = storage.knowledge_verification_lifecycle(
        "knowledge-a"
    )

    assert context["verification_status"] == "UNVERIFIED"
    assert context["verification_event_count"] == 1
    assert context["last_verification_status"] == "UNVERIFIED"

    storage.close()


def test_conflicted_state_is_recorded() -> None:
    knowledge = make_knowledge(
        "knowledge-a",
        "The system is online.",
    )

    storage = ResearchStorage(":memory:")

    storage.save_knowledge(knowledge)

    storage.record_knowledge_verification(
        knowledge_id="knowledge-a",
        status="CONFLICTED",
        reason="Knowledge conflicts with another verified candidate.",
        verified_at=datetime.now(timezone.utc),
    )

    context = storage.knowledge_verification_lifecycle(
        "knowledge-a"
    )

    assert context["verification_status"] == "CONFLICTED"
    assert context["verification_event_count"] == 1
    assert context["last_verification_status"] == "CONFLICTED"

    storage.close()


def test_verification_history_is_preserved() -> None:
    knowledge = make_knowledge(
        "knowledge-a",
        "The system is online.",
    )

    storage = ResearchStorage(":memory:")

    storage.save_knowledge(knowledge)

    first_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    second_time = datetime(2026, 1, 2, tzinfo=timezone.utc)

    storage.record_knowledge_verification(
        knowledge_id="knowledge-a",
        status="UNVERIFIED",
        reason="Initial evidence was insufficient.",
        verified_at=first_time,
    )

    storage.record_knowledge_verification(
        knowledge_id="knowledge-a",
        status="VERIFIED",
        reason="Additional evidence confirmed the claim.",
        verified_at=second_time,
    )

    history = storage.knowledge_verification_history(
        "knowledge-a"
    )

    assert len(history) == 2
    assert history[0]["status"] == "UNVERIFIED"
    assert history[1]["status"] == "VERIFIED"
    assert history[0]["reason"] == (
        "Initial evidence was insufficient."
    )
    assert history[1]["reason"] == (
        "Additional evidence confirmed the claim."
    )

    context = storage.knowledge_verification_lifecycle(
        "knowledge-a"
    )

    assert context["verification_status"] == "VERIFIED"
    assert context["verification_event_count"] == 2
    assert context["last_verification_status"] == "VERIFIED"

    storage.close()


def test_verification_history_survives_restart() -> None:
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        first_storage = ResearchStorage(tmp.name)

        knowledge = make_knowledge(
            "knowledge-a",
            "The system is online.",
        )

        first_storage.save_knowledge(knowledge)

        verified_at = datetime(
            2026,
            2,
            1,
            tzinfo=timezone.utc,
        )

        first_storage.record_knowledge_verification(
            knowledge_id="knowledge-a",
            status="VERIFIED",
            reason="Persistent verification.",
            verified_at=verified_at,
        )

        first_storage.close()

        second_storage = ResearchStorage(tmp.name)

        history = second_storage.knowledge_verification_history(
            "knowledge-a"
        )

        assert len(history) == 1
        assert history[0]["status"] == "VERIFIED"
        assert history[0]["reason"] == (
            "Persistent verification."
        )

        context = second_storage.knowledge_verification_lifecycle(
            "knowledge-a"
        )

        assert context["verification_status"] == "VERIFIED"
        assert context["verification_event_count"] == 1

        second_storage.close()


def test_invalid_verification_status_is_rejected() -> None:
    storage = ResearchStorage(":memory:")

    storage.save_knowledge(
        make_knowledge(
            "knowledge-a",
            "The system is online.",
        )
    )

    try:
        storage.record_knowledge_verification(
            knowledge_id="knowledge-a",
            status="INVALID",
            reason="Invalid status.",
            verified_at=datetime.now(timezone.utc),
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "invalid verification status was accepted"
        )

    storage.close()


def test_empty_knowledge_id_is_rejected() -> None:
    storage = ResearchStorage(":memory:")

    try:
        storage.knowledge_verification_lifecycle("")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty knowledge ID was accepted"
        )

    storage.close()


def test_unknown_knowledge_history_is_empty() -> None:
    storage = ResearchStorage(":memory:")

    history = storage.knowledge_verification_history(
        "unknown-knowledge"
    )

    assert history == []

    storage.close()


def run() -> None:
    print(
        "SAHIBEX 6H-8 KNOWLEDGE VERIFICATION LIFECYCLE TEST"
    )

    tests = [
        (
            "initial verification state",
            test_initial_verification_state,
        ),
        (
            "verified state is recorded",
            test_verified_state_is_recorded,
        ),
        (
            "unverified state is recorded",
            test_unverified_state_is_recorded,
        ),
        (
            "conflicted state is recorded",
            test_conflicted_state_is_recorded,
        ),
        (
            "verification history is preserved",
            test_verification_history_is_preserved,
        ),
        (
            "verification history survives restart",
            test_verification_history_survives_restart,
        ),
        (
            "invalid verification status protection",
            test_invalid_verification_status_is_rejected,
        ),
        (
            "empty knowledge ID protection",
            test_empty_knowledge_id_is_rejected,
        ),
        (
            "unknown knowledge history",
            test_unknown_knowledge_history_is_empty,
        ),
    ]

    for label, test in tests:
        test()
        print(f"[PASS] {label}")

    print(
        "SAHIBEX 6H-8 KNOWLEDGE VERIFICATION LIFECYCLE TEST: PASS"
    )


if __name__ == "__main__":
    run()


def test_same_timestamp_and_status_preserve_both_events() -> None:
    storage = ResearchStorage(":memory:")
    storage.save_knowledge(
        make_knowledge(
            "knowledge-same-time",
            "A candidate with repeated verification attempts.",
        )
    )
    timestamp = datetime(2026, 3, 1, tzinfo=timezone.utc)

    for reason in (
        "First verification attempt.",
        "Second verification attempt.",
    ):
        storage.record_knowledge_verification(
            knowledge_id="knowledge-same-time",
            status="UNVERIFIED",
            reason=reason,
            verified_at=timestamp,
        )

    history = storage.knowledge_verification_history("knowledge-same-time")
    assert len(history) == 2
    assert {item["reason"] for item in history} == {
        "First verification attempt.",
        "Second verification attempt.",
    }
    assert len({item["event_id"] for item in history}) == 2
    storage.close()
