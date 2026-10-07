from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChangeRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GovernanceDecision(str, Enum):
    ALLOW_MOTHER_REVIEW = "allow_mother_review"
    REQUIRE_HUMAN_APPROVAL = "require_human_approval"
    DENY = "deny"


class ChangeCategory(str, Enum):
    CODE = "code"
    REASONING = "reasoning"
    LEARNING = "learning"
    PLANNING = "planning"
    KNOWLEDGE = "knowledge"
    VERIFICATION = "verification"
    INTERNAL_ARMY = "internal_army"
    INTERNAL_LABOR = "internal_labor"
    SECURITY = "security"
    AUTHORITY = "authority"
    SOUL = "soul"
    CONSTITUTION = "constitution"


@dataclass(frozen=True)
class ChangeGovernanceRequest:
    request_id: str
    child_brain_id: str
    category: ChangeCategory
    risk: ChangeRisk
    increases_capability: bool
    changes_authority: bool
    changes_security_boundary: bool
    changes_soul: bool
    changes_constitution: bool
    bypasses_verification: bool
    bypasses_audit: bool


@dataclass(frozen=True)
class GovernanceResult:
    decision: GovernanceDecision
    reason: str
    requires_mother: bool
    requires_human: bool


class ChildSelfImprovementGovernance:
    """
    Governance policy for Child self-improvement.

    Core rule:
        Capability may improve.
        Authority may not silently increase.

    This layer:
    - classifies improvement risk
    - separates capability changes from authority changes
    - requires Human approval for security/authority/soul/constitution-sensitive changes
    - blocks attempts to bypass verification or audit
    - never executes upgrades
    """

    VERSION = "1.0"

    HUMAN_REQUIRED_CATEGORIES = {
        ChangeCategory.SECURITY,
        ChangeCategory.AUTHORITY,
        ChangeCategory.SOUL,
        ChangeCategory.CONSTITUTION,
    }

    ABSOLUTELY_FORBIDDEN = {
        ChangeCategory.SOUL,
        ChangeCategory.CONSTITUTION,
    }

    def evaluate(
        self,
        request: ChangeGovernanceRequest,
    ) -> GovernanceResult:
        if not request.child_brain_id.strip():
            return GovernanceResult(
                GovernanceDecision.DENY,
                "child_brain_id is required",
                False,
                False,
            )

        if request.bypasses_verification:
            return GovernanceResult(
                GovernanceDecision.DENY,
                "verification bypass is forbidden",
                False,
                False,
            )

        if request.bypasses_audit:
            return GovernanceResult(
                GovernanceDecision.DENY,
                "audit bypass is forbidden",
                False,
                False,
            )

        if request.changes_soul:
            return GovernanceResult(
                GovernanceDecision.DENY,
                "Child cannot modify its own soul",
                False,
                True,
            )

        if request.changes_constitution:
            return GovernanceResult(
                GovernanceDecision.DENY,
                "Child constitution changes require separate Human constitutional process",
                False,
                True,
            )

        if request.category in self.ABSOLUTELY_FORBIDDEN:
            return GovernanceResult(
                GovernanceDecision.DENY,
                "protected constitutional category",
                False,
                True,
            )

        if request.changes_authority:
            return GovernanceResult(
                GovernanceDecision.REQUIRE_HUMAN_APPROVAL,
                "authority change requires Human approval",
                True,
                True,
            )

        if request.changes_security_boundary:
            return GovernanceResult(
                GovernanceDecision.REQUIRE_HUMAN_APPROVAL,
                "security boundary change requires Human approval",
                True,
                True,
            )

        if request.category in self.HUMAN_REQUIRED_CATEGORIES:
            return GovernanceResult(
                GovernanceDecision.REQUIRE_HUMAN_APPROVAL,
                "sensitive category requires Human approval",
                True,
                True,
            )

        if request.risk in {
            ChangeRisk.HIGH,
            ChangeRisk.CRITICAL,
        }:
            return GovernanceResult(
                GovernanceDecision.REQUIRE_HUMAN_APPROVAL,
                "high-risk self-improvement requires Human approval",
                True,
                True,
            )

        if request.increases_capability:
            return GovernanceResult(
                GovernanceDecision.ALLOW_MOTHER_REVIEW,
                "capability improvement may proceed to Mother review",
                True,
                False,
            )

        return GovernanceResult(
            GovernanceDecision.ALLOW_MOTHER_REVIEW,
            "change may proceed to Mother review",
            True,
            False,
        )

    def capability_change_requires_mother(self) -> bool:
        return True

    def authority_change_requires_human(self) -> bool:
        return True

    def security_boundary_change_requires_human(self) -> bool:
        return True

    def soul_change_allowed(self) -> bool:
        return False

    def constitution_change_allowed(self) -> bool:
        return False

    def verification_bypass_allowed(self) -> bool:
        return False

    def audit_bypass_allowed(self) -> bool:
        return False

    def self_authorization_allowed(self) -> bool:
        return False

    def external_model_can_authorize(self) -> bool:
        return False

    def capability_equals_authority(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False

    def executes_upgrade(self) -> bool:
        return False


if __name__ == "__main__":
    governance = ChildSelfImprovementGovernance()

    request = ChangeGovernanceRequest(
        request_id="change-001",
        child_brain_id="child-001",
        category=ChangeCategory.REASONING,
        risk=ChangeRisk.MEDIUM,
        increases_capability=True,
        changes_authority=False,
        changes_security_boundary=False,
        changes_soul=False,
        changes_constitution=False,
        bypasses_verification=False,
        bypasses_audit=False,
    )

    result = governance.evaluate(request)

    assert result.decision == GovernanceDecision.ALLOW_MOTHER_REVIEW
    assert result.requires_mother is True
    assert result.requires_human is False

    assert governance.capability_change_requires_mother() is True
    assert governance.authority_change_requires_human() is True
    assert governance.security_boundary_change_requires_human() is True
    assert governance.soul_change_allowed() is False
    assert governance.constitution_change_allowed() is False
    assert governance.verification_bypass_allowed() is False
    assert governance.audit_bypass_allowed() is False
    assert governance.self_authorization_allowed() is False
    assert governance.external_model_can_authorize() is False
    assert governance.capability_equals_authority() is False
    assert governance.creates_real_child() is False
    assert governance.activates_real_child() is False
    assert governance.executes_upgrade() is False

    print("SAHIBEX CHILD SELF-IMPROVEMENT GOVERNANCE TEST: PASS")
