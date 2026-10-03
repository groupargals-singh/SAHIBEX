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
    print("SAHIBEX 6I-6 MEMORY LIFECYCLE TEST")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "research.db"
        storage = ResearchStorage(str(db_path))

        old_time = datetime.now(timezone.utc) - timedelta(days=10)

        memory = MemoryCandidate(
            memory_id="lifecycle-001",
            content="SAHIBEX lifecycle test memory.",
            memory_type="test",
            source="test",
            importance=0.8,
            confidence=0.9,
            tags=["lifecycle"],
            metadata={"test": True},
            created_at=old_time,
            updated_at=old_time,
            last_accessed_at=old_time,
        )

        storage.save_memory(memory)

        stored = storage.get_memory("lifecycle-001")

        check(
            stored is not None,
            "lifecycle memory stored",
        )

        check(
            stored.created_at == old_time,
            "created timestamp preserved",
        )

        check(
            stored.updated_at == old_time,
            "updated timestamp initially preserved",
        )

        check(
            stored.last_accessed_at == old_time,
            "last accessed timestamp initially preserved",
        )

        before_touch = datetime.now(timezone.utc)

        storage.touch_memory("lifecycle-001")

        after_touch = datetime.now(timezone.utc)

        touched = storage.get_memory("lifecycle-001")

        check(
            touched is not None,
            "touched memory retrieved",
        )

        check(
            touched.created_at == old_time,
            "created timestamp remains immutable",
        )

        check(
            touched.last_accessed_at >= before_touch,
            "last accessed timestamp updated",
        )

        check(
            touched.last_accessed_at <= after_touch,
            "last accessed timestamp is valid",
        )

        check(
            touched.updated_at >= before_touch,
            "updated timestamp refreshed",
        )

        check(
            touched.updated_at <= after_touch,
            "updated timestamp is valid",
        )

        check(
            touched.content == memory.content,
            "memory content preserved after lifecycle update",
        )

        check(
            touched.importance == memory.importance,
            "memory importance preserved after lifecycle update",
        )

        check(
            touched.confidence == memory.confidence,
            "memory confidence preserved after lifecycle update",
        )

        storage.close()

        restarted = ResearchStorage(str(db_path))

        restored = restarted.get_memory("lifecycle-001")

        check(
            restored is not None,
            "lifecycle state survives restart",
        )

        check(
            restored.created_at == old_time,
            "created timestamp survives restart",
        )

        check(
            restored.last_accessed_at >= before_touch,
            "last accessed state survives restart",
        )

        check(
            restored.updated_at >= before_touch,
            "updated state survives restart",
        )

        restarted.close()

    print("SAHIBEX 6I-6 MEMORY LIFECYCLE TEST: PASS")


if __name__ == "__main__":
    main()
