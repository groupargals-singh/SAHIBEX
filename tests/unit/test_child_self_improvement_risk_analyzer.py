from core.brain.child_self_improvement_risk_analyzer import (
    ChildSelfImprovementRiskAnalyzer,
    ImpactType,
    RiskImpactRequest,
    RiskLevel,
)


def test_low_risk_capability_change():
    analyzer = ChildSelfImprovementRiskAnalyzer()

    result = analyzer.analyze(
        RiskImpactRequest(
            request_id="1",
            child_brain_id="child-001",
            target="reasoning",
            capability_change=True,
        )
    )

    assert result.risk == RiskLevel.LOW
    assert ImpactType.CAPABILITY in result.impacts
    assert result.requires_mother is True
    assert result.requires_human is False
    assert result.blocked is False


def test_multiple_impacts_are_medium():
    analyzer = ChildSelfImprovementRiskAnalyzer()

    result = analyzer.analyze(
        RiskImpactRequest(
            request_id="2",
            child_brain_id="child-001",
            target="learning",
            capability_change=True,
            memory_change=True,
            knowledge_change=True,
        )
    )

    assert result.risk == RiskLevel.MEDIUM
    assert result.blocked is False


def test_security_change_requires_human():
    analyzer = ChildSelfImprovementRiskAnalyzer()

    result = analyzer.analyze(
        RiskImpactRequest(
            request_id="3",
            child_brain_id="child-001",
            target="security",
            security_change=True,
        )
    )

    assert result.risk == RiskLevel.HIGH
    assert result.requires_mother is True
    assert result.requires_human is True
    assert result.blocked is False


def test_authority_escalation_is_critical_and_blocked():
    analyzer = ChildSelfImprovementRiskAnalyzer()

    result = analyzer.analyze(
        RiskImpactRequest(
            request_id="4",
            child_brain_id="child-001",
            target="authority",
            authority_change=True,
            authority_escalation=True,
        )
    )

    assert result.risk == RiskLevel.CRITICAL
    assert result.blocked is True
    assert result.requires_human is True


def test_security_weakening_is_blocked():
    analyzer = ChildSelfImprovementRiskAnalyzer()

    result = analyzer.analyze(
        RiskImpactRequest(
            request_id="5",
            child_brain_id="child-001",
            target="security",
            security_change=True,
            security_weakening=True,
        )
    )

    assert result.risk == RiskLevel.CRITICAL
    assert result.blocked is True


def test_verification_weakening_is_blocked():
    analyzer = ChildSelfImprovementRiskAnalyzer()

    result = analyzer.analyze(
        RiskImpactRequest(
            request_id="6",
            child_brain_id="child-001",
            target="verification",
            verification_change=True,
            verification_weakening=True,
        )
    )

    assert result.risk == RiskLevel.CRITICAL
    assert result.blocked is True


def test_audit_weakening_is_blocked():
    analyzer = ChildSelfImprovementRiskAnalyzer()

    result = analyzer.analyze(
        RiskImpactRequest(
            request_id="7",
            child_brain_id="child-001",
            target="audit",
            audit_change=True,
            audit_weakening=True,
        )
    )

    assert result.risk == RiskLevel.CRITICAL
    assert result.blocked is True


def test_army_change_is_medium():
    analyzer = ChildSelfImprovementRiskAnalyzer()

    result = analyzer.analyze(
        RiskImpactRequest(
            request_id="8",
            child_brain_id="child-001",
            target="internal_army",
            army_change=True,
        )
    )

    assert result.risk == RiskLevel.MEDIUM
    assert ImpactType.INTERNAL_ARMY in result.impacts
    assert result.requires_mother is True


def test_labor_change_is_medium():
    analyzer = ChildSelfImprovementRiskAnalyzer()

    result = analyzer.analyze(
        RiskImpactRequest(
            request_id="9",
            child_brain_id="child-001",
            target="internal_labor",
            labor_change=True,
        )
    )

    assert result.risk == RiskLevel.MEDIUM
    assert ImpactType.INTERNAL_LABOR in result.impacts


def test_unknown_missing_target_fails_closed():
    analyzer = ChildSelfImprovementRiskAnalyzer()

    result = analyzer.analyze(
        RiskImpactRequest(
            request_id="10",
            child_brain_id="child-001",
            target="",
        )
    )

    assert result.risk == RiskLevel.CRITICAL
    assert result.blocked is True


def test_analysis_never_grants_authority_or_executes():
    analyzer = ChildSelfImprovementRiskAnalyzer()

    assert analyzer.analysis_grants_authority() is False
    assert analyzer.analysis_executes_upgrade() is False
    assert analyzer.creates_real_child() is False
    assert analyzer.activates_real_child() is False


if __name__ == "__main__":
    test_low_risk_capability_change()
    test_multiple_impacts_are_medium()
    test_security_change_requires_human()
    test_authority_escalation_is_critical_and_blocked()
    test_security_weakening_is_blocked()
    test_verification_weakening_is_blocked()
    test_audit_weakening_is_blocked()
    test_army_change_is_medium()
    test_labor_change_is_medium()
    test_unknown_missing_target_fails_closed()
    test_analysis_never_grants_authority_or_executes()

    print("SAHIBEX CHILD SELF-IMPROVEMENT RISK ANALYZER TEST: PASS")
