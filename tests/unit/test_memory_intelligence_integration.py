from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.memory_object import MemoryCandidate
from core.research.storage import ResearchStorage


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX 6I-11 MEMORY INTELLIGENCE INTEGRATION TEST")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "research.db"

        storage = ResearchStorage(str(db_path))

        # ---------------------------------------------------------
        # 1. Create memories
        # ---------------------------------------------------------

        python_memory = MemoryCandidate(
            memory_id="memory-python",
            content="SAHIBEX uses Python for its core implementation.",
            memory_type="project_fact",
            source="user-confirmed",
            importance=0.95,
            confidence=0.95,
            tags=["sahibex", "python"],
            metadata={"category": "technology"},
        )

        termux_memory = MemoryCandidate(
            memory_id="memory-termux",
            content="SAHIBEX is developed in Termux.",
            memory_type="project_fact",
            source="user-confirmed",
            importance=0.90,
            confidence=0.90,
            tags=["sahibex", "termux"],
            metadata={"category": "development"},
        )

        trading_memory = MemoryCandidate(
            memory_id="memory-trading",
            content="Quantum-Bot is planned as a specialist trading brain.",
            memory_type="project_fact",
            source="user-confirmed",
            importance=0.85,
            confidence=0.90,
            tags=["quantum-bot", "trading"],
            metadata={"category": "specialist"},
        )

        storage.save_memory(python_memory)
        storage.save_memory(termux_memory)
        storage.save_memory(trading_memory)

        check(
            storage.memory_count() == 3,
            "three memories stored",
        )

        # ---------------------------------------------------------
        # 2. Retrieval
        # ---------------------------------------------------------

        results = storage.retrieve_memories(
            "Python",
        )

        check(
            len(results) >= 1,
            "Python memory retrieved",
        )

        check(
            results[0].memory_id == "memory-python",
            "retrieval identifies correct memory",
        )

        # ---------------------------------------------------------
        # 3. Ranking
        # ---------------------------------------------------------

        ranked = storage.retrieve_memories(
            "project_fact",
        )

        check(
            len(ranked) == 3,
            "all relevant memories retrieved",
        )

        check(
            ranked[0].importance >= ranked[-1].importance,
            "memory ranking is deterministic",
        )

        # ---------------------------------------------------------
        # 4. Lifecycle
        # ---------------------------------------------------------

        before = storage.get_memory(
            "memory-python"
        )

        check(
            before is not None,
            "memory available before lifecycle update",
        )

        touched = storage.touch_memory(
            "memory-python"
        )

        check(
            touched.memory_id == "memory-python",
            "lifecycle preserves memory identity",
        )

        check(
            touched.created_at == before.created_at,
            "lifecycle preserves created timestamp",
        )

        check(
            touched.last_accessed_at is not None,
            "lifecycle updates last accessed timestamp",
        )

        # ---------------------------------------------------------
        # 5. Duplicate detection
        # ---------------------------------------------------------

        duplicate = MemoryCandidate(
            memory_id="memory-python-duplicate",
            content="SAHIBEX uses Python for its core implementation.",
            memory_type="project_fact",
            source="user-confirmed",
            importance=0.80,
            confidence=0.80,
            tags=["sahibex", "python"],
            metadata={"category": "technology"},
        )

        storage.save_memory(duplicate)

        duplicates = storage.find_duplicate_memories(
            duplicate
        )

        check(
            any(
                memory.memory_id == "memory-python"
                for memory in duplicates
            ),
            "duplicate memory detected",
        )

        # ---------------------------------------------------------
        # 6. Consolidation proposal
        # ---------------------------------------------------------

        consolidation = storage.plan_memory_consolidation(
            "memory-python",
            "memory-python-duplicate",
        )

        check(
            consolidation["action"] == "PROPOSAL_ONLY",
            "consolidation remains proposal only",
        )

        check(
            consolidation["safe_to_consolidate"] is True,
            "safe duplicate consolidation identified",
        )

        # ---------------------------------------------------------
        # 7. Conflict detection
        # ---------------------------------------------------------

        conflicting_memory = MemoryCandidate(
            memory_id="memory-python-conflict",
            content="SAHIBEX uses Java as its core implementation.",
            memory_type="project_fact",
            source="unverified-source",
            importance=0.60,
            confidence=0.40,
            tags=["sahibex", "python"],
            metadata={"category": "technology"},
        )

        storage.save_memory(conflicting_memory)

        conflict = storage.detect_memory_conflict(
            python_memory,
            conflicting_memory,
        )

        check(
            conflict["conflict"] is True,
            "memory conflict detected",
        )

        check(
            conflict["status"] == "UNRESOLVED",
            "memory conflict remains unresolved",
        )

        # ---------------------------------------------------------
        # 8. Conflict resolution proposal
        # ---------------------------------------------------------

        resolution = storage.plan_memory_conflict_resolution(
            "memory-python",
            "memory-python-conflict",
            "memory-python",
            "independent-verification-source",
        )

        check(
            resolution["action"] == "PROPOSAL_ONLY",
            "conflict resolution remains proposal only",
        )

        check(
            resolution["selected_memory_id"]
            == "memory-python",
            "selected memory identity preserved",
        )

        check(
            resolution["rejected_memory_id"]
            == "memory-python-conflict",
            "rejected memory identity preserved",
        )

        # ---------------------------------------------------------
        # 9. Verification
        # ---------------------------------------------------------

        verification = storage.record_memory_verification(
            "memory-python",
            "VERIFIED",
            "verification-source-python",
            "Independent evidence confirms the memory claim.",
        )

        check(
            verification["memory_id"]
            == "memory-python",
            "verification preserves memory identity",
        )

        check(
            verification["status"] == "VERIFIED",
            "verification status preserved",
        )

        verification_context = storage.get_memory_verification(
            "memory-python"
        )

        check(
            verification_context is not None,
            "memory verification context retrieved",
        )

        check(
            verification_context["status"] == "VERIFIED",
            "verified status retrieved",
        )

        # ---------------------------------------------------------
        # 10. Non-destructive conflict preservation
        # ---------------------------------------------------------

        preserved_python = storage.get_memory(
            "memory-python"
        )

        preserved_conflict = storage.get_memory(
            "memory-python-conflict"
        )

        check(
            preserved_python is not None,
            "selected memory remains stored",
        )

        check(
            preserved_conflict is not None,
            "conflicting memory remains stored",
        )

        check(
            preserved_conflict.content
            == "SAHIBEX uses Java as its core implementation.",
            "conflicting memory content preserved",
        )

        # ---------------------------------------------------------
        # 11. Restart persistence
        # ---------------------------------------------------------

        storage.close()

        restarted = ResearchStorage(
            str(db_path)
        )

        restored_python = restarted.get_memory(
            "memory-python"
        )

        check(
            restored_python is not None,
            "memory survives restart",
        )

        check(
            restored_python.content
            == "SAHIBEX uses Python for its core implementation.",
            "memory content survives restart",
        )

        restored_verification = (
            restarted.get_memory_verification(
                "memory-python"
            )
        )

        check(
            restored_verification is not None,
            "verification survives restart",
        )

        check(
            restored_verification["status"]
            == "VERIFIED",
            "verification status survives restart",
        )

        restored_conflict = restarted.get_memory(
            "memory-python-conflict"
        )

        check(
            restored_conflict is not None,
            "conflict memory survives restart",
        )

        check(
            restored_conflict.content
            == "SAHIBEX uses Java as its core implementation.",
            "conflict content survives restart",
        )

        restarted.close()

    print(
        "SAHIBEX 6I-11 MEMORY INTELLIGENCE INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
