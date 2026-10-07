from datetime import datetime, timedelta, timezone

from core.research.procedural_memory import (
    PROCEDURAL_MEMORY_VERSION,
    ProceduralMemory,
    ProceduralMemoryStore,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    procedure_1 = ProceduralMemory(
        procedure_id="procedure-001",
        name="Python project setup",
        purpose="Prepare a Python development project.",
        steps=(
            "Create project directory",
            "Create virtual environment",
            "Install required dependencies",
            "Run validation tests",
        ),
        source="experience-1",
        confidence=0.95,
        importance=0.90,
        success_count=9,
        failure_count=1,
        provenance={"experience_id": "experience-1"},
        tags=["python", "development", "setup"],
        created_at=base_time,
        updated_at=base_time,
    )

    procedure_2 = ProceduralMemory(
        procedure_id="procedure-002",
        name="Python project setup",
        purpose="Set up a Python project for testing.",
        steps=(
            "Create project directory",
            "Create virtual environment",
            "Run tests",
        ),
        source="experience-2",
        confidence=0.80,
        importance=0.70,
        success_count=4,
        failure_count=1,
        provenance={"experience_id": "experience-2"},
        tags=["python", "testing"],
        created_at=base_time + timedelta(seconds=1),
        updated_at=base_time + timedelta(seconds=1),
    )

    procedure_3 = ProceduralMemory(
        procedure_id="procedure-003",
        name="Termux environment setup",
        purpose="Prepare a Termux development environment.",
        steps=(
            "Open Termux",
            "Update packages",
            "Create project environment",
        ),
        source="experience-3",
        confidence=0.85,
        importance=0.75,
        success_count=6,
        failure_count=2,
        provenance={"experience_id": "experience-3"},
        tags=["termux", "android"],
        created_at=base_time + timedelta(seconds=2),
        updated_at=base_time + timedelta(seconds=2),
    )

    check(
        procedure_1.procedure_id == "procedure-001",
        "procedural memory identity preserved",
    )

    check(
        procedure_1.name == "Python project setup",
        "procedure name preserved",
    )

    check(
        len(procedure_1.steps) == 4,
        "procedure steps preserved",
    )

    check(
        procedure_1.purpose.startswith("Prepare"),
        "procedure purpose preserved",
    )

    check(
        procedure_1.provenance["experience_id"] == "experience-1",
        "procedural provenance preserved",
    )

    store = ProceduralMemoryStore(capacity=3)

    store.store(procedure_1)
    store.store(procedure_2)
    store.store(procedure_3)

    check(
        store.count() == 3,
        "procedural memory storage works",
    )

    check(
        store.get("procedure-001") == procedure_1,
        "procedural memory retrieval works",
    )

    check(
        store.contains("procedure-002"),
        "procedural memory identity lookup works",
    )

    named = store.by_name("python project setup")

    check(
        len(named) == 2,
        "procedure name retrieval returns matching procedures",
    )

    check(
        named[0].procedure_id == "procedure-001",
        "procedure retrieval ranks successful procedure first",
    )

    tagged = store.by_tag("python")

    check(
        len(tagged) == 2,
        "procedural tag retrieval works",
    )

    searched = store.search("virtual environment")

    check(
        len(searched) == 2,
        "procedural step search works",
    )

    successful = store.successful()

    check(
        len(successful) == 3,
        "successful procedure retrieval works",
    )

    check(
        successful[0].procedure_id == "procedure-001",
        "successful procedure ranking works",
    )

    all_procedures = store.all()

    check(
        len(all_procedures) == 3,
        "procedural memory listing works",
    )

    old_procedure = ProceduralMemory(
        procedure_id="procedure-004",
        name="Old procedure",
        purpose="Old procedural information.",
        steps=("Old step",),
        source="experience-4",
        confidence=0.40,
        importance=0.20,
        success_count=0,
        failure_count=1,
        provenance={"experience_id": "experience-4"},
        tags=["old"],
        created_at=base_time - timedelta(days=1),
        updated_at=base_time - timedelta(days=1),
    )

    store.store(old_procedure)

    check(
        not store.contains("procedure-004"),
        "oldest procedural memory is evicted when capacity is exceeded",
    )

    check(
        store.contains("procedure-001"),
        "newer procedural memory is retained",
    )

    try:
        procedure_1.name = "changed"
        immutable_blocked = False
    except (AttributeError, TypeError):
        immutable_blocked = True

    check(
        immutable_blocked,
        "procedural memory objects are immutable",
    )

    check(
        PROCEDURAL_MEMORY_VERSION == "P2-PM-1",
        "procedural memory version is correct",
    )

    summary = store.summary()

    check(
        summary["preserves_steps"] is True,
        "procedure step preservation enabled",
    )

    check(
        summary["preserves_provenance"] is True,
        "procedural provenance preservation enabled",
    )

    check(
        summary["tracks_success_failure"] is True,
        "success and failure tracking enabled",
    )

    check(
        summary["supports_procedure_retrieval"] is True,
        "procedure retrieval capability enabled",
    )

    check(
        summary["supports_procedure_search"] is True,
        "procedure search capability enabled",
    )

    check(
        summary["execution_authority"] is False,
        "procedural memory has no execution authority",
    )

    check(
        summary["grants_permission"] is False,
        "procedural memory grants no permission",
    )

    check(
        summary["executes_actions"] is False,
        "procedural memory executes no actions",
    )

    check(
        summary["modifies_constitution"] is False,
        "procedural memory cannot modify constitution",
    )

    removed = store.remove("procedure-002")

    check(
        removed is not None and not store.contains("procedure-002"),
        "procedural memory removal works",
    )

    store.clear()

    check(
        store.count() == 0,
        "procedural memory cleanup works",
    )

    print("SAHIBEX PHASE 2 #46 PROCEDURAL MEMORY TEST: PASS")


if __name__ == "__main__":
    main()
