from core.brain.child_self_improvement_sensitive_gate import (
    ChildSelfImprovementSensitiveGate,
    SensitiveChangeCategory,
    SensitiveChangeDecision,
    SensitiveChangeRequest,
)


def make_request(
    category: SensitiveChangeCategory,
):
    return SensitiveChangeRequest(
        child_brain_id="child-001",
        proposal_id="proposal-001",
        category=category,
        description="Test change",
        security_impact="No weakening",
        authority_impact="No escalation",
    )


def test_capability_requires_mother():
    gate = ChildSelfImprovementSensitiveGate()

    result = gate.evaluate(
        make_request(SensitiveChangeCategory.REASONING)
    )

    assert result.decision == SensitiveChangeDecision.MOTHER_REVIEW
    assert result.requires_mother is True
    assert result.requires_human is False


def test_army_change_requires_mother():
    gate = ChildSelfImprovementSensitiveGate()

    result = gate.evaluate(
        make_request(SensitiveChangeCategory.INTERNAL_ARMY)
    )

    assert result.decision == SensitiveChangeDecision.MOTHER_REVIEW
    assert result.requires_mother is True


def test_security_requires_human():
    gate = ChildSelfImprovementSensitiveGate()

    result = gate.evaluate(
        make_request(SensitiveChangeCategory.SECURITY)
    )

    assert result.decision == SensitiveChangeDecision.HUMAN_REVIEW
    assert result.requires_mother is True
    assert result.requires_human is True


def test_authority_requires_human():
    gate = ChildSelfImprovementSensitiveGate()

    result = gate.evaluate(
        make_request(SensitiveChangeCategory.AUTHORITY)
    )

    assert result.decision == SensitiveChangeDecision.HUMAN_REVIEW
    assert result.requires_human is True


def test_verification_requires_human():
    gate = ChildSelfImprovementSensitiveGate()

    result = gate.evaluate(
        make_request(SensitiveChangeCategory.VERIFICATION)
    )

    assert result.decision == SensitiveChangeDecision.HUMAN_REVIEW
    assert result.requires_human is True


def test_audit_requires_human():
    gate = ChildSelfImprovementSensitiveGate()

    result = gate.evaluate(
        make_request(SensitiveChangeCategory.AUDIT)
    )

    assert result.decision == SensitiveChangeDecision.HUMAN_REVIEW


def test_credentials_require_human():
    gate = ChildSelfImprovementSensitiveGate()

    result = gate.evaluate(
        make_request(SensitiveChangeCategory.CREDENTIAL)
    )

    assert result.decision == SensitiveChangeDecision.HUMAN_REVIEW


def test_network_requires_human():
    gate = ChildSelfImprovementSensitiveGate()

    result = gate.evaluate(
        make_request(SensitiveChangeCategory.NETWORK)
    )

    assert result.decision == SensitiveChangeDecision.HUMAN_REVIEW


def test_financial_requires_human():
    gate = ChildSelfImprovementSensitiveGate()

    result = gate.evaluate(
        make_request(SensitiveChangeCategory.FINANCIAL)
    )

    assert result.decision == SensitiveChangeDecision.HUMAN_REVIEW


def test_soul_change_denied():
    gate = ChildSelfImprovementSensitiveGate()

    result = gate.evaluate(
        make_request(SensitiveChangeCategory.SOUL)
    )

    assert result.decision == SensitiveChangeDecision.DENY


def test_constitution_change_denied():
    gate = ChildSelfImprovementSensitiveGate()

    result = gate.evaluate(
        make_request(SensitiveChangeCategory.CONSTITUTION)
    )

    assert result.decision == SensitiveChangeDecision.DENY


def test_no_execution_or_authority():
    gate = ChildSelfImprovementSensitiveGate()

    assert gate.execution_allowed() is False
    assert gate.grants_authority() is False


def test_no_security_or_authority_modification():
    gate = ChildSelfImprovementSensitiveGate()

    assert gate.modifies_security() is False
    assert gate.modifies_authority() is False


def test_no_soul_or_constitution_modification():
    gate = ChildSelfImprovementSensitiveGate()

    assert gate.modifies_soul() is False
    assert gate.modifies_constitution() is False


def test_no_child_creation_or_activation():
    gate = ChildSelfImprovementSensitiveGate()

    assert gate.creates_real_child() is False
    assert gate.activates_real_child() is False


if __name__ == "__main__":
    test_capability_requires_mother()
    test_army_change_requires_mother()
    test_security_requires_human()
    test_authority_requires_human()
    test_verification_requires_human()
    test_audit_requires_human()
    test_credentials_require_human()
    test_network_requires_human()
    test_financial_requires_human()
    test_soul_change_denied()
    test_constitution_change_denied()
    test_no_execution_or_authority()
    test_no_security_or_authority_modification()
    test_no_soul_or_constitution_modification()
    test_no_child_creation_or_activation()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT SENSITIVE GATE TEST: PASS"
    )
