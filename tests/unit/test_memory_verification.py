from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.memory_object import MemoryCandidate
from core.research.storage import ResearchStorage


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX 6I-10 MEMORY VERIFICATION TEST")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "research.db"
        storage = ResearchStorage(str(db_path))

        memory = MemoryCandidate(
            memory_id="verification-memory",
            content="SAHIBEX uses Python for its core implementation.",
            memory_type="project_fact",
            source="memory-source",
            importance=0.9,
            confidence=0.7,
            tags=["sahibex", "python"],
            metadata={"claim": "python"},
        )

        storage.save_memory(memory)

        verification = storage.record_memory_verification(
            "verification-memory",
            "VERIFIED",
            "verified-source-001",
            "Independent evidence confirms the memory claim.",
        )

        check(
            verification["memory_id"] == "verification-memory",
            "memory identity preserved",
        )

        check(
            verification["status"] == "VERIFIED",
            "verification status preserved",
        )

        check(
            verification["evidence_id"] == "verified-source-001",
            "verification evidence identity preserved",
        )

        check(
            verification["reason"]
            == "Independent evidence confirms the memory claim.",
            "verification reason preserved",
        )

        stored = storage.get_memory("verification-memory")

        check(
            stored is not None,
            "verified memory remains stored",
        )

        context = storage.get_memory_verification(
            "verification-memory"
        )

        check(
            context["status"] == "VERIFIED",
            "stored verification status preserved",
        )

        check(
            context["evidence_id"] == "verified-source-001",
            "stored evidence identity preserved",
        )

        check(
            context["reason"]
            == "Independent evidence confirms the memory claim.",
            "stored verification reason preserved",
        )

        storage.close()

        restarted = ResearchStorage(str(db_path))

        restored_context = restarted.get_memory_verification(
            "verification-memory"
        )

        check(
            restored_context["status"] == "VERIFIED",
            "verification survives restart",
        )

        check(
            restored_context["evidence_id"]
            == "verified-source-001",
            "verification evidence survives restart",
        )

        check(
            restored_context["reason"]
            == "Independent evidence confirms the memory claim.",
            "verification reason survives restart",
        )

        restarted.close()

    print("SAHIBEX 6I-10 MEMORY VERIFICATION TEST: PASS")


if __name__ == "__main__":
    main()
