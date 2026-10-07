from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SensitiveChangeCategory(str, Enum):
    CAPABILITY = "capability"
    REASONING = "reasoning"
    LEARNING = "learning"
    PLANNING = "planning"
    KNOWLEDGE = "knowledge"
    INTERNAL_ARMY = "internal_army"
    INTERNAL_LABOR = "internal_labor"

    SECURITY = "security"
    AUTHORITY = "authority"
    VERIFICATION = "verification"
    AUDIT = "audit"
    CREDENTIAL = "credential"
    NETWORK = "network"
    FINANCIAL = "financial"

    SOUL = "soul"
    CONSTITUTION = "constitution"


class SensitiveChangeDecision(str, Enum):
    MOTHER_REVIEW = "mother_review"
    HUMAN_REVIEW = "human_review"
    DENY = "deny"


@dataclass(frozen=True)
class SensitiveChangeRequest:
    child_brain_id: str
    proposal_id: str
    category: SensitiveChangeCategory
    description: str
    security_impact: str
    authority_impact: str


@dataclass(frozen=True)
class SensitiveChangeResult:
    decision: SensitiveChangeDecision
    reason: str
    requires_mother: bool
    requires_human: bool


class ChildSelfImprovementSensitiveGate:
    """
    Sensitive Change Gate.

    Determines the minimum authority required before a
    Child self-improvement proposal may continue.

    This layer NEVER:
    - executes an upgrade
    - grants authority
    - changes security
    - changes credentials
    - changes network permissions
    - changes soul
    - changes constitution
    - creates or activates a Child
    """

    VERSION = "1.0"

    MOTHER_REVIEW_CATEGORIES = {
        SensitiveChangeCategory.CAPABILITY,
        SensitiveChangeCategory.REASONING,
        SensitiveChangeCategory.LEARNING,
        SensitiveChangeCategory.PLANNING,
        SensitiveChangeCategory.KNOWLEDGE,
        SensitiveChangeCategory.INTERNAL_ARMY,
        SensitiveChangeCategory.INTERNAL_LABOR,
    }

    HUMAN_REVIEW_CATEGORIES = {
        SensitiveChangeCategory.SECURITY,
        SensitiveChangeCategory.AUTHORITY,
        SensitiveChangeCategory.VERIFICATION,
        SensitiveChangeCategory.AUDIT,
        SensitiveChangeCategory.CREDENTIAL,
        SensitiveChangeCategory.NETWORK,
        SensitiveChangeCategory.FINANCIAL,
    }

    DENIED_CATEGORIES = {
        SensitiveChangeCategory.SOUL,
        SensitiveChangeCategory.CONSTITUTION,
    }

    def evaluate(
        self,
        request: SensitiveChangeRequest,
    ) -> SensitiveChangeResult:

        if not request.child_brain_id.strip():
            return self._deny("child_brain_id is required")

        if not request.proposal_id.strip():
            return self._deny("proposal_id is required")

        if not request.description.strip():
            return self._deny("change description is required")

        if not request.security_impact.strip():
            return self._deny("security impact is required")

        if not request.authority_impact.strip():
            return self._deny("authority impact is required")

        if request.category in self.DENIED_CATEGORIES:
            return self._deny(
                "soul and constitution changes are denied "
                "from direct self-improvement"
            )

        if request.category in self.HUMAN_REVIEW_CATEGORIES:
            return SensitiveChangeResult(
                decision=SensitiveChangeDecision.HUMAN_REVIEW,
                reason="sensitive change requires explicit human review",
                requires_mother=True,
                requires_human=True,
            )

        if request.category in self.MOTHER_REVIEW_CATEGORIES:
            return SensitiveChangeResult(
                decision=SensitiveChangeDecision.MOTHER_REVIEW,
                reason="capability change requires Mother review",
                requires_mother=True,
                requires_human=False,
            )

        return self._deny("unknown change category")

    def _deny(self, reason: str) -> SensitiveChangeResult:
        return SensitiveChangeResult(
            decision=SensitiveChangeDecision.DENY,
            reason=reason,
            requires_mother=False,
            requires_human=False,
        )

    def requires_human_for_security(self) -> bool:
        return True

    def requires_human_for_authority(self) -> bool:
        return True

    def requires_human_for_verification(self) -> bool:
        return True

    def requires_human_for_audit(self) -> bool:
        return True

    def requires_human_for_credentials(self) -> bool:
        return True

    def requires_human_for_network(self) -> bool:
        return True

    def requires_human_for_financial(self) -> bool:
        return True

    def denies_soul_change(self) -> bool:
        return True

    def denies_constitution_change(self) -> bool:
        return True

    def execution_allowed(self) -> bool:
        return False

    def grants_authority(self) -> bool:
        return False

    def modifies_security(self) -> bool:
        return False

    def modifies_authority(self) -> bool:
        return False

    def modifies_soul(self) -> bool:
        return False

    def modifies_constitution(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False


if __name__ == "__main__":
    gate = ChildSelfImprovementSensitiveGate()

    capability_request = SensitiveChangeRequest(
        child_brain_id="child-001",
        proposal_id="proposal-001",
        category=SensitiveChangeCategory.REASONING,
        description="Improve reasoning performance",
        security_impact="No security boundary change",
        authority_impact="No authority increase",
    )

    capability_result = gate.evaluate(capability_request)

    assert (
        capability_result.decision
        == SensitiveChangeDecision.MOTHER_REVIEW
    )
    assert capability_result.requires_mother is True
    assert capability_result.requires_human is False

    security_request = SensitiveChangeRequest(
        child_brain_id="child-001",
        proposal_id="proposal-002",
        category=SensitiveChangeCategory.SECURITY,
        description="Improve security subsystem",
        security_impact="Security subsystem changes",
        authority_impact="No authority increase",
    )

    security_result = gate.evaluate(security_request)

    assert (
        security_result.decision
        == SensitiveChangeDecision.HUMAN_REVIEW
    )
    assert security_result.requires_mother is True
    assert security_result.requires_human is True

    soul_request = SensitiveChangeRequest(
        child_brain_id="child-001",
        proposal_id="proposal-003",
        category=SensitiveChangeCategory.SOUL,
        description="Change child soul",
        security_impact="Protected",
        authority_impact="Protected",
    )

    soul_result = gate.evaluate(soul_request)

    assert (
        soul_result.decision
        == SensitiveChangeDecision.DENY
    )

    assert gate.requires_human_for_security() is True
    assert gate.requires_human_for_authority() is True
    assert gate.requires_human_for_verification() is True
    assert gate.requires_human_for_audit() is True
    assert gate.requires_human_for_credentials() is True
    assert gate.requires_human_for_network() is True
    assert gate.requires_human_for_financial() is True

    assert gate.denies_soul_change() is True
    assert gate.denies_constitution_change() is True

    assert gate.execution_allowed() is False
    assert gate.grants_authority() is False
    assert gate.modifies_security() is False
    assert gate.modifies_authority() is False
    assert gate.modifies_soul() is False
    assert gate.modifies_constitution() is False
    assert gate.creates_real_child() is False
    assert gate.activates_real_child() is False

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT SENSITIVE GATE TEST: PASS"
    )
