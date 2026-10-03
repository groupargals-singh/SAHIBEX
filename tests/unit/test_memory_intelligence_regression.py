from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.memory_object import MemoryCandidate
from core.research.storage import ResearchStorage


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX 6I-12 FULL MEMORY INTELLIGENCE REGRESSION TEST")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "research.db"

        # =========================================================
        # STORAGE
        # =========================================================

        storage = ResearchStorage(str(db_path))

        memory_a = MemoryCandidate(
            memory_id="regression-python",
            content="SAHIBEX uses Python for its core implementation.",
            memory_type="project_fact",
            source="user-confirmed",
            importance=0.95,
            confidence=0.95,
            tags=["sahibex", "python"],
            metadata={"category": "technology"},
        )

        memory_b = MemoryCandidate(
            memory_id="regression-termux",
            content="SAHIBEX is developed in Termux.",
            memory_type="project_fact",
            source="user-confirmed",
            importance=0.90,
            confidence=0.90,
            tags=["sahibex", "termux"],
            metadata={"category": "development"},
        )

        memory_c = MemoryCandidate(
            memory_id="regression-quantum",
            content="Quantum-Bot is planned as a specialist trading brain.",
            memory_type="project_fact",
            source="user-confirmed",
            importance=0.85,
            confidence=0.90,
            tags=["quantum-bot", "trading"],
            metadata={"category": "specialist"},
        )

        storage.save_memory(memory_a)
        storage.save_memory(memory_b)
        storage.save_memory(memory_c)

        check(
            storage.memory_count() == 3,
            "memory storage regression",
        )

        # =========================================================
        # RETRIEVAL
        # =========================================================

        python_results = storage.retrieve_memories("Python")

        check(
            len(python_results) >= 1,
            "memory retrieval regression",
        )

        check(
            python_results[0].memory_id == "regression-python",
            "retrieval identity regression",
        )

        # =========================================================
        # RANKING
        # =========================================================

        ranked = storage.retrieve_memories("project_fact")

        check(
            len(ranked) == 3,
            "memory ranking retrieval regression",
        )

        check(
            ranked[0].importance >= ranked[-1].importance,
            "memory ranking order regression",
        )

        # =========================================================
        # FILTERING
        # =========================================================

        confidence_filtered = storage.retrieve_memories(
            "project_fact",
            min_confidence=0.95,
        )

        check(
            len(confidence_filtered) == 1,
            "confidence filtering regression",
        )

        check(
            confidence_filtered[0].memory_id
            == "regression-python",
            "confidence filtering identity regression",
        )

        importance_filtered = storage.retrieve_memories(
            "project_fact",
            min_importance=0.95,
        )

        check(
            len(importance_filtered) == 1,
            "importance filtering regression",
        )

        check(
            importance_filtered[0].memory_id
            == "regression-python",
            "importance filtering identity regression",
        )

        # =========================================================
        # LIFECYCLE
        # =========================================================

        before_touch = storage.get_memory(
            "regression-python"
        )

        check(
            before_touch is not None,
            "memory lifecycle source exists",
        )

        touched = storage.touch_memory(
            "regression-python"
        )

        check(
            touched.memory_id == "regression-python",
            "memory lifecycle identity regression",
        )

        check(
            touched.created_at == before_touch.created_at,
            "memory created timestamp regression",
        )

        check(
            touched.last_accessed_at is not None,
            "memory access timestamp regression",
        )

        # =========================================================
        # DEDUPLICATION
        # =========================================================

        duplicate = MemoryCandidate(
            memory_id="regression-python-duplicate",
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
                item.memory_id == "regression-python"
                for item in duplicates
            ),
            "duplicate detection regression",
        )

        consolidation = storage.plan_memory_consolidation(
            "regression-python",
            "regression-python-duplicate",
        )

        check(
            consolidation["action"] == "PROPOSAL_ONLY",
            "consolidation proposal regression",
        )

        check(
            consolidation["safe_to_consolidate"] is True,
            "safe consolidation regression",
        )

        # =========================================================
        # CONFLICT DETECTION
        # =========================================================

        conflicting = MemoryCandidate(
            memory_id="regression-python-conflict",
            content="SAHIBEX uses Java for its core implementation.",
            memory_type="project_fact",
            source="unverified-source",
            importance=0.60,
            confidence=0.40,
            tags=["sahibex", "python"],
            metadata={"category": "technology"},
        )

        storage.save_memory(conflicting)

        conflict = storage.detect_memory_conflict(
            memory_a,
            conflicting,
        )

        check(
            conflict["conflict"] is True,
            "conflict detection regression",
        )

        check(
            conflict["status"] == "UNRESOLVED",
            "conflict unresolved-state regression",
        )

        # =========================================================
        # CONFLICT RESOLUTION
        # =========================================================

        resolution = storage.plan_memory_conflict_resolution(
            "regression-python",
            "regression-python-conflict",
            "regression-python",
            "independent-verification-source",
        )

        check(
            resolution["action"] == "PROPOSAL_ONLY",
            "conflict resolution proposal regression",
        )

        check(
            resolution["selected_memory_id"]
            == "regression-python",
            "selected memory regression",
        )

        check(
            resolution["rejected_memory_id"]
            == "regression-python-conflict",
            "rejected memory regression",
        )

        # =========================================================
        # VERIFICATION
        # =========================================================

        verification = storage.record_memory_verification(
            "regression-python",
            "VERIFIED",
            "regression-verification-source",
            "Independent evidence confirms the memory claim.",
        )

        check(
            verification["memory_id"]
            == "regression-python",
            "memory verification identity regression",
        )

        check(
            verification["status"] == "VERIFIED",
            "memory verification status regression",
        )

        verification_context = (
            storage.get_memory_verification(
                "regression-python"
            )
        )

        check(
            verification_context is not None,
            "memory verification retrieval regression",
        )

        check(
            verification_context["status"] == "VERIFIED",
            "stored verification regression",
        )

        # =========================================================
        # NON-DESTRUCTIVE SAFETY
        # =========================================================

        selected_after_resolution = storage.get_memory(
            "regression-python"
        )

        rejected_after_resolution = storage.get_memory(
            "regression-python-conflict"
        )

        duplicate_after_consolidation = storage.get_memory(
            "regression-python-duplicate"
        )

        check(
            selected_after_resolution is not None,
            "selected memory remains preserved",
        )

        check(
            rejected_after_resolution is not None,
            "conflicting memory remains preserved",
        )

        check(
            duplicate_after_consolidation is not None,
            "duplicate remains preserved as proposal-only",
        )

        # =========================================================
        # RESTART
        # =========================================================

        storage.close()

        restarted = ResearchStorage(
            str(db_path)
        )

        restored_python = restarted.get_memory(
            "regression-python"
        )

        restored_termux = restarted.get_memory(
            "regression-termux"
        )

        restored_quantum = restarted.get_memory(
            "regression-quantum"
        )

        restored_conflict = restarted.get_memory(
            "regression-python-conflict"
        )

        check(
            restored_python is not None,
            "primary memory survives restart",
        )

        check(
            restored_termux is not None,
            "second memory survives restart",
        )

        check(
            restored_quantum is not None,
            "third memory survives restart",
        )

        check(
            restored_conflict is not None,
            "conflicting memory survives restart",
        )

        check(
            restored_python.content
            == "SAHIBEX uses Python for its core implementation.",
            "primary memory content survives restart",
        )

        restored_verification = (
            restarted.get_memory_verification(
                "regression-python"
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

        check(
            restored_verification["evidence_id"]
            == "regression-verification-source",
            "verification evidence survives restart",
        )

        check(
            restored_conflict.content
            == "SAHIBEX uses Java for its core implementation.",
            "conflict content survives restart",
        )

        restarted.close()

    print(
        "SAHIBEX 6I-12 FULL MEMORY INTELLIGENCE REGRESSION TEST: PASS"
    )


if __name__ == "__main__":
    main()
