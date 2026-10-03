from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.memory_object import MemoryCandidate
from core.research.storage import ResearchStorage


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX 6I-8 MEMORY CONFLICT TEST")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "research.db"
        storage = ResearchStorage(str(db_path))

        memory_a = MemoryCandidate(
            memory_id="conflict-a",
            content="SAHIBEX uses Python for its core implementation.",
            memory_type="project_fact",
            source="source-a",
            importance=0.9,
            confidence=0.9,
            tags=["sahibex", "python"],
            metadata={"claim": "python"},
        )

        memory_b = MemoryCandidate(
            memory_id="conflict-b",
            content="SAHIBEX uses another language for its core implementation.",
            memory_type="project_fact",
            source="source-b",
            importance=0.8,
            confidence=0.8,
            tags=["sahibex"],
            metadata={"claim": "other-language"},
        )

        storage.save_memory(memory_a)
        storage.save_memory(memory_b)

        conflict = storage.detect_memory_conflict(
            memory_a,
            memory_b,
        )

        check(
            conflict["conflict"] is True,
            "memory conflict detected",
        )

        check(
            conflict["status"] == "UNRESOLVED",
            "conflict remains unresolved",
        )

        check(
            conflict["memory_a_id"] == "conflict-a",
            "first memory identity preserved",
        )

        check(
            conflict["memory_b_id"] == "conflict-b",
            "second memory identity preserved",
        )

        check(
            conflict["action"] == "REQUIRES_VERIFICATION",
            "conflict requires verification",
        )

        check(
            storage.get_memory("conflict-a") is not None,
            "first conflicting memory preserved",
        )

        check(
            storage.get_memory("conflict-b") is not None,
            "second conflicting memory preserved",
        )

        identical = storage.detect_memory_conflict(
            memory_a,
            memory_a,
        )

        check(
            identical["conflict"] is False,
            "identical memory is not a conflict",
        )

        storage.close()

    print("SAHIBEX 6I-8 MEMORY CONFLICT TEST: PASS")


if __name__ == "__main__":
    main()
