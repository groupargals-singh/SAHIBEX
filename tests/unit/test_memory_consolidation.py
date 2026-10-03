from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.memory_object import MemoryCandidate
from core.research.storage import ResearchStorage


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX 6I-7 MEMORY CONSOLIDATION TEST")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "research.db"
        storage = ResearchStorage(str(db_path))

        primary = MemoryCandidate(
            memory_id="memory-primary",
            content="User prefers step-by-step coding instructions.",
            memory_type="preference",
            source="user",
            importance=0.9,
            confidence=1.0,
            tags=["coding", "workflow"],
            metadata={"origin": "direct"},
        )

        duplicate = MemoryCandidate(
            memory_id="memory-duplicate",
            content="User prefers step-by-step coding instructions.",
            memory_type="preference",
            source="user",
            importance=0.8,
            confidence=0.95,
            tags=["coding"],
            metadata={"origin": "repeated"},
        )

        similar_but_different = MemoryCandidate(
            memory_id="memory-similar",
            content="User prefers concise coding instructions.",
            memory_type="preference",
            source="user",
            importance=0.8,
            confidence=0.95,
            tags=["coding"],
            metadata={},
        )

        storage.save_memory(primary)
        storage.save_memory(duplicate)
        storage.save_memory(similar_but_different)

        exact_matches = storage.find_duplicate_memories(primary)

        check(
            "memory-duplicate"
            in [memory.memory_id for memory in exact_matches],
            "exact duplicate detected",
        )

        check(
            "memory-similar"
            not in [memory.memory_id for memory in exact_matches],
            "similar but different memory preserved",
        )

        proposal = storage.plan_memory_consolidation(
            "memory-primary",
            "memory-duplicate",
        )

        check(
            proposal["safe_to_consolidate"] is True,
            "safe consolidation identified",
        )

        check(
            proposal["primary_memory_id"] == "memory-primary",
            "primary memory identity preserved",
        )

        check(
            proposal["duplicate_memory_id"] == "memory-duplicate",
            "duplicate identity preserved in proposal",
        )

        check(
            proposal["action"] == "PROPOSAL_ONLY",
            "consolidation remains proposal only",
        )

        check(
            storage.get_memory("memory-primary") is not None,
            "primary memory remains unchanged",
        )

        check(
            storage.get_memory("memory-duplicate") is not None,
            "duplicate memory remains unchanged",
        )

        check(
            storage.get_memory("memory-similar") is not None,
            "similar memory remains unchanged",
        )

        storage.close()

    print("SAHIBEX 6I-7 MEMORY CONSOLIDATION TEST: PASS")


if __name__ == "__main__":
    main()
