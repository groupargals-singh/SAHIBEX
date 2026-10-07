from core.brain.child_self_improvement_compatibility import (
    ChildSelfImprovementCompatibilityChecker,
    CompatibilityRequest,
    CompatibilityStatus,
    DependencyRequirement,
    DependencyType,
)


def test_compatible_upgrade():
    checker = ChildSelfImprovementCompatibilityChecker()

    result = checker.check(
        CompatibilityRequest(
            request_id="1",
            child_brain_id="child-001",
            target="reasoning",
            current_version="1.0",
            proposed_version="1.1",
            dependencies=(
                DependencyRequirement(
                    name="reasoning-core",
                    dependency_type=DependencyType.REQUIRED,
                    available=True,
                    compatible=True,
                ),
            ),
        )
    )

    assert result.status == CompatibilityStatus.COMPATIBLE
    assert result.requires_mother is True
    assert result.requires_human is False


def test_missing_required_dependency():
    checker = ChildSelfImprovementCompatibilityChecker()

    result = checker.check(
        CompatibilityRequest(
            request_id="2",
            child_brain_id="child-001",
            target="reasoning",
            current_version="1.0",
            proposed_version="1.1",
            dependencies=(
                DependencyRequirement(
                    name="missing-core",
                    dependency_type=DependencyType.REQUIRED,
                    available=False,
                    compatible=True,
                ),
            ),
        )
    )

    assert result.status == CompatibilityStatus.INCOMPATIBLE
    assert "missing-core" in result.failed_dependencies


def test_incompatible_required_dependency():
    checker = ChildSelfImprovementCompatibilityChecker()

    result = checker.check(
        CompatibilityRequest(
            request_id="3",
            child_brain_id="child-001",
            target="learning",
            current_version="1.0",
            proposed_version="1.1",
            dependencies=(
                DependencyRequirement(
                    name="learning-core",
                    dependency_type=DependencyType.REQUIRED,
                    available=True,
                    compatible=False,
                ),
            ),
        )
    )

    assert result.status == CompatibilityStatus.INCOMPATIBLE
    assert "learning-core" in result.conflicts


def test_conflicting_dependency():
    checker = ChildSelfImprovementCompatibilityChecker()

    result = checker.check(
        CompatibilityRequest(
            request_id="4",
            child_brain_id="child-001",
            target="code",
            current_version="1.0",
            proposed_version="1.1",
            dependencies=(
                DependencyRequirement(
                    name="legacy-module",
                    dependency_type=DependencyType.CONFLICT,
                    available=True,
                    compatible=True,
                ),
            ),
        )
    )

    assert result.status == CompatibilityStatus.INCOMPATIBLE
    assert "legacy-module" in result.conflicts
    assert result.requires_human is True


def test_security_change_requires_human():
    checker = ChildSelfImprovementCompatibilityChecker()

    result = checker.check(
        CompatibilityRequest(
            request_id="5",
            child_brain_id="child-001",
            target="security",
            current_version="1.0",
            proposed_version="1.1",
            affects_security=True,
        )
    )

    assert result.status == CompatibilityStatus.COMPATIBLE
    assert result.requires_mother is True
    assert result.requires_human is True


def test_verification_change_requires_human():
    checker = ChildSelfImprovementCompatibilityChecker()

    result = checker.check(
        CompatibilityRequest(
            request_id="6",
            child_brain_id="child-001",
            target="verification",
            current_version="1.0",
            proposed_version="1.1",
            affects_verification=True,
        )
    )

    assert result.status == CompatibilityStatus.COMPATIBLE
    assert result.requires_human is True


def test_army_change_requires_mother():
    checker = ChildSelfImprovementCompatibilityChecker()

    result = checker.check(
        CompatibilityRequest(
            request_id="7",
            child_brain_id="child-001",
            target="internal_army",
            current_version="1.0",
            proposed_version="1.1",
            affects_army=True,
        )
    )

    assert result.status == CompatibilityStatus.COMPATIBLE
    assert result.requires_mother is True


def test_labor_change_requires_mother():
    checker = ChildSelfImprovementCompatibilityChecker()

    result = checker.check(
        CompatibilityRequest(
            request_id="8",
            child_brain_id="child-001",
            target="internal_labor",
            current_version="1.0",
            proposed_version="1.1",
            affects_labor=True,
        )
    )

    assert result.status == CompatibilityStatus.COMPATIBLE
    assert result.requires_mother is True


def test_memory_change_requires_mother():
    checker = ChildSelfImprovementCompatibilityChecker()

    result = checker.check(
        CompatibilityRequest(
            request_id="9",
            child_brain_id="child-001",
            target="memory",
            current_version="1.0",
            proposed_version="1.1",
            affects_memory=True,
        )
    )

    assert result.status == CompatibilityStatus.COMPATIBLE
    assert result.requires_mother is True


def test_missing_identity_fails_closed():
    checker = ChildSelfImprovementCompatibilityChecker()

    result = checker.check(
        CompatibilityRequest(
            request_id="10",
            child_brain_id="",
            target="reasoning",
            current_version="1.0",
            proposed_version="1.1",
        )
    )

    assert result.status == CompatibilityStatus.BLOCKED
    assert result.requires_human is True


def test_compatibility_checker_never_executes():
    checker = ChildSelfImprovementCompatibilityChecker()

    assert checker.execution_allowed() is False
    assert checker.upgrade_execution_allowed() is False
    assert checker.grants_authority() is False
    assert checker.can_override_conflict() is False
    assert checker.can_bypass_dependency() is False
    assert checker.creates_real_child() is False
    assert checker.activates_real_child() is False


if __name__ == "__main__":
    test_compatible_upgrade()
    test_missing_required_dependency()
    test_incompatible_required_dependency()
    test_conflicting_dependency()
    test_security_change_requires_human()
    test_verification_change_requires_human()
    test_army_change_requires_mother()
    test_labor_change_requires_mother()
    test_memory_change_requires_mother()
    test_missing_identity_fails_closed()
    test_compatibility_checker_never_executes()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT COMPATIBILITY TEST: PASS"
    )
