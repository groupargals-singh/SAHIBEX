from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.memory_object import MemoryCandidate
from core.research.storage import ResearchStorage


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX 6I-3 MEMORY STORAGE TEST")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "research.db"

        memory = MemoryCandidate(
            memory_id="mem-001",
            content="User prefers step-by-step implementation.",
            memory_type="preference",
            source="user",
            importance=0.9,
            confidence=1.0,
            tags=["preference", "workflow"],
            metadata={"scope": "development"},
        )

        storage = ResearchStorage(str(db_path))

        storage.save_memory(memory)

        stored = storage.get_memory("mem-001")

        check(stored is not None, "memory stored")
        check(
            stored.memory_id == memory.memory_id,
            "memory identity preserved",
        )
        check(
            stored.content == memory.content,
            "memory content preserved",
        )
        check(
            stored.memory_type == memory.memory_type,
            "memory type preserved",
        )
        check(
            stored.source == memory.source,
            "memory source preserved",
        )
        check(
            stored.importance == memory.importance,
            "memory importance preserved",
        )
        check(
            stored.confidence == memory.confidence,
            "memory confidence preserved",
        )
        check(
            stored.tags == memory.tags,
            "memory tags preserved",
        )
        check(
            stored.metadata == memory.metadata,
            "memory metadata preserved",
        )

        check(
            storage.memory_count() == 1,
            "memory count",
        )

        memories = storage.list_memories()

        check(
            len(memories) == 1,
            "memory enumeration",
        )
        check(
            memories[0].memory_id == "mem-001",
            "enumerated memory identity preserved",
        )

        storage.close()

        restarted = ResearchStorage(str(db_path))

        restored = restarted.get_memory("mem-001")

        check(
            restored is not None,
            "memory survives restart",
        )
        check(
            restored.content == memory.content,
            "memory content survives restart",
        )
        check(
            restored.memory_type == memory.memory_type,
            "memory type survives restart",
        )
        check(
            restored.tags == memory.tags,
            "memory tags survive restart",
        )
        check(
            restored.metadata == memory.metadata,
            "memory metadata survives restart",
        )

        check(
            restarted.memory_count() == 1,
            "memory count survives restart",
        )

        restarted.close()

    print("SAHIBEX 6I-3 MEMORY STORAGE TEST: PASS")


if __name__ == "__main__":
    main()
