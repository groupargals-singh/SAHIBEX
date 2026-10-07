from datetime import datetime, timedelta, timezone

from core.research.user_context_memory import (
    USER_CONTEXT_MEMORY_VERSION,
    UserContextMemory,
    UserContextMemoryStore,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    context_1 = UserContextMemory(
        context_id="context-001",
        context_type="preference",
        subject="coding workflow",
        value="Use Nano with complete file content",
        context="SAHIBEX development workflow",
        source="user-instruction-1",
        confidence=0.98,
        importance=0.95,
        provenance={"session_id": "session-1"},
        tags=["coding", "nano", "workflow"],
        created_at=base_time,
        updated_at=base_time,
    )

    context_2 = UserContextMemory(
        context_id="context-002",
        context_type="project",
        subject="SAHIBEX",
        value="Model-independent Mother Brain architecture",
        context="Main AI architecture project",
        source="project-context-1",
        confidence=0.96,
        importance=0.94,
        provenance={"session_id": "session-2"},
        tags=["sahibex", "project", "architecture"],
        created_at=base_time + timedelta(seconds=1),
        updated_at=base_time + timedelta(seconds=1),
    )

    context_3 = UserContextMemory(
        context_id="context-003",
        context_type="constraint",
        subject="testing",
        value="Do not claim PASS without actual terminal output",
        context="SAHIBEX verification workflow",
        source="user-instruction-2",
        confidence=0.99,
        importance=0.99,
        provenance={"session_id": "session-3"},
        tags=["testing", "verification"],
        created_at=base_time + timedelta(seconds=2),
        updated_at=base_time + timedelta(seconds=2),
    )

    check(
        context_1.context_id == "context-001",
        "user-context identity preserved",
    )

    check(
        context_1.context_type == "preference",
        "context type preserved",
    )

    check(
        context_1.subject == "coding workflow",
        "context subject preserved",
    )

    check(
        context_1.value.startswith("Use Nano"),
        "context value preserved",
    )

    check(
        context_1.context == "SAHIBEX development workflow",
        "context description preserved",
    )

    check(
        context_1.source == "user-instruction-1",
        "context source preserved",
    )

    check(
        context_1.provenance["session_id"] == "session-1",
        "context provenance preserved",
    )

    store = UserContextMemoryStore(capacity=3)

    store.store(context_1)
    store.store(context_2)
    store.store(context_3)

    check(
        store.count() == 3,
        "user-context memory storage works",
    )

    check(
        store.get("context-001") == context_1,
        "user-context memory retrieval works",
    )

    check(
        store.contains("context-002"),
        "user-context identity lookup works",
    )

    preference_items = store.by_type("preference")

    check(
        len(preference_items) == 1
        and preference_items[0].context_id == "context-001",
        "context-type retrieval works",
    )

    project_items = store.by_subject("SAHIBEX")

    check(
        len(project_items) == 1
        and project_items[0].context_id == "context-002",
        "subject retrieval works",
    )

    testing_items = store.by_tag("testing")

    check(
        len(testing_items) == 1
        and testing_items[0].context_id == "context-003",
        "context tag retrieval works",
    )

    searched = store.search("Nano")

    check(
        len(searched) == 1
        and searched[0].context_id == "context-001",
        "user-context search works",
    )

    important = store.important(minimum=0.98)

    check(
        len(important) == 1
        and important[0].context_id == "context-003",
        "important context retrieval works",
    )

    recent = store.recent(limit=2)

    check(
        len(recent) == 2,
        "recent context retrieval works",
    )

    check(
        recent[0].context_id == "context-003",
        "recent context ordering works",
    )

    all_context = store.all()

    check(
        len(all_context) == 3,
        "user-context memory listing works",
    )

    old_context = UserContextMemory(
        context_id="context-004",
        context_type="old",
        subject="old",
        value="old value",
        context="old context",
        source="old-source",
        confidence=0.20,
        importance=0.20,
        provenance={"session_id": "old"},
        tags=["old"],
        created_at=base_time - timedelta(days=1),
        updated_at=base_time - timedelta(days=1),
    )

    store.store(old_context)

    check(
        not store.contains("context-004"),
        "oldest context is evicted when capacity is exceeded",
    )

    check(
        store.contains("context-001"),
        "newer context is retained",
    )

    try:
        context_1.value = "changed"
        immutable_blocked = False
    except (AttributeError, TypeError):
        immutable_blocked = True

    check(
        immutable_blocked,
        "user-context memory objects are immutable",
    )

    check(
        USER_CONTEXT_MEMORY_VERSION == "P2-UCM-1",
        "user-context memory version is correct",
    )

    summary = store.summary()

    check(
        summary["supports_type_retrieval"] is True,
        "context-type retrieval capability enabled",
    )

    check(
        summary["supports_subject_retrieval"] is True,
        "subject retrieval capability enabled",
    )

    check(
        summary["supports_tag_retrieval"] is True,
        "context tag retrieval capability enabled",
    )

    check(
        summary["supports_context_search"] is True,
        "context search capability enabled",
    )

    check(
        summary["supports_importance_retrieval"] is True,
        "importance retrieval capability enabled",
    )

    check(
        summary["supports_recent_retrieval"] is True,
        "recent retrieval capability enabled",
    )

    check(
        summary["execution_authority"] is False,
        "user-context memory has no execution authority",
    )

    check(
        summary["grants_permission"] is False,
        "user-context memory grants no permission",
    )

    check(
        summary["executes_actions"] is False,
        "user-context memory executes no actions",
    )

    check(
        summary["modifies_constitution"] is False,
        "user-context memory cannot modify constitution",
    )

    removed = store.remove("context-002")

    check(
        removed is not None and not store.contains("context-002"),
        "user-context memory removal works",
    )

    store.clear()

    check(
        store.count() == 0,
        "user-context memory cleanup works",
    )

    print("SAHIBEX PHASE 2 #50 USER-CONTEXT MEMORY TEST: PASS")


if __name__ == "__main__":
    main()
