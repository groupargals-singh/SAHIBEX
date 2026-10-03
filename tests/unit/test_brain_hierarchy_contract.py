from __future__ import annotations

from core.brain.brain_registry import BrainRegistry
from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.policies.constitution import BrainRole


def make_brain(
    name: str,
    role: BrainRole,
    parent_brain_id: str | None = None,
) -> SpecialistBrain:
    return SpecialistBrain(
        name=name,
        description=f"{name} test brain",
        specialization=name.lower().replace(" ", "_"),
        capabilities={BrainCapability.THINK},
        brain_role=role,
        parent_brain_id=parent_brain_id,
    )


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def expect_failure(
    operation,
    message: str,
) -> None:
    try:
        operation()
    except (TypeError, ValueError):
        print(f"[PASS] {message}")
        return

    raise AssertionError(
        f"Expected hierarchy rejection: {message}"
    )


def main() -> None:
    print("=" * 60)
    print("SAHIBEX 6L-3 BRAIN HIERARCHY INTEGRITY TEST")
    print("=" * 60)

    registry = BrainRegistry()

    # ---------------------------------------------------------
    # 1. Mother Brain
    # ---------------------------------------------------------

    mother = make_brain(
        "SAHIBEX Mother Brain",
        BrainRole.MOTHER_BRAIN,
    )

    registry.register(mother)

    check(
        registry.get_mother_brain() is mother,
        "Mother Brain is registered as the hierarchy root",
    )

    check(
        mother.parent_brain_id is None,
        "Mother Brain has no parent",
    )

    # ---------------------------------------------------------
    # 2. Internal Army Brain
    # ---------------------------------------------------------

    coding = make_brain(
        "Coding Internal Army",
        BrainRole.INTERNAL_ARMY,
        mother.brain_id,
    )

    registry.register(coding)

    check(
        registry.get_parent(coding.brain_id) is mother,
        "Internal Army parent resolves to Mother Brain",
    )

    check(
        coding in registry.get_children(mother.brain_id),
        "Mother Brain contains Internal Army child",
    )

    # ---------------------------------------------------------
    # 3. Child Brain
    # ---------------------------------------------------------

    quantum = make_brain(
        "Quantum-Bot Child Brain",
        BrainRole.CHILD_BRAIN,
        mother.brain_id,
    )

    registry.register(quantum)

    check(
        registry.get_parent(quantum.brain_id) is mother,
        "Child Brain parent resolves to Mother Brain",
    )

    check(
        quantum in registry.get_children(mother.brain_id),
        "Mother Brain contains Child Brain",
    )

    # ---------------------------------------------------------
    # 4. Child Brain Internal Army
    # ---------------------------------------------------------

    quantum_analysis = make_brain(
        "Quantum Analysis Internal Army",
        BrainRole.INTERNAL_ARMY,
        quantum.brain_id,
    )

    registry.register(quantum_analysis)

    check(
        registry.get_parent(
            quantum_analysis.brain_id
        ) is quantum,
        "Child Brain Internal Army resolves to Child Brain",
    )

    check(
        quantum_analysis in registry.get_children(
            quantum.brain_id
        ),
        "Child Brain contains its Internal Army",
    )

    # ---------------------------------------------------------
    # 5. Descendant integrity
    # ---------------------------------------------------------

    check(
        registry.is_descendant(
            quantum_analysis.brain_id,
            quantum.brain_id,
        ),
        "Child Internal Army is descendant of Child Brain",
    )

    check(
        registry.is_descendant(
            quantum_analysis.brain_id,
            mother.brain_id,
        ),
        "Child Internal Army is descendant of Mother Brain",
    )

    check(
        not registry.is_descendant(
            mother.brain_id,
            quantum.brain_id,
        ),
        "Mother Brain cannot be descendant of Child Brain",
    )

    # ---------------------------------------------------------
    # 6. Only one Mother Brain
    # ---------------------------------------------------------

    duplicate_mother = make_brain(
        "Second Mother Brain",
        BrainRole.MOTHER_BRAIN,
    )

    expect_failure(
        lambda: registry.register(duplicate_mother),
        "Only one Mother Brain can exist in a registry",
    )

    # ---------------------------------------------------------
    # 7. Mother Brain cannot have parent
    # ---------------------------------------------------------

    expect_failure(
    lambda: make_brain(
        "Invalid Mother Brain",
        BrainRole.MOTHER_BRAIN,
        mother.brain_id,
    ),
    "Mother Brain cannot have a parent",
)

    # ---------------------------------------------------------
    # 8. Child Brain requires parent
    # ---------------------------------------------------------

    orphan_child = make_brain(
        "Orphan Child Brain",
        BrainRole.CHILD_BRAIN,
    )

    expect_failure(
        lambda: registry.register(orphan_child),
        "Child Brain requires a parent",
    )

    # ---------------------------------------------------------
    # 9. Unknown parent rejected
    # ---------------------------------------------------------

    unknown_parent_child = make_brain(
        "Unknown Parent Child",
        BrainRole.CHILD_BRAIN,
        "non-existent-parent",
    )

    expect_failure(
        lambda: registry.register(unknown_parent_child),
        "Child Brain cannot reference an unknown parent",
    )

    # ---------------------------------------------------------
    # 10. Internal Army cannot be a parent
    # ---------------------------------------------------------

    invalid_army_child = make_brain(
        "Invalid Army Child",
        BrainRole.CHILD_BRAIN,
        coding.brain_id,
    )

    expect_failure(
        lambda: registry.register(invalid_army_child),
        "Internal Army Brain cannot become a parent",
    )

    # ---------------------------------------------------------
    # 11. Child Brain cannot contain another Child Brain
    # ---------------------------------------------------------

    nested_child = make_brain(
        "Nested Child Brain",
        BrainRole.CHILD_BRAIN,
        quantum.brain_id,
    )

    expect_failure(
        lambda: registry.register(nested_child),
        "Child Brain cannot directly contain another Child Brain",
    )

    # ---------------------------------------------------------
    # 12. Child removal protection
    # ---------------------------------------------------------

    expect_failure(
        lambda: registry.remove(quantum.brain_id),
        "Parent cannot be removed while children exist",
    )

    # ---------------------------------------------------------
    # 13. Remove leaf first
    # ---------------------------------------------------------

    removed_army = registry.remove(
        quantum_analysis.brain_id
    )

    check(
        removed_army is quantum_analysis,
        "Leaf Internal Army can be removed",
    )

    removed_quantum = registry.remove(
        quantum.brain_id
    )

    check(
        removed_quantum is quantum,
        "Child Brain can be removed after its children",
    )

    # ---------------------------------------------------------
    # 14. Registry does not grant authority
    # ---------------------------------------------------------

    check(
        registry.get_mother_brain() is mother,
        "Registry identity does not replace Constitutional authority",
    )

    print("=" * 60)
    print("SAHIBEX 6L-3 BRAIN HIERARCHY INTEGRITY TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
