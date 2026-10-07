from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.memory_association import (
    MemoryAssociation,
)
from core.research.memory_association_storage import (
    MemoryAssociationStorage,
)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print(
        "SAHIBEX PHASE 2 PERSISTENT MEMORY ASSOCIATION TEST"
    )

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "memory_graph.db"

        storage = MemoryAssociationStorage(db_path)

        association = MemoryAssociation(
            association_id="assoc-001",
            source_memory_id="memory-001",
            target_id="concept-python",
            target_type="concept",
            association_type="memory_to_concept",
            strength=0.9,
            confidence=0.95,
            metadata={"shared": True},
        )

        saved = storage.save_association(association)

        check(
            saved.association_id == "assoc-001",
            "association persisted",
        )

        loaded = storage.get_by_id("assoc-001")

        check(
            loaded is not None,
            "association retrieved",
        )

        check(
            loaded.target_id == "concept-python",
            "target identity persisted",
        )

        check(
            loaded.metadata["shared"] is True,
            "metadata persisted",
        )

        storage.save_association(
            MemoryAssociation(
                association_id="assoc-002",
                source_memory_id="memory-002",
                target_id="concept-python",
                target_type="concept",
                association_type="memory_to_concept",
                strength=0.8,
                confidence=0.9,
            )
        )

        check(
            storage.association_count() == 2,
            "multiple memories share one concept",
        )

        linked = storage.memories_for_target(
            "concept-python",
            "concept",
        )

        check(
            linked == (
                "memory-001",
                "memory-002",
            ),
            "shared concept reverse lookup works",
        )

        storage.close()

        restarted = MemoryAssociationStorage(db_path)

        restored = restarted.get_by_id("assoc-001")

        check(
            restored is not None,
            "association survives restart",
        )

        check(
            restored.source_memory_id == "memory-001",
            "source memory survives restart",
        )

        check(
            restarted.association_count() == 2,
            "association graph survives restart",
        )

        summary = restarted.summary()

        check(
            summary[
                "stores_links_not_duplicate_memory_content"
            ] is True,
            "storage uses link-based architecture",
        )

        check(
            summary["grants_permission"] is False,
            "storage grants no permission",
        )

        check(
            summary["executes_actions"] is False,
            "storage executes no actions",
        )

        restarted.close()

    print(
        "SAHIBEX PHASE 2 PERSISTENT MEMORY ASSOCIATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
