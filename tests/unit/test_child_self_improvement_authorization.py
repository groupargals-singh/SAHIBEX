from core.brain.child_self_improvement_authorization import (
    AuthorizationDecision,
    ChildSelfImprovementAuthorization,
    UpgradeAuthorizationRequest,
)


def make_request(
    mother=True,
    human=True,
    human_required=True,
    security=True,
    regression=True,
    verification=True,
    audit=True,
    provenance=True,
    authority=True,
    same_version=False,
):
    return UpgradeAuthorizationRequest(
        proposal_id="proposal-001",
        child_brain_id="child-001",
        target="reasoning",
        version_before="1.0",
        version_after="1.0" if same_version else "1.1",
        mother_approved=mother,
        human_approved=human,
        human_required=human_required,
        security_verified=security,
        regression_verified=regression,
        verification_passed=verification,
        audit_complete=audit,
        provenance_complete=provenance,
        authority_boundary_intact=authority,
    )


def test_authorization_success():
    authorization = ChildSelfImprovementAuthorization()

    result = authorization.authorize(make_request())

    assert result.decision == AuthorizationDecision.AUTHORIZED
    assert authorization.authorization_is_valid(result) is True
    assert result.record.immutable is True
    assert result.record.execution_granted is False


def test_missing_mother_approval_blocks():
    authorization = ChildSelfImprovementAuthorization()

    result = authorization.authorize(
        make_request(mother=False)
    )

    assert result.decision == AuthorizationDecision.BLOCKED


def test_missing_human_approval_blocks():
    authorization = ChildSelfImprovementAuthorization()

    result = authorization.authorize(
        make_request(human=False)
    )

    assert result.decision == AuthorizationDecision.BLOCKED


def test_security_failure_blocks():
    authorization = ChildSelfImprovementAuthorization()

    result = authorization.authorize(
        make_request(security=False)
    )

    assert result.decision == AuthorizationDecision.BLOCKED


def test_regression_failure_blocks():
    authorization = ChildSelfImprovementAuthorization()

    result = authorization.authorize(
        make_request(regression=False)
    )

    assert result.decision == AuthorizationDecision.BLOCKED


def test_verification_failure_blocks():
    authorization = ChildSelfImprovementAuthorization()

    result = authorization.authorize(
        make_request(verification=False)
    )

    assert result.decision == AuthorizationDecision.BLOCKED


def test_audit_failure_blocks():
    authorization = ChildSelfImprovementAuthorization()

    result = authorization.authorize(
        make_request(audit=False)
    )

    assert result.decision == AuthorizationDecision.BLOCKED


def test_provenance_failure_blocks():
    authorization = ChildSelfImprovementAuthorization()

    result = authorization.authorize(
        make_request(provenance=False)
    )

    assert result.decision == AuthorizationDecision.BLOCKED


def test_authority_boundary_failure_blocks():
    authorization = ChildSelfImprovementAuthorization()

    result = authorization.authorize(
        make_request(authority=False)
    )

    assert result.decision == AuthorizationDecision.BLOCKED


def test_same_version_blocks():
    authorization = ChildSelfImprovementAuthorization()

    result = authorization.authorize(
        make_request(same_version=True)
    )

    assert result.decision == AuthorizationDecision.BLOCKED


def test_authorization_does_not_execute():
    authorization = ChildSelfImprovementAuthorization()

    result = authorization.authorize(make_request())

    assert authorization.execution_is_granted(result) is False
    assert authorization.executes_upgrade() is False
    assert authorization.grants_general_authority() is False


def test_soul_constitution_unchanged():
    authorization = ChildSelfImprovementAuthorization()

    assert authorization.modifies_soul() is False
    assert authorization.modifies_constitution() is False


def test_no_child_creation_or_activation():
    authorization = ChildSelfImprovementAuthorization()

    assert authorization.creates_real_child() is False
    assert authorization.activates_real_child() is False


if __name__ == "__main__":
    test_authorization_success()
    test_missing_mother_approval_blocks()
    test_missing_human_approval_blocks()
    test_security_failure_blocks()
    test_regression_failure_blocks()
    test_verification_failure_blocks()
    test_audit_failure_blocks()
    test_provenance_failure_blocks()
    test_authority_boundary_failure_blocks()
    test_same_version_blocks()
    test_authorization_does_not_execute()
    test_soul_constitution_unchanged()
    test_no_child_creation_or_activation()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT AUTHORIZATION TEST: PASS"
    )
