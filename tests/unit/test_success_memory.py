from datetime import datetime, timedelta, timezone

from core.research.success_memory import (
    SUCCESS_MEMORY_VERSION,
    SuccessMemory,
    SuccessMemoryStore,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    success_1 = SuccessMemory(
        success_id="success-001",
        task="Run SAHIBEX memory tests",
        context="Phase 2 verification",
        action_taken="Compile modules and execute unit tests",
        outcome="All memory tests passed",
        lesson="Compile and test every completed memory component",
        source="development-session-1",
        confidence=0.98,
        importance=0.95,
        effectiveness=0.95,
        provenance={"session_id": "session-1"},
        tags=["testing", "sahibex", "memory"],
        occurred_at=base_time,
        recorded_at=base_time,
    )

    success_2 = SuccessMemory(
        success_id="success-002",
        task="Implement semantic memory",
        context="Phase 2 memory development",
        action_taken="Build bounded semantic store with retrieval",
        outcome="Semantic memory test passed",
        lesson="Keep memory components bounded and read-only",
        source="development-session-2",
        confidence=0.92,
        importance=0.85,
        effectiveness=0.88,
        provenance={"session_id": "session-2"},
        tags=["semantic", "memory"],
        occurred_at=base_time + timedelta(seconds=1),
        recorded_at=base_time + timedelta(seconds=1),
    )

    success_3 = SuccessMemory(
        success_id="success-003",
        task="Verify procedural memory",
        context="Phase 2 verification",
        action_taken="Run procedural memory unit test",
        outcome="Procedural memory test passed",
        lesson="Verify learned procedures with deterministic tests",
        source="development-session-3",
        confidence=0.90,
        importance=0.80,
        effectiveness=0.82,
        provenance={"session_id": "session-3"},
        tags=["procedural", "testing"],
        occurred_at=base_time + timedelta(seconds=2),
        recorded_at=base_time + timedelta(seconds=2),
    )

    check(
        success_1.success_id == "success-001",
        "success memory identity preserved",
    )

    check(
        success_1.task == "Run SAHIBEX memory tests",
        "success task preserved",
    )

    check(
        success_1.context == "Phase 2 verification",
        "success context preserved",
    )

    check(
        success_1.action_taken.startswith("Compile"),
        "successful action record preserved",
    )

    check(
        success_1.outcome == "All memory tests passed",
        "success outcome preserved",
    )

    check(
        success_1.lesson.startswith("Compile"),
        "success lesson preserved",
    )

    check(
        success_1.provenance["session_id"] == "session-1",
        "success provenance preserved",
    )

    store = SuccessMemoryStore(capacity=3)

    store.store(success_1)
    store.store(success_2)
    store.store(success_3)

    check(
        store.count() == 3,
        "success memory storage works",
    )

    check(
        store.get("success-001") == success_1,
        "success memory retrieval works",
    )

    check(
        store.contains("success-002"),
        "success identity lookup works",
    )

    effective = store.by_effectiveness(minimum=0.90)

    check(
        len(effective) == 1
        and effective[0].success_id == "success-001",
        "effectiveness-based retrieval works",
    )

    tagged = store.by_tag("memory")

    check(
        len(tagged) == 2,
        "success tag retrieval works",
    )

    searched = store.search("bounded semantic")

    check(
        len(searched) == 1
        and searched[0].success_id == "success-002",
        "success search works",
    )

    lessons = store.lessons()

    check(
        len(lessons) == 3,
        "success lesson retrieval works",
    )

    actions = store.effective_actions()

    check(
        len(actions) == 3,
        "effective action retrieval works",
    )

    recent = store.recent(limit=2)

    check(
        len(recent) == 2,
        "recent success retrieval works",
    )

    check(
        recent[0].success_id == "success-003",
        "recent success ordering works",
    )

    all_successes = store.all()

    check(
        len(all_successes) == 3,
        "success memory listing works",
    )

    old_success = SuccessMemory(
        success_id="success-004",
        task="Old task",
        context="Old context",
        action_taken="Old action",
        outcome="Old outcome",
        lesson="Old lesson",
        source="old-source",
        confidence=0.30,
        importance=0.20,
        effectiveness=0.20,
        provenance={"session_id": "old"},
        tags=["old"],
        occurred_at=base_time - timedelta(days=1),
        recorded_at=base_time - timedelta(days=1),
    )

    store.store(old_success)

    check(
        not store.contains("success-004"),
        "oldest success is evicted when capacity is exceeded",
    )

    check(
        store.contains("success-001"),
        "newer success is retained",
    )

    try:
        success_1.lesson = "changed"
        immutable_blocked = False
    except (AttributeError, TypeError):
        immutable_blocked = True

    check(
        immutable_blocked,
        "success memory objects are immutable",
    )

    check(
        SUCCESS_MEMORY_VERSION == "P2-SC-1",
        "success memory version is correct",
    )

    summary = store.summary()

    check(
        summary["preserves_context"] is True,
        "success context preservation enabled",
    )

    check(
        summary["preserves_action_record"] is True,
        "successful action preservation enabled",
    )

    check(
        summary["preserves_outcome"] is True,
        "success outcome preservation enabled",
    )

    check(
        summary["preserves_lesson"] is True,
        "success lesson preservation enabled",
    )

    check(
        summary["preserves_provenance"] is True,
        "success provenance preservation enabled",
    )

    check(
        summary["tracks_effectiveness"] is True,
        "effectiveness tracking enabled",
    )

    check(
        summary["supports_effectiveness_retrieval"] is True,
        "effectiveness retrieval capability enabled",
    )

    check(
        summary["supports_success_search"] is True,
        "success search capability enabled",
    )

    check(
        summary["supports_lesson_retrieval"] is True,
        "success lesson retrieval enabled",
    )

    check(
        summary["supports_effective_action_retrieval"] is True,
        "effective action retrieval enabled",
    )

    check(
        summary["execution_authority"] is False,
        "success memory has no execution authority",
    )

    check(
        summary["grants_permission"] is False,
        "success memory grants no permission",
    )

    check(
        summary["executes_actions"] is False,
        "success memory executes no actions",
    )

    check(
        summary["modifies_constitution"] is False,
        "success memory cannot modify constitution",
    )

    removed = store.remove("success-002")

    check(
        removed is not None and not store.contains("success-002"),
        "success memory removal works",
    )

    store.clear()

    check(
        store.count() == 0,
        "success memory cleanup works",
    )

    print("SAHIBEX PHASE 2 #49 SUCCESS MEMORY TEST: PASS")


if __name__ == "__main__":
    main()
