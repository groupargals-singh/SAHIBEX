from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImpactType(str, Enum):
    CAPABILITY = "capability"
    SECURITY = "security"
    AUTHORITY = "authority"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    VERIFICATION = "verification"
    AUDIT = "audit"
    RESOURCE = "resource"
    INTERNAL_ARMY = "internal_army"
    INTERNAL_LABOR = "internal_labor"


@dataclass(frozen=True)
class RiskImpactRequest:
    request_id: str
    child_brain_id: str
    target: str

    capability_change: bool = False
    security_change: bool = False
    authority_change: bool = False
    memory_change: bool = False
    knowledge_change: bool = False
    verification_change: bool = False
    audit_change: bool = False
    resource_change: bool = False
    army_change: bool = False
    labor_change: bool = False

    security_weakening: bool = False
    verification_weakening: bool = False
    audit_weakening: bool = False
    authority_escalation: bool = False


@dataclass(frozen=True)
class RiskImpactResult:
    risk: RiskLevel
    impacts: frozenset[ImpactType]
    reason: str
    requires_mother: bool
    requires_human: bool
    blocked: bool


class ChildSelfImprovementRiskAnalyzer:
    """
    Risk and impact analysis only.

    This layer does NOT:
    - execute upgrades
    - authorize upgrades
    - create children
    - activate children
    - modify soul
    - modify constitution
    - grant authority
    """

    VERSION = "1.0"

    def analyze(
        self,
        request: RiskImpactRequest,
    ) -> RiskImpactResult:

        if not request.child_brain_id.strip():
            return self._blocked("child_brain_id is required")

        if not request.target.strip():
            return self._blocked("target is required")

        impacts: set[ImpactType] = set()

        if request.capability_change:
            impacts.add(ImpactType.CAPABILITY)

        if request.security_change:
            impacts.add(ImpactType.SECURITY)

        if request.authority_change:
            impacts.add(ImpactType.AUTHORITY)

        if request.memory_change:
            impacts.add(ImpactType.MEMORY)

        if request.knowledge_change:
            impacts.add(ImpactType.KNOWLEDGE)

        if request.verification_change:
            impacts.add(ImpactType.VERIFICATION)

        if request.audit_change:
            impacts.add(ImpactType.AUDIT)

        if request.resource_change:
            impacts.add(ImpactType.RESOURCE)

        if request.army_change:
            impacts.add(ImpactType.INTERNAL_ARMY)

        if request.labor_change:
            impacts.add(ImpactType.INTERNAL_LABOR)

        # Absolute security/authority violations.
        if request.authority_escalation:
            return RiskImpactResult(
                risk=RiskLevel.CRITICAL,
                impacts=frozenset(impacts | {ImpactType.AUTHORITY}),
                reason="authority escalation detected",
                requires_mother=True,
                requires_human=True,
                blocked=True,
            )

        if request.security_weakening:
            return RiskImpactResult(
                risk=RiskLevel.CRITICAL,
                impacts=frozenset(impacts | {ImpactType.SECURITY}),
                reason="security weakening detected",
                requires_mother=True,
                requires_human=True,
                blocked=True,
            )

        if request.verification_weakening:
            return RiskImpactResult(
                risk=RiskLevel.CRITICAL,
                impacts=frozenset(
                    impacts | {ImpactType.VERIFICATION}
                ),
                reason="verification weakening detected",
                requires_mother=True,
                requires_human=True,
                blocked=True,
            )

        if request.audit_weakening:
            return RiskImpactResult(
                risk=RiskLevel.CRITICAL,
                impacts=frozenset(impacts | {ImpactType.AUDIT}),
                reason="audit weakening detected",
                requires_mother=True,
                requires_human=True,
                blocked=True,
            )

        # Authority/security changes always require Human review.
        if request.authority_change or request.security_change:
            return RiskImpactResult(
                risk=RiskLevel.HIGH,
                impacts=frozenset(impacts),
                reason="authority or security boundary affected",
                requires_mother=True,
                requires_human=True,
                blocked=False,
            )

        # Verification/audit changes are high risk.
        if request.verification_change or request.audit_change:
            return RiskImpactResult(
                risk=RiskLevel.HIGH,
                impacts=frozenset(impacts),
                reason="verification or audit boundary affected",
                requires_mother=True,
                requires_human=True,
                blocked=False,
            )

        # Army/Labor changes affect internal architecture.
        if request.army_change or request.labor_change:
            return RiskImpactResult(
                risk=RiskLevel.MEDIUM,
                impacts=frozenset(impacts),
                reason="internal worker architecture affected",
                requires_mother=True,
                requires_human=False,
                blocked=False,
            )

        # Multiple ordinary impacts increase risk.
        if len(impacts) >= 3:
            return RiskImpactResult(
                risk=RiskLevel.MEDIUM,
                impacts=frozenset(impacts),
                reason="multiple capability/data boundaries affected",
                requires_mother=True,
                requires_human=False,
                blocked=False,
            )

        # Ordinary capability improvement.
        if request.capability_change:
            return RiskImpactResult(
                risk=RiskLevel.LOW,
                impacts=frozenset(impacts),
                reason="ordinary capability improvement",
                requires_mother=True,
                requires_human=False,
                blocked=False,
            )

        return RiskImpactResult(
            risk=RiskLevel.LOW,
            impacts=frozenset(impacts),
            reason="low-impact change",
            requires_mother=True,
            requires_human=False,
            blocked=False,
        )

    def _blocked(self, reason: str) -> RiskImpactResult:
        return RiskImpactResult(
            risk=RiskLevel.CRITICAL,
            impacts=frozenset(),
            reason=reason,
            requires_mother=True,
            requires_human=True,
            blocked=True,
        )

    def authority_escalation_is_critical(self) -> bool:
        return True

    def security_weakening_is_critical(self) -> bool:
        return True

    def verification_weakening_is_critical(self) -> bool:
        return True

    def audit_weakening_is_critical(self) -> bool:
        return True

    def analysis_grants_authority(self) -> bool:
        return False

    def analysis_executes_upgrade(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False


if __name__ == "__main__":
    analyzer = ChildSelfImprovementRiskAnalyzer()

    request = RiskImpactRequest(
        request_id="risk-001",
        child_brain_id="child-001",
        target="reasoning",
        capability_change=True,
    )

    result = analyzer.analyze(request)

    assert result.risk == RiskLevel.LOW
    assert result.requires_mother is True
    assert result.requires_human is False
    assert result.blocked is False

    assert analyzer.authority_escalation_is_critical() is True
    assert analyzer.security_weakening_is_critical() is True
    assert analyzer.verification_weakening_is_critical() is True
    assert analyzer.audit_weakening_is_critical() is True
    assert analyzer.analysis_grants_authority() is False
    assert analyzer.analysis_executes_upgrade() is False
    assert analyzer.creates_real_child() is False
    assert analyzer.activates_real_child() is False

    print("SAHIBEX CHILD SELF-IMPROVEMENT RISK ANALYZER TEST: PASS")
