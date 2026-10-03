from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.memory_object import MemoryCandidate
from core.research.storage import ResearchStorage


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX 6I-9 MEMORY CONFLICT RESOLUTION TEST")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "research.db"
        storage = ResearchStorage(str(db_path))

        memory_a = MemoryCandidate(
            memory_id="resolution-a",
            content="SAHIBEX uses Python for its core implementation.",
            memory_type="project_fact",
            source="source-a",
            importance=0.9,
            confidence=0.9,
            tags=["sahibex", "python"],
            metadata={"claim": "python"},
        )

        memory_b = MemoryCandidate(
            memory_id="resolution-b",
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
            "conflict detected before resolution",
        )

        resolution = storage.plan_memory_conflict_resolution(
            "resolution-a",
            "resolution-b",
            "resolution-a",
            "verified_source_a",
        )

        check(
            resolution["action"] == "PROPOSAL_ONLY",
            "resolution remains proposal only",
        )

        check(
            resolution["status"] == "VERIFIED",
            "resolution status is verified",
        )

        check(
            resolution["selected_memory_id"] == "resolution-a",
            "selected memory identity preserved",
        )

        check(
            resolution["rejected_memory_id"] == "resolution-b",
            "rejected memory identity preserved",
        )

        check(
            resolution["verification_source"] == "verified_source_a",
            "verification source preserved",
        )

        check(
            storage.get_memory("resolution-a") is not None,
            "selected memory remains stored",
        )

        check(
            storage.get_memory("resolution-b") is not None,
            "rejected memory remains stored",
        )

        invalid = storage.plan_memory_conflict_resolution(
            "resolution-a",
            "resolution-b",
            "resolution-a",
            "verified_source_a",
        )

        check(
            invalid["selected_memory_id"] == "resolution-a",
            "resolution proposal remains deterministic",
        )

        storage.close()

    print("SAHIBEX 6I-9 MEMORY CONFLICT RESOLUTION TEST: PASS")


if __name__ == "__main__":
    main()
