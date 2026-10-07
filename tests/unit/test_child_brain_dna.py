from core.policies.constitution import SahibexConstitution


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    constitution = SahibexConstitution()

    print("=" * 60)
    print("SAHIBEX CHILD BRAIN CREATION DNA TEST")
    print("=" * 60)

    # ------------------------------------------------------------
    # DNA existence and identity
    # ------------------------------------------------------------

    check(
        constitution.child_brain_dna_version() == "1.0",
        "child brain DNA version exists",
    )

    dna = constitution.child_brain_dna()

    check(
        isinstance(dna, tuple),
        "child brain DNA is immutable tuple",
    )

    check(
        constitution.child_brain_has_independent_soul(),
        "child brain has independent soul",
    )

    check(
        constitution.child_brain_is_separate_entity(),
        "child brain is a separate brain entity",
    )

    check(
        not constitution.child_brain_is_sahibex(),
        "child brain is not SAHIBEX Mother Brain",
    )

    check(
        constitution.child_brain_creation_requires_new_identity(),
        "child receives a new independent identity",
    )

    # ------------------------------------------------------------
    # Child internal architecture
    # ------------------------------------------------------------

    check(
        constitution.child_brain_has_internal_army(),
        "child brain has internal Army Brain architecture",
    )

    check(
        constitution.child_brain_has_internal_labor(),
        "child brain has internal Labor Brain architecture",
    )

    check(
        constitution.child_brain_specialist_work_is_internal(),
        "specialist work remains inside child architecture",
    )

    check(
        constitution.child_brain_has_independent_memory(),
        "child brain has independent memory architecture",
    )

    check(
        constitution.child_brain_has_independent_thought(),
        "child brain has independent thought",
    )

    # ------------------------------------------------------------
    # Authority hierarchy
    # ------------------------------------------------------------

    check(
        constitution.child_brain_remains_under_mother_authority(),
        "child remains under Mother Brain authority",
    )

    check(
        constitution.child_brain_cannot_override_mother(),
        "child cannot override Mother Brain",
    )

    check(
        constitution.child_brain_cannot_override_human(),
        "child cannot override Human authority",
    )

    # ------------------------------------------------------------
    # Soul / Constitution protection
    # ------------------------------------------------------------

    check(
        constitution.child_brain_cannot_modify_own_soul(),
        "child cannot modify its own soul",
    )

    check(
        constitution.sahibex_cannot_directly_rewrite_child_soul(),
        "SAHIBEX cannot directly rewrite child soul",
    )

    check(
        constitution.child_brain_requires_constitutional_boundary(),
        "child requires its own constitutional boundary",
    )

    # ------------------------------------------------------------
    # Multiple Child Brain architecture
    # ------------------------------------------------------------

    check(
        constitution.child_brain_creation_supports_multiple_children(),
        "multiple independent child brains are supported",
    )

    # ------------------------------------------------------------
    # Important architectural distinction
    # ------------------------------------------------------------

    check(
        constitution.child_brain_creation_is_not_specialist_creation(),
        "child creation is different from specialist brain creation",
    )

    # ------------------------------------------------------------
    # Required DNA markers
    # ------------------------------------------------------------

    required_dna = {
        "independent_brain_identity",
        "independent_constitutional_soul",
        "independent_constitution",
        "independent_memory",
        "independent_reasoning",
        "independent_learning",
        "independent_planning",
        "internal_army_brains",
        "internal_labor_brains",
        "verification",
        "security",
        "audit_and_provenance",
        "mother_authority_boundary",
        "human_authority_boundary",
        "capability_is_not_authority",
        "no_authority_escalation",
        "no_constitution_override",
        "no_self_soul_modification",
        "separate_brain_identity",
        "multiple_child_creation",
    }

    for marker in sorted(required_dna):
        check(
            marker in dna,
            f"child DNA contains: {marker}",
        )

    print("=" * 60)
    print("SAHIBEX CHILD BRAIN CREATION DNA TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
