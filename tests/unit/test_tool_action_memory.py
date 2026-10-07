from __future__ import annotations

from core.research.tool_action_memory import (
    ToolActionMemory,
    ToolActionMemoryStore,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_memory(
    memory_id: str = "tam-001",
    *,
    tool: str = "read_file",
    action: str = "read",
    success: bool = True,
    error: str | None = None,
) -> ToolActionMemory:
    return ToolActionMemory(
        memory_id=memory_id,
        tool=tool,
        action=action,
        context="Inspect SAHIBEX source.",
        input_summary="core/brain/master_brain.py",
        result_summary=(
            "Source content returned."
            if success
            else "Tool execution failed."
        ),
        success=success,
        verification_status=(
            "VERIFIED" if success else "FAILED"
        ),
        error=error,
        lesson=(
            "read_file successfully retrieves source."
            if success
            else "Retry or alternative inspection may be required."
        ),
        source="tool_intelligence",
        confidence=0.9,
        importance=0.8,
        provenance={"test": "phase-2-52"},
        tags=["tool", "read", "sahibex"],
    )


def main() -> None:
    # -------------------------------------------------
    # 1. Identity and contract
    # -------------------------------------------------
    memory = make_memory()

    check(
        memory.memory_id == "tam-001",
        "Memory identity must be preserved.",
    )
    check(
        memory.tool == "read_file",
        "Tool identity must be preserved.",
    )
    check(
        memory.action == "read",
        "Action must be preserved.",
    )
    check(
        memory.success is True,
        "Success state must be preserved.",
    )
    check(
        memory.verification_status == "VERIFIED",
        "Verification status must be preserved.",
    )
    check(
        memory.lesson != "",
        "Lesson must be preserved.",
    )
    check(
        memory.provenance["test"] == "phase-2-52",
        "Provenance must be preserved.",
    )

    # -------------------------------------------------
    # 2. Store and retrieval
    # -------------------------------------------------
    store = ToolActionMemoryStore(capacity=8)

    stored = store.store(memory)

    check(
        stored is memory,
        "Store must return the stored memory.",
    )
    check(
        store.contains("tam-001"),
        "Stored memory must be retrievable by ID.",
    )
    check(
        store.get("tam-001") == memory,
        "Retrieved memory must match original.",
    )
    check(
        store.count() == 1,
        "Store count must be correct.",
    )

    # -------------------------------------------------
    # 3. Tool/action filtering
    # -------------------------------------------------
    store.store(
        make_memory(
            "tam-002",
            tool="list_directory",
            action="inspect",
        )
    )

    store.store(
        make_memory(
            "tam-003",
            tool="read_file",
            action="read",
        )
    )

    check(
        len(store.by_tool("read_file")) == 2,
        "Tool filtering must work.",
    )
    check(
        len(store.by_action("read")) == 2,
        "Action filtering must work.",
    )

    # -------------------------------------------------
    # 4. Failure memory
    # -------------------------------------------------
    failure = make_memory(
        "tam-004",
        success=False,
        error="FileNotFoundError: missing.txt",
    )

    store.store(failure)

    failed = store.by_success(False)

    check(
        len(failed) == 1,
        "Failure filtering must work.",
    )
    check(
        failed[0].error == "FileNotFoundError: missing.txt",
        "Failure error must be preserved.",
    )

    # -------------------------------------------------
    # 5. Verification and tag retrieval
    # -------------------------------------------------
    verified = store.by_verification("VERIFIED")

    check(
        len(verified) >= 1,
        "Verification filtering must work.",
    )

    tagged = store.by_tag("sahibex")

    check(
        len(tagged) == 4,
        "Tag filtering must work.",
    )

    # -------------------------------------------------
    # 6. Search
    # -------------------------------------------------
    results = store.search("missing.txt")

    check(
        len(results) == 1,
        "Search must find matching failure memory.",
    )
    check(
        results[0].memory_id == "tam-004",
        "Search must return correct memory.",
    )

    # -------------------------------------------------
    # 7. Lessons and effective actions
    # -------------------------------------------------
    lessons = store.lessons()

    check(
        len(lessons) >= 1,
        "Lessons must be retrievable.",
    )

    effective = store.effective_actions(
        minimum_confidence=0.8,
    )

    check(
        len(effective) >= 3,
        "Effective successful actions must be retrievable.",
    )

    # -------------------------------------------------
    # 8. Recent memories
    # -------------------------------------------------
    recent = store.recent(limit=3)

    check(
        len(recent) == 3,
        "Recent memory limit must work.",
    )

    # -------------------------------------------------
    # 9. Capacity / eviction
    # -------------------------------------------------
    small = ToolActionMemoryStore(capacity=2)

    small.store(make_memory("capacity-1"))
    small.store(make_memory("capacity-2"))
    small.store(make_memory("capacity-3"))

    check(
        small.count() == 2,
        "Capacity must be enforced.",
    )
    check(
        not small.contains("capacity-1"),
        "Oldest memory must be evicted.",
    )

    # -------------------------------------------------
    # 10. Duplicate identity protection
    # -------------------------------------------------
    try:
        store.store(make_memory("tam-001"))
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Duplicate memory IDs must be rejected."
        )

    # -------------------------------------------------
    # 11. Immutability
    # -------------------------------------------------
    try:
        memory.tool = "changed"  # type: ignore[misc]
    except Exception:
        pass
    else:
        raise AssertionError(
            "ToolActionMemory must be immutable."
        )

    # -------------------------------------------------
    # 12. Invalid successful state
    # -------------------------------------------------
    try:
        ToolActionMemory(
            memory_id="invalid-success",
            tool="read_file",
            action="read",
            context="test",
            input_summary="test",
            result_summary="test",
            success=True,
            verification_status="VERIFIED",
            error="unexpected",
            lesson="test",
            source="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Successful memory with error must be rejected."
        )

    # -------------------------------------------------
    # 13. Invalid failed state
    # -------------------------------------------------
    try:
        ToolActionMemory(
            memory_id="invalid-failure",
            tool="read_file",
            action="read",
            context="test",
            input_summary="test",
            result_summary="test",
            success=False,
            verification_status="FAILED",
            error=None,
            lesson="test",
            source="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Failed memory without error must be rejected."
        )

    # -------------------------------------------------
    # 14. Security boundary
    # -------------------------------------------------
    summary = store.summary()

    check(
        summary["execution_allowed"] is False,
        "Memory must not execute tools.",
    )
    check(
        summary["permission_allowed"] is False,
        "Memory must not grant permission.",
    )
    check(
        summary["credential_access"] is False,
        "Memory must not access credentials.",
    )
    check(
        summary["constitution_change_allowed"] is False,
        "Memory must not change Constitution.",
    )
    check(
        summary["authority"] is False,
        "Memory must have no authority.",
    )

    print(
        "SAHIBEX PHASE 2 #52 TOOL/ACTION MEMORY TEST: PASS"
    )


if __name__ == "__main__":
    main()
