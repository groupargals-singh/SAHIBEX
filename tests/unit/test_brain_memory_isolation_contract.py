from __future__ import annotations

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # ---------------------------------------------------------
    # 6L-6 Brain Memory Isolation Contract
    # ---------------------------------------------------------

    research_brain = SpecialistBrain(
        name="Research Specialist",
        description="Research specialist brain.",
        specialization="research",
        capabilities={
            BrainCapability.RESEARCH,
        },
    )

    coding_brain = SpecialistBrain(
        name="Coding Specialist",
        description="Coding specialist brain.",
        specialization="code",
        capabilities={
            BrainCapability.CODE,
        },
    )

    # 1. Every brain must have a unique identity.
    check(
        research_brain.brain_id != coding_brain.brain_id,
        "Specialist brains must have unique identities.",
    )

    # 2. A brain must expose an isolated memory namespace.
    check(
        hasattr(research_brain, "memory_namespace"),
        "Brain must expose a memory_namespace.",
    )

    check(
        hasattr(coding_brain, "memory_namespace"),
        "Brain must expose a memory_namespace.",
    )

    # 3. Memory namespaces must be unique per brain.
    check(
        research_brain.memory_namespace
        != coding_brain.memory_namespace,
        "Each brain must have a unique memory namespace.",
    )

    # 4. Memory namespace must be derived from brain identity.
    check(
        research_brain.brain_id in research_brain.memory_namespace,
        "Memory namespace must be bound to brain identity.",
    )

    check(
        coding_brain.brain_id in coding_brain.memory_namespace,
        "Memory namespace must be bound to brain identity.",
    )

    # 5. Memory namespaces must be stable.
    research_namespace = research_brain.memory_namespace
    coding_namespace = coding_brain.memory_namespace

    check(
        research_brain.memory_namespace == research_namespace,
        "Research brain memory namespace must remain stable.",
    )

    check(
        coding_brain.memory_namespace == coding_namespace,
        "Coding brain memory namespace must remain stable.",
    )

    # 6. Memory isolation must not change brain identity.
    research_id = research_brain.brain_id
    coding_id = coding_brain.brain_id

    check(
        research_brain.brain_id == research_id,
        "Memory isolation must preserve research brain identity.",
    )

    check(
        coding_brain.brain_id == coding_id,
        "Memory isolation must preserve coding brain identity.",
    )

    # 7. Memory namespace must not grant permissions.
    brain_fields = set(research_brain.__dataclass_fields__)

    check(
        "permission" not in brain_fields,
        "Memory isolation must not add permission fields.",
    )

    check(
        "authorization" not in brain_fields,
        "Memory isolation must not add authorization fields.",
    )

    # 8. Memory namespace must not contain shared/global identity.
    check(
        research_brain.memory_namespace
        != "global",
        "Specialist memory must not use a global namespace.",
    )

    check(
        coding_brain.memory_namespace
        != "global",
        "Specialist memory must not use a global namespace.",
    )

    print(
        "SAHIBEX 6L-6 BRAIN MEMORY ISOLATION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
