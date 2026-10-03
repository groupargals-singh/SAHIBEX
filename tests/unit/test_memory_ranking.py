from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.memory_object import MemoryCandidate
from core.research.storage import ResearchStorage


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX 6I-5 MEMORY RANKING TEST")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "research.db"
        storage = ResearchStorage(str(db_path))

        now = datetime.now(timezone.utc)

        memories = [
            MemoryCandidate(
                memory_id="rank-low",
                content="SAHIBEX development information.",
                memory_type="project",
                source="user",
                importance=0.40,
                confidence=0.70,
                tags=["sahibex"],
                metadata={},
                created_at=now - timedelta(days=30),
                updated_at=now - timedelta(days=30),
                last_accessed_at=now - timedelta(days=30),
            ),
            MemoryCandidate(
                memory_id="rank-high",
                content="SAHIBEX development information.",
                memory_type="project",
                source="user",
                importance=0.90,
                confidence=0.95,
                tags=["sahibex"],
                metadata={},
                created_at=now - timedelta(days=2),
                updated_at=now - timedelta(days=2),
                last_accessed_at=now - timedelta(days=2),
            ),
            MemoryCandidate(
                memory_id="rank-medium",
                content="SAHIBEX development information.",
                memory_type="project",
                source="user",
                importance=0.70,
                confidence=0.85,
                tags=["sahibex"],
                metadata={},
                created_at=now - timedelta(days=10),
                updated_at=now - timedelta(days=10),
                last_accessed_at=now - timedelta(days=10),
            ),
        ]

        for memory in memories:
            storage.save_memory(memory)

        results = storage.retrieve_memories("SAHIBEX")

        check(
            len(results) == 3,
            "all relevant memories retrieved",
        )

        result_ids = [memory.memory_id for memory in results]

        check(
            result_ids == [
                "rank-high",
                "rank-medium",
                "rank-low",
            ],
            "importance and confidence ranking",
        )

        high_confidence = storage.retrieve_memories(
            "SAHIBEX",
            min_confidence=0.90,
        )

        check(
            [memory.memory_id for memory in high_confidence]
            == ["rank-high"],
            "confidence threshold ranking",
        )

        high_importance = storage.retrieve_memories(
            "SAHIBEX",
            min_importance=0.80,
        )

        check(
            [memory.memory_id for memory in high_importance]
            == ["rank-high"],
            "importance threshold ranking",
        )

        repeated_a = storage.retrieve_memories("SAHIBEX")
        repeated_b = storage.retrieve_memories("SAHIBEX")

        check(
            [memory.memory_id for memory in repeated_a]
            == [memory.memory_id for memory in repeated_b],
            "ranking is deterministic",
        )

        storage.close()

        restarted = ResearchStorage(str(db_path))

        restored = restarted.retrieve_memories("SAHIBEX")

        check(
            [memory.memory_id for memory in restored]
            == [
                "rank-high",
                "rank-medium",
                "rank-low",
            ],
            "ranking survives restart",
        )

        restarted.close()

    print("SAHIBEX 6I-5 MEMORY RANKING TEST: PASS")


if __name__ == "__main__":
    main()
