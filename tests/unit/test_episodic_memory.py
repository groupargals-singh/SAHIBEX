from datetime import datetime, timezone, timedelta

from core.research.episodic_memory import (
    EPISODIC_MEMORY_VERSION,
    EpisodicMemory,
    EpisodicMemoryStore,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    base_time = datetime(
        2026,
        1,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    episode_1 = EpisodicMemory(
        episode_id="episode-001",
        event="SAHIBEX completed a memory test",
        context="Phase 2 development",
        source="test",
        occurred_at=base_time,
        participants=["user", "SAHIBEX"],
        outcome="PASS",
        importance=0.9,
        confidence=0.95,
        provenance={"test": "episodic_memory"},
        tags=["sahibex", "memory", "phase2"],
    )

    check(
        episode_1.episode_id == "episode-001",
        "episode identity preserved",
    )

    check(
        episode_1.event == "SAHIBEX completed a memory test",
        "event preserved",
    )

    check(
        episode_1.context == "Phase 2 development",
        "episode context preserved",
    )

    check(
        episode_1.occurred_at == base_time,
        "event timestamp preserved",
    )

    check(
        episode_1.participants == ["user", "SAHIBEX"],
        "participants preserved",
    )

    check(
        episode_1.outcome == "PASS",
        "episode outcome preserved",
    )

    check(
        episode_1.provenance["test"] == "episodic_memory",
        "episode provenance preserved",
    )

    store = EpisodicMemoryStore(capacity=3)

    store.store(episode_1)

    check(
        store.contains("episode-001"),
        "episode storage works",
    )

    check(
        store.get("episode-001") == episode_1,
        "episode retrieval works",
    )

    episode_2 = EpisodicMemory(
        episode_id="episode-002",
        event="SAHIBEX performed another memory operation",
        context="Phase 2 development",
        source="test",
        occurred_at=base_time + timedelta(minutes=5),
        participants=["SAHIBEX"],
        outcome="PASS",
        importance=0.7,
        confidence=0.8,
        tags=["memory"],
    )

    episode_3 = EpisodicMemory(
        episode_id="episode-003",
        event="User reviewed the result",
        context="Phase 2 development",
        source="test",
        occurred_at=base_time + timedelta(minutes=10),
        participants=["user"],
        outcome="reviewed",
        importance=0.6,
        confidence=0.9,
        tags=["review"],
    )

    store.store(episode_2)
    store.store(episode_3)

    check(
        store.count() == 3,
        "episodic memory count works",
    )

    participant_results = store.by_participant("user")

    check(
        len(participant_results) == 2,
        "participant retrieval works",
    )

    tag_results = store.by_tag("memory")

    check(
        len(tag_results) == 2,
        "tag retrieval works",
    )

    recent = store.recent(limit=2)

    check(
        recent[0].episode_id == "episode-003",
        "recent episode ordering works",
    )

    episode_4 = EpisodicMemory(
        episode_id="episode-004",
        event="Oldest capacity test episode",
        context="capacity test",
        source="test",
        occurred_at=base_time - timedelta(days=1),
    )

    store.store(episode_4)

    check(
        store.count() == 3,
        "episodic capacity is enforced",
    )

    check(
        not store.contains("episode-004"),
        "oldest episode is evicted when capacity is exceeded",
    )

    check(
        store.contains("episode-001"),
        "newer episode is retained",
    )
    summary = store.summary()

    check(
        summary["version"] == EPISODIC_MEMORY_VERSION,
        "episodic memory version is correct",
    )

    check(
        summary["immutable_episode_objects"] is True,
        "episode objects are immutable",
    )

    check(
        summary["preserves_event_time"] is True,
        "event time preservation enabled",
    )

    check(
        summary["preserves_context"] is True,
        "context preservation enabled",
    )

    check(
        summary["preserves_provenance"] is True,
        "provenance preservation enabled",
    )

    check(
        summary["grants_permission"] is False,
        "episodic memory grants no permission",
    )

    check(
        summary["executes_actions"] is False,
        "episodic memory executes no actions",
    )

    check(
        summary["modifies_constitution"] is False,
        "episodic memory cannot modify constitution",
    )

    removed = store.remove("episode-002")

    check(
        removed is True,
        "episode removal works",
    )

    store.clear()

    check(
        store.count() == 0,
        "episodic memory cleanup works",
    )

    print(
        "SAHIBEX PHASE 2 #44 EPISODIC MEMORY TEST: PASS"
    )


if __name__ == "__main__":
    main()
