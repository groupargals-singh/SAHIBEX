from __future__ import annotations

from core.brain.specialist_brain import (
    BrainCapability,
    BrainStatus,
    SpecialistBrain,
)
from core.brain.brain_registry import BrainRegistry


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # ---------------------------------------------------------
    # 6L-2 Brain Identity & Role Registry Contract
    # ---------------------------------------------------------

    registry = BrainRegistry()

    # 1. Registry must start empty.
    check(
        registry.count() == 0,
        "New registry must start empty.",
    )

    # 2. Create specialist brains.
    research_brain = SpecialistBrain(
        name="Research Specialist",
        description="Handles research-oriented tasks.",
        specialization="research",
        capabilities={
            BrainCapability.RESEARCH,
            BrainCapability.ANALYZE,
        },
    )

    coding_brain = SpecialistBrain(
        name="Coding Specialist",
        description="Handles coding-oriented tasks.",
        specialization="coding",
        capabilities={
            BrainCapability.CODE,
            BrainCapability.CREATE,
        },
    )

    # 3. Register brain.
    registered = registry.register(research_brain)

    check(
        registered is research_brain,
        "register() must return the registered brain.",
    )

    check(
        registry.count() == 1,
        "Registry count must increase after registration.",
    )

    # 4. Retrieve by brain ID.
    retrieved = registry.get(research_brain.brain_id)

    check(
        retrieved is research_brain,
        "get() must return the registered brain.",
    )

    # 5. Register second brain.
    registry.register(coding_brain)

    check(
        registry.count() == 2,
        "Registry must contain both registered brains.",
    )

    # 6. List all brains.
    brains = registry.list_all()

    check(
        len(brains) == 2,
        "list_all() must return all registered brains.",
    )

    check(
        research_brain in brains,
        "Research brain must be present in registry.",
    )

    check(
        coding_brain in brains,
        "Coding brain must be present in registry.",
    )

    # 7. Lookup by specialization.
    research_results = registry.find_by_specialization(
        "research"
    )

    check(
        len(research_results) == 1,
        "Research specialization lookup must return one brain.",
    )

    check(
        research_results[0] is research_brain,
        "Research lookup returned the wrong brain.",
    )

    # 8. Lookup must not invent missing brains.
    missing = registry.get("does-not-exist")

    check(
        missing is None,
        "Unknown brain ID must return None.",
    )

    # 9. Duplicate identity must be rejected.
    duplicate = SpecialistBrain(
        name="Duplicate Identity",
        description="Duplicate test brain.",
        specialization="research",
        capabilities={
            BrainCapability.RESEARCH,
        },
        brain_id=research_brain.brain_id,
    )

    duplicate_rejected = False

    try:
        registry.register(duplicate)
    except ValueError:
        duplicate_rejected = True

    check(
        duplicate_rejected,
        "Duplicate brain_id must be rejected.",
    )

    # 10. Remove brain.
    removed = registry.remove(coding_brain.brain_id)

    check(
        removed is coding_brain,
        "remove() must return the removed brain.",
    )

    check(
        registry.count() == 1,
        "Registry count must decrease after removal.",
    )

    check(
        registry.get(coding_brain.brain_id) is None,
        "Removed brain must no longer be retrievable.",
    )

    # 11. Invalid registration must be rejected.
    invalid_rejected = False

    try:
        registry.register("not-a-brain")
    except TypeError:
        invalid_rejected = True

    check(
        invalid_rejected,
        "Registry must reject non-SpecialistBrain objects.",
    )

    print(
        "SAHIBEX 6L-2 BRAIN REGISTRY CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
