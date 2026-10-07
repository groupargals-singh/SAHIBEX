from datetime import datetime, timedelta, timezone

from core.research.experience_memory import (
    EXPERIENCE_MEMORY_VERSION,
    ExperienceMemory,
    ExperienceMemoryStore,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    experience_1 = ExperienceMemory(
        experience_id="experience-001",
        task="Build SAHIBEX memory component",
        context="Phase 2 memory development",
        action_taken="Implemented working memory and tests",
        outcome="All tests passed",
        lesson="Small verified components reduce integration risk",
        source="development-session-1",
        success=True,
        confidence=0.95,
        importance=0.95,
        provenance={"session_id": "session-1"},
        tags=["sahibex", "memory", "development"],
        occurred_at=base_time,
        recorded_at=base_time,
    )

    experience_2 = ExperienceMemory(
        experience_id="experience-002",
        task="Run memory regression",
        context="Phase 2 verification",
        action_taken="Executed regression tests",
        outcome="Regression completed successfully",
        lesson="Automated regression catches integration problems early",
        source="development-session-2",
        success=True,
        confidence=0.90,
        importance=0.85,
        provenance={"session_id": "session-2"},
        tags=["testing", "verification"],
        occurred_at=base_time + timedelta(seconds=1),
        recorded_at=base_time + timedelta(seconds=1),
    )

    experience_3 = ExperienceMemory(
        experience_id="experience-003",
        task="Debug memory test",
        context="Phase 2 debugging",
        action_taken="Inspected failed assertion",
        outcome="Test expectation was incorrect",
        lesson="Verify test assumptions before changing production code",
        source="development-session-3",
        success=False,
        confidence=0.88,
        importance=0.80,
        provenance={"session_id": "session-3"},
        tags=["debugging", "testing"],
        occurred_at=base_time + timedelta(seconds=2),
        recorded_at=base_time + timedelta(seconds=2),
    )

    check(
        experience_1.experience_id == "experience-001",
        "experience identity preserved",
    )

    check(
        experience_1.task == "Build SAHIBEX memory component",
        "experience task preserved",
    )

    check(
        experience_1.context == "Phase 2 memory development",
        "experience context preserved",
    )

    check(
        experience_1.action_taken.startswith("Implemented"),
        "experience action record preserved",
    )

    check(
        experience_1.outcome == "All tests passed",
        "experience outcome preserved",
    )

    check(
        experience_1.lesson.startswith("Small verified"),
        "experience lesson preserved",
    )

    check(
        experience_1.provenance["session_id"] == "session-1",
        "experience provenance preserved",
    )

    store = ExperienceMemoryStore(capacity=3)

    store.store(experience_1)
    store.store(experience_2)
    store.store(experience_3)

    check(
        store.count() == 3,
        "experience memory storage works",
    )

    check(
        store.get("experience-001") == experience_1,
        "experience memory retrieval works",
    )

    check(
        store.contains("experience-002"),
        "experience identity lookup works",
    )

    successful = store.successful()

    check(
        len(successful) == 2,
        "successful experience retrieval works",
    )

    check(
        successful[0].experience_id == "experience-001",
        "successful experience ranking works",
    )

    failed = store.failed()

    check(
        len(failed) == 1
        and failed[0].experience_id == "experience-003",
        "failed experience retrieval works",
    )

    tagged = store.by_tag("testing")

    check(
        len(tagged) == 2,
        "experience tag retrieval works",
    )

    searched = store.search("test expectation")

    check(
        len(searched) == 1
        and searched[0].experience_id == "experience-003",
        "experience search works",
    )

    recent = store.recent(limit=2)

    check(
        len(recent) == 2,
        "recent experience retrieval works",
    )

    check(
        recent[0].experience_id == "experience-003",
        "recent experience ordering works",
    )

    lessons = store.lessons()

    check(
        len(lessons) == 3,
        "experience lesson retrieval works",
    )

    old_experience = ExperienceMemory(
        experience_id="experience-004",
        task="Old task",
        context="Old context",
        action_taken="Old action",
        outcome="Old outcome",
        lesson="Old lesson",
        source="old-source",
        success=False,
        confidence=0.30,
        importance=0.20,
        provenance={"session_id": "old"},
        tags=["old"],
        occurred_at=base_time - timedelta(days=1),
        recorded_at=base_time - timedelta(days=1),
    )

    store.store(old_experience)

    check(
        not store.contains("experience-004"),
        "oldest experience is evicted when capacity is exceeded",
    )

    check(
        store.contains("experience-001"),
        "newer experience is retained",
    )

    try:
        experience_1.lesson = "changed"
        immutable_blocked = False
    except (AttributeError, TypeError):
        immutable_blocked = True

    check(
        immutable_blocked,
        "experience memory objects are immutable",
    )

    check(
        EXPERIENCE_MEMORY_VERSION == "P2-EX-1",
        "experience memory version is correct",
    )

    summary = store.summary()

    check(
        summary["preserves_context"] is True,
        "experience context preservation enabled",
    )

    check(
        summary["preserves_action_record"] is True,
        "experience action record preservation enabled",
    )

    check(
        summary["preserves_outcome"] is True,
        "experience outcome preservation enabled",
    )

    check(
        summary["preserves_lesson"] is True,
        "experience lesson preservation enabled",
    )

    check(
        summary["preserves_provenance"] is True,
        "experience provenance preservation enabled",
    )

    check(
        summary["supports_success_failure_retrieval"] is True,
        "success and failure retrieval enabled",
    )

    check(
        summary["supports_lesson_retrieval"] is True,
        "lesson retrieval enabled",
    )

    check(
        summary["supports_experience_search"] is True,
        "experience search capability enabled",
    )

    check(
        summary["grants_permission"] is False,
        "experience memory grants no permission",
    )

    check(
        summary["executes_actions"] is False,
        "experience memory executes no actions",
    )

    check(
        summary["modifies_constitution"] is False,
        "experience memory cannot modify constitution",
    )

    removed = store.remove("experience-002")

    check(
        removed is not None and not store.contains("experience-002"),
        "experience memory removal works",
    )

    store.clear()

    check(
        store.count() == 0,
        "experience memory cleanup works",
    )

    print("SAHIBEX PHASE 2 #47 EXPERIENCE MEMORY TEST: PASS")


if __name__ == "__main__":
    main()
