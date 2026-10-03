from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.memory_object import MemoryCandidate
from core.research.storage import ResearchStorage


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX 6I-4 MEMORY RETRIEVAL TEST")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "research.db"
        storage = ResearchStorage(str(db_path))

        memories = [
            MemoryCandidate(
                memory_id="mem-python",
                content="User is building SAHIBEX with Python.",
                memory_type="project",
                source="user",
                importance=0.9,
                confidence=1.0,
                tags=["sahibex", "python", "development"],
                metadata={"project": "SAHIBEX"},
            ),
            MemoryCandidate(
                memory_id="mem-termux",
                content="User develops SAHIBEX in Termux.",
                memory_type="environment",
                source="user",
                importance=0.8,
                confidence=0.95,
                tags=["sahibex", "termux"],
                metadata={"project": "SAHIBEX"},
            ),
            MemoryCandidate(
                memory_id="mem-trading",
                content="Quantum-Bot is intended to become a trading specialist brain.",
                memory_type="project",
                source="user",
                importance=0.7,
                confidence=0.9,
                tags=["quantum-bot", "trading"],
                metadata={"project": "quantum-bot"},
            ),
        ]

        for memory in memories:
            storage.save_memory(memory)

        results = storage.retrieve_memories("SAHIBEX")

        check(
            len(results) >= 2,
            "relevant memories retrieved",
        )

        result_ids = [memory.memory_id for memory in results]

        check(
            "mem-python" in result_ids,
            "Python memory retrieved",
        )

        check(
            "mem-termux" in result_ids,
            "Termux memory retrieved",
        )

        check(
            "mem-trading" not in result_ids,
            "unrelated trading memory excluded",
        )

        python_results = storage.retrieve_memories("Python")

        check(
            len(python_results) == 1,
            "specific memory query",
        )

        check(
            python_results[0].memory_id == "mem-python",
            "specific query returns correct memory",
        )

        tag_results = storage.retrieve_memories("termux")

        check(
            len(tag_results) == 1,
            "tag-related retrieval",
        )

        check(
            tag_results[0].memory_id == "mem-termux",
            "tag-related memory identity",
        )

        project_results = storage.retrieve_memories(
            "SAHIBEX",
            memory_type="project",
        )

        check(
            len(project_results) == 1,
            "memory type filtering",
        )

        check(
            project_results[0].memory_id == "mem-python",
            "memory type filter preserves correct result",
        )

        confidence_results = storage.retrieve_memories(
            "SAHIBEX",
            min_confidence=0.98,
        )

        check(
            len(confidence_results) == 1,
            "minimum confidence filtering",
        )

        check(
            confidence_results[0].memory_id == "mem-python",
            "confidence filter preserves correct result",
        )

        important_results = storage.retrieve_memories(
            "SAHIBEX",
            min_importance=0.85,
        )

        check(
            len(important_results) == 1,
            "minimum importance filtering",
        )

        check(
            important_results[0].memory_id == "mem-python",
            "importance filter preserves correct result",
        )

        repeated_a = storage.retrieve_memories("SAHIBEX")
        repeated_b = storage.retrieve_memories("SAHIBEX")

        check(
            [m.memory_id for m in repeated_a]
            == [m.memory_id for m in repeated_b],
            "deterministic retrieval ordering",
        )

        storage.close()

        restarted = ResearchStorage(str(db_path))

        restored_results = restarted.retrieve_memories("SAHIBEX")

        check(
            len(restored_results) >= 2,
            "retrieval survives restart",
        )

        check(
            "mem-python"
            in [memory.memory_id for memory in restored_results],
            "retrieved memory survives restart",
        )

        restarted.close()

    print("SAHIBEX 6I-4 MEMORY RETRIEVAL TEST: PASS")


if __name__ == "__main__":
    main()
