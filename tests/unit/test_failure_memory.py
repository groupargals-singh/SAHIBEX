from datetime import datetime, timedelta, timezone

from core.research.failure_memory import (
    FAILURE_MEMORY_VERSION,
    FailureMemory,
    FailureMemoryStore,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    failure_1 = FailureMemory(
        failure_id="failure-001",
        task="Run SAHIBEX test suite",
        context="Phase 2 verification",
        attempted_action="Execute unit tests",
        failure="Test assertion failed",
        cause="Test expectation did not match fixture data",
        recovery="Correct the test expectation and rerun",
        lesson="Verify fixture assumptions before changing production code",
        source="development-session-1",
        severity=0.75,
        confidence=0.95,
        importance=0.90,
        provenance={"session_id": "session-1"},
        tags=["testing", "debugging", "sahibex"],
        occurred_at=base_time,
        recorded_at=base_time,
    )

    failure_2 = FailureMemory(
        failure_id="failure-002",
        task="Compile Python module",
        context="Development environment",
        attempted_action="Run Python compiler",
        failure="Syntax error",
        cause="Missing closing parenthesis",
        recovery="Fix syntax and compile again",
        lesson="Compile immediately after structural code edits",
        source="development-session-2",
        severity=0.60,
        confidence=0.90,
        importance=0.75,
        provenance={"session_id": "session-2"},
        tags=["python", "compile"],
        occurred_at=base_time + timedelta(seconds=1),
        recorded_at=base_time + timedelta(seconds=1),
    )

    failure_3 = FailureMemory(
        failure_id="failure-003",
        task="Run integration test",
        context="Integration verification",
        attempted_action="Execute integration test",
        failure="Dependency unavailable",
        cause="Required test dependency was missing",
        recovery="Install or provide the required dependency",
        lesson="Validate test environment dependencies before execution",
        source="development-session-3",
        severity=0.85,
        confidence=0.88,
        importance=0.80,
        provenance={"session_id": "session-3"},
        tags=["testing", "environment"],
        occurred_at=base_time + timedelta(seconds=2),
        recorded_at=base_time + timedelta(seconds=2),
    )

    check(
        failure_1.failure_id == "failure-001",
        "failure memory identity preserved",
    )

    check(
        failure_1.task == "Run SAHIBEX test suite",
        "failure task preserved",
    )

    check(
        failure_1.context == "Phase 2 verification",
        "failure context preserved",
    )

    check(
        failure_1.attempted_action == "Execute unit tests",
        "attempted action preserved",
    )

    check(
        failure_1.failure == "Test assertion failed",
        "failure description preserved",
    )

    check(
        failure_1.cause.startswith("Test expectation"),
        "failure cause preserved",
    )

    check(
        failure_1.recovery.startswith("Correct"),
        "recovery knowledge preserved",
    )

    check(
        failure_1.lesson.startswith("Verify"),
        "failure lesson preserved",
    )

    check(
        failure_1.provenance["session_id"] == "session-1",
        "failure provenance preserved",
    )

    store = FailureMemoryStore(capacity=3)

    store.store(failure_1)
    store.store(failure_2)
    store.store(failure_3)

    check(
        store.count() == 3,
        "failure memory storage works",
    )

    check(
        store.get("failure-001") == failure_1,
        "failure memory retrieval works",
    )

    check(
        store.contains("failure-002"),
        "failure identity lookup works",
    )

    severe = store.by_severity(minimum=0.80)

    check(
        len(severe) == 1
        and severe[0].failure_id == "failure-003",
        "severity-based failure retrieval works",
    )

    tagged = store.by_tag("testing")

    check(
        len(tagged) == 2,
        "failure tag retrieval works",
    )

    searched = store.search("fixture data")

    check(
        len(searched) == 1
        and searched[0].failure_id == "failure-001",
        "failure search works",
    )

    lessons = store.lessons()

    check(
        len(lessons) == 3,
        "failure lesson retrieval works",
    )

    recovery = store.recovery_knowledge()

    check(
        len(recovery) == 3,
        "recovery knowledge retrieval works",
    )

    recent = store.recent(limit=2)

    check(
        len(recent) == 2,
        "recent failure retrieval works",
    )

    check(
        recent[0].failure_id == "failure-003",
        "recent failure ordering works",
    )

    old_failure = FailureMemory(
        failure_id="failure-004",
        task="Old task",
        context="Old context",
        attempted_action="Old action",
        failure="Old failure",
        cause="Old cause",
        recovery="Old recovery",
        lesson="Old lesson",
        source="old-source",
        severity=0.20,
        confidence=0.30,
        importance=0.20,
        provenance={"session_id": "old"},
        tags=["old"],
        occurred_at=base_time - timedelta(days=1),
        recorded_at=base_time - timedelta(days=1),
    )

    store.store(old_failure)

    check(
        not store.contains("failure-004"),
        "oldest failure is evicted when capacity is exceeded",
    )

    check(
        store.contains("failure-001"),
        "newer failure is retained",
    )

    try:
        failure_1.lesson = "changed"
        immutable_blocked = False
    except (AttributeError, TypeError):
        immutable_blocked = True

    check(
        immutable_blocked,
        "failure memory objects are immutable",
    )

    check(
        FAILURE_MEMORY_VERSION == "P2-FM-1",
        "failure memory version is correct",
    )

    summary = store.summary()

    check(
        summary["preserves_context"] is True,
        "failure context preservation enabled",
    )

    check(
        summary["preserves_attempted_action"] is True,
        "attempted action preservation enabled",
    )

    check(
        summary["preserves_failure"] is True,
        "failure preservation enabled",
    )

    check(
        summary["preserves_cause"] is True,
        "failure cause preservation enabled",
    )

    check(
        summary["preserves_recovery"] is True,
        "recovery preservation enabled",
    )

    check(
        summary["preserves_lesson"] is True,
        "failure lesson preservation enabled",
    )

    check(
        summary["preserves_provenance"] is True,
        "failure provenance preservation enabled",
    )

    check(
        summary["supports_severity_retrieval"] is True,
        "severity retrieval capability enabled",
    )

    check(
        summary["supports_failure_search"] is True,
        "failure search capability enabled",
    )

    check(
        summary["supports_lesson_retrieval"] is True,
        "lesson retrieval capability enabled",
    )

    check(
        summary["recovery_is_knowledge_only"] is True,
        "recovery is knowledge-only",
    )

    check(
        summary["grants_permission"] is False,
        "failure memory grants no permission",
    )

    check(
        summary["executes_actions"] is False,
        "failure memory executes no actions",
    )

    check(
        summary["modifies_constitution"] is False,
        "failure memory cannot modify constitution",
    )

    removed = store.remove("failure-002")

    check(
        removed is not None and not store.contains("failure-002"),
        "failure memory removal works",
    )

    store.clear()

    check(
        store.count() == 0,
        "failure memory cleanup works",
    )

    print("SAHIBEX PHASE 2 #48 FAILURE MEMORY TEST: PASS")


if __name__ == "__main__":
    main()
