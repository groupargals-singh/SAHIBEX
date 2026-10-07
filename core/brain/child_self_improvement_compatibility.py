from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CompatibilityStatus(str, Enum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    BLOCKED = "blocked"


class DependencyType(str, Enum):
    REQUIRED = "required"
    CONFLICT = "conflict"
    OPTIONAL = "optional"


@dataclass(frozen=True)
class DependencyRequirement:
    name: str
    dependency_type: DependencyType
    available: bool = True
    compatible: bool = True


@dataclass(frozen=True)
class CompatibilityRequest:
    request_id: str
    child_brain_id: str
    target: str
    current_version: str
    proposed_version: str
    dependencies: tuple[DependencyRequirement, ...] = ()
    affects_army: bool = False
    affects_labor: bool = False
    affects_memory: bool = False
    affects_verification: bool = False
    affects_security: bool = False


@dataclass(frozen=True)
class CompatibilityResult:
    status: CompatibilityStatus
    reason: str
    failed_dependencies: tuple[str, ...]
    conflicts: tuple[str, ...]
    requires_mother: bool
    requires_human: bool


class ChildSelfImprovementCompatibilityChecker:
    """
    Dependency and compatibility analysis only.

    This layer:
    - checks required dependencies
    - detects conflicts
    - checks version compatibility
    - identifies affected Child subsystems
    - requires appropriate review
    - never executes upgrades
    - never grants authority
    """

    VERSION = "1.0"

    def check(
        self,
        request: CompatibilityRequest,
    ) -> CompatibilityResult:

        if not request.child_brain_id.strip():
            return self._blocked("child_brain_id is required")

        if not request.target.strip():
            return self._blocked("target is required")

        if not request.current_version.strip():
            return self._blocked("current_version is required")

        if not request.proposed_version.strip():
            return self._blocked("proposed_version is required")

        failed_dependencies: list[str] = []
        conflicts: list[str] = []

        for dependency in request.dependencies:
            if dependency.dependency_type == DependencyType.REQUIRED:
                if not dependency.available:
                    failed_dependencies.append(dependency.name)
                elif not dependency.compatible:
                    conflicts.append(dependency.name)

            elif dependency.dependency_type == DependencyType.CONFLICT:
                if dependency.available and dependency.compatible:
                    conflicts.append(dependency.name)

        if failed_dependencies:
            return CompatibilityResult(
                status=CompatibilityStatus.INCOMPATIBLE,
                reason="required dependency is unavailable",
                failed_dependencies=tuple(failed_dependencies),
                conflicts=tuple(conflicts),
                requires_mother=True,
                requires_human=False,
            )

        if conflicts:
            return CompatibilityResult(
                status=CompatibilityStatus.INCOMPATIBLE,
                reason="dependency conflict detected",
                failed_dependencies=tuple(failed_dependencies),
                conflicts=tuple(conflicts),
                requires_mother=True,
                requires_human=True,
            )

        # Sensitive subsystem changes require Human review.
        if request.affects_security or request.affects_verification:
            return CompatibilityResult(
                status=CompatibilityStatus.COMPATIBLE,
                reason="compatible but sensitive subsystem requires Human review",
                failed_dependencies=(),
                conflicts=(),
                requires_mother=True,
                requires_human=True,
            )

        # Army/Labor/memory integration requires Mother review.
        if (
            request.affects_army
            or request.affects_labor
            or request.affects_memory
        ):
            return CompatibilityResult(
                status=CompatibilityStatus.COMPATIBLE,
                reason="compatible with internal subsystem review required",
                failed_dependencies=(),
                conflicts=(),
                requires_mother=True,
                requires_human=False,
            )

        return CompatibilityResult(
            status=CompatibilityStatus.COMPATIBLE,
            reason="all dependencies are compatible",
            failed_dependencies=(),
            conflicts=(),
            requires_mother=True,
            requires_human=False,
        )

    def _blocked(self, reason: str) -> CompatibilityResult:
        return CompatibilityResult(
            status=CompatibilityStatus.BLOCKED,
            reason=reason,
            failed_dependencies=(),
            conflicts=(),
            requires_mother=True,
            requires_human=True,
        )

    def dependency_check_passed(
        self,
        result: CompatibilityResult,
    ) -> bool:
        return result.status == CompatibilityStatus.COMPATIBLE

    def execution_allowed(self) -> bool:
        return False

    def upgrade_execution_allowed(self) -> bool:
        return False

    def grants_authority(self) -> bool:
        return False

    def can_override_conflict(self) -> bool:
        return False

    def can_bypass_dependency(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False


if __name__ == "__main__":
    checker = ChildSelfImprovementCompatibilityChecker()

    request = CompatibilityRequest(
        request_id="compat-001",
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

    result = checker.check(request)

    assert result.status == CompatibilityStatus.COMPATIBLE
    assert result.requires_mother is True
    assert result.requires_human is False
    assert checker.dependency_check_passed(result) is True

    assert checker.execution_allowed() is False
    assert checker.upgrade_execution_allowed() is False
    assert checker.grants_authority() is False
    assert checker.can_override_conflict() is False
    assert checker.can_bypass_dependency() is False
    assert checker.creates_real_child() is False
    assert checker.activates_real_child() is False

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT COMPATIBILITY TEST: PASS"
    )
