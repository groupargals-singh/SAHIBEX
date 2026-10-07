from core.research.memory_object import MemoryCandidate
from core.research.working_memory import (
    WORKING_MEMORY_VERSION,
    WorkingMemory,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def make_memory(
    memory_id: str,
    importance: float = 0.5,
    confidence: float = 0.5,
) -> MemoryCandidate:
    return MemoryCandidate(
        memory_id=memory_id,
        content=f"memory content {memory_id}",
        memory_type="working",
        source="test",
        importance=importance,
        confidence=confidence,
    )


def main() -> None:
    working = WorkingMemory(capacity=3)

    memory_1 = make_memory(
        "memory-001",
        importance=0.8,
        confidence=0.9,
    )

    memory_2 = make_memory(
        "memory-002",
        importance=0.7,
        confidence=0.8,
    )

    memory_3 = make_memory(
        "memory-003",
        importance=0.6,
        confidence=0.7,
    )

    working.activate(
        memory_1,
        priority=0.9,
    )

    check(
        working.contains("memory-001"),
        "memory activation works",
    )

    check(
        working.count() == 1,
        "active memory count works",
    )

    entry = working.get("memory-001")

    check(
        entry is not None,
        "active memory retrieval works",
    )

    check(
        entry.access_count == 2,
        "memory access tracking works",
    )

    working.activate(
        memory_2,
        priority=0.7,
    )

    working.activate(
        memory_3,
        priority=0.6,
    )

    check(
        working.count() == 3,
        "working-memory capacity accepts active set",
    )

    memory_4 = make_memory(
        "memory-004",
        importance=0.1,
        confidence=0.1,
    )

    working.activate(
        memory_4,
        priority=0.1,
    )

    check(
        working.count() == 3,
        "working-memory capacity is enforced",
    )

    check(
        working.contains("memory-001"),
        "high-value memory retained",
    )

    check(
        not working.contains("memory-004"),
        "low-value memory evicted",
    )

    ordered = working.active_memories()

    check(
        ordered[0].memory_id == "memory-001",
        "active memories ranked by working-memory value",
    )

    removed = working.remove("memory-003")

    check(
        removed is True,
        "memory removal works",
    )

    check(
        working.contains("memory-003") is False,
        "removed memory is no longer active",
    )

    promoted = working.promote_candidates()

    check(
        "memory-001" in {
            memory.memory_id
            for memory in promoted
        },
        "strong memory promotion candidate detected",
    )

    summary = working.summary()

    check(
        summary["version"] == WORKING_MEMORY_VERSION,
        "working-memory version is correct",
    )

    check(
        summary["bounded"] is True,
        "working memory is bounded",
    )

    check(
        summary["long_term_storage"] is False,
        "working memory is separate from long-term storage",
    )

    check(
        summary["promotion_is_proposal_only"] is True,
        "promotion is proposal-only",
    )

    check(
        summary["grants_permission"] is False,
        "working memory grants no permission",
    )

    check(
        summary["executes_actions"] is False,
        "working memory executes no actions",
    )

    check(
        summary["modifies_constitution"] is False,
        "working memory cannot modify constitution",
    )

    working.clear()

    check(
        working.count() == 0,
        "working-memory cleanup works",
    )

    print(
        "SAHIBEX PHASE 2 #43 WORKING MEMORY TEST: PASS"
    )


if __name__ == "__main__":
    main()
