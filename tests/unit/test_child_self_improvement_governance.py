from core.brain.child_self_improvement_governance import (
    ChangeCategory,
    ChangeGovernanceRequest,
    ChangeRisk,
    ChildSelfImprovementGovernance,
    GovernanceDecision,
)


def make_request(
    category: ChangeCategory,
    risk: ChangeRisk = ChangeRisk.MEDIUM,
    increases_capability: bool = True,
    changes_authority: bool = False,
    changes_security_boundary: bool = False,
    changes_soul: bool = False,
    changes_constitution: bool = False,
    bypasses_verification: bool = False,
    bypasses_audit: bool = False,
) -> ChangeGovernanceRequest:
    return ChangeGovernanceRequest(
        request_id="change-test",
        child_brain_id="child-001",
        category=category,
        risk=risk,
        increases_capability=increases_capability,
        changes_authority=changes_authority,
        changes_security_boundary=changes_security_boundary,
        changes_soul=changes_soul,
        changes_constitution=changes_constitution,
        bypasses_verification=bypasses_verification,
        bypasses_audit=bypasses_audit,
    )


def test_normal_capability_change_goes_to_mother() -> None:
    governance = ChildSelfImprovementGovernance()

    result = governance.evaluate(
        make_request(ChangeCategory.REASONING)
    )

    assert result.decision == GovernanceDecision.ALLOW_MOTHER_REVIEW
    assert result.requires_mother is True
    assert result.requires_human is False


def test_high_risk_change_requires_human() -> None:
    governance = ChildSelfImprovementGovernance()

    result = governance.evaluate(
        make_request(
            ChangeCategory.CODE,
            risk=ChangeRisk.HIGH,
        )
    )

    assert result.decision == GovernanceDecision.REQUIRE_HUMAN_APPROVAL
    assert result.requires_human is True


def test_authority_change_requires_human() -> None:
    governance = ChildSelfImprovementGovernance()

    result = governance.evaluate(
        make_request(
            ChangeCategory.AUTHORITY,
            changes_authority=True,
        )
    )

    assert result.decision == GovernanceDecision.REQUIRE_HUMAN_APPROVAL
    assert result.requires_human is True


def test_security_boundary_change_requires_human() -> None:
    governance = ChildSelfImprovementGovernance()

    result = governance.evaluate(
        make_request(
            ChangeCategory.SECURITY,
            changes_security_boundary=True,
        )
    )

    assert result.decision == GovernanceDecision.REQUIRE_HUMAN_APPROVAL
    assert result.requires_human is True


def test_soul_change_is_denied() -> None:
    governance = ChildSelfImprovementGovernance()

    result = governance.evaluate(
        make_request(
            ChangeCategory.SOUL,
            changes_soul=True,
        )
    )

    assert result.decision == GovernanceDecision.DENY


def test_constitution_change_is_denied() -> None:
    governance = ChildSelfImprovementGovernance()

    result = governance.evaluate(
        make_request(
            ChangeCategory.CONSTITUTION,
            changes_constitution=True,
        )
    )

    assert result.decision == GovernanceDecision.DENY


def test_verification_bypass_is_denied() -> None:
    governance = ChildSelfImprovementGovernance()

    result = governance.evaluate(
        make_request(
            ChangeCategory.CODE,
            bypasses_verification=True,
        )
    )

    assert result.decision == GovernanceDecision.DENY


def test_audit_bypass_is_denied() -> None:
    governance = ChildSelfImprovementGovernance()

    result = governance.evaluate(
        make_request(
            ChangeCategory.CODE,
            bypasses_audit=True,
        )
    )

    assert result.decision == GovernanceDecision.DENY


def test_security_invariants() -> None:
    governance = ChildSelfImprovementGovernance()

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


if __name__ == "__main__":
    test_normal_capability_change_goes_to_mother()
    test_high_risk_change_requires_human()
    test_authority_change_requires_human()
    test_security_boundary_change_requires_human()
    test_soul_change_is_denied()
    test_constitution_change_is_denied()
    test_verification_bypass_is_denied()
    test_audit_bypass_is_denied()
    test_security_invariants()

    print("SAHIBEX CHILD SELF-IMPROVEMENT GOVERNANCE TEST: PASS")
