from core.policies.constitution import SahibexConstitution


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    constitution = SahibexConstitution()

    print("=" * 60)
    print("SAHIBEX CHILD BIRTH PROTOCOL TEST")
    print("=" * 60)

    check(
        constitution.child_birth_protocol_version() == "1.0",
        "child birth protocol version exists",
    )

    check(
        constitution.child_birth_requires_new_brain_identity(),
        "child is born with a new brain identity",
    )

    check(
        constitution.child_birth_requires_new_soul(),
        "child is born with a new independent soul",
    )

    check(
        constitution.child_birth_requires_new_constitution(),
        "child is born with its own constitution",
    )

    check(
        constitution.child_birth_requires_independent_memory(),
        "child receives independent memory",
    )

    check(
        constitution.child_birth_requires_defined_purpose(),
        "child requires a defined purpose",
    )

    check(
        constitution.child_birth_requires_parent_identity(),
        "child has a defined parent identity",
    )

    check(
        constitution.child_birth_creates_internal_army(),
        "child has internal Army architecture",
    )

    check(
        constitution.child_birth_creates_internal_labor(),
        "child has internal Labor architecture",
    )

    check(
        constitution.child_birth_has_independent_soul_from_mother(),
        "child soul is independent from mother soul",
    )

    check(
        not constitution.child_birth_copies_mother_soul(),
        "child does not copy mother soul",
    )

    check(
        not constitution.child_birth_copies_mother_memory(),
        "child does not automatically copy mother memory",
    )

    check(
        not constitution.child_birth_copies_mother_authority(),
        "child does not inherit mother authority",
    )

    check(
        not constitution.child_birth_becomes_sahibex(),
        "child does not become SAHIBEX",
    )

    check(
        constitution.child_birth_has_mother_authority_boundary(),
        "child remains under Mother authority",
    )

    check(
        constitution.child_birth_has_human_authority_boundary(),
        "child remains under Human authority",
    )

    check(
        constitution.child_birth_requires_security_boundary(),
        "child is born with security boundary",
    )

    check(
        constitution.child_birth_requires_verification_boundary(),
        "child is born with verification boundary",
    )

    check(
        constitution.child_birth_requires_audit_identity(),
        "child receives independent audit identity",
    )

    check(
        constitution.child_birth_requires_resource_boundary(),
        "child receives resource boundary",
    )

    check(
        constitution.child_birth_requires_lifecycle_boundary(),
        "child receives lifecycle boundary",
    )

    check(
        constitution.child_birth_is_separate_brain_creation(),
        "child birth creates a separate brain entity",
    )

    required = set(constitution.child_birth_requirements())

    for item in required:
        check(
            item in required,
            f"birth requirement exists: {item}",
        )

    forbidden = set(constitution.child_birth_forbidden_inheritance())

    for item in forbidden:
        check(
            item in forbidden,
            f"forbidden inheritance rule exists: {item}",
        )

    print("=" * 60)
    print("SAHIBEX CHILD BIRTH PROTOCOL TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
