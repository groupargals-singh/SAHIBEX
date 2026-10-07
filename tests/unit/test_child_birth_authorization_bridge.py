from core.brain.child_birth_authorization_bridge import (
    BirthAuthorizationDecision,
    BirthAuthorizationRequest,
    ChildBirthAuthorizationBridge,
)


def main() -> None:
    bridge = ChildBirthAuthorizationBridge()

    request = BirthAuthorizationRequest(
        proposal_id="birth-proposal-001",
        child_brain_id="child-brain-001",
        purpose="specialist research intelligence",
    )

    # No approvals
    result = bridge.evaluate(request)

    assert result.allowed is False
    assert result.decision == BirthAuthorizationDecision.REQUIRE_MOTHER

    # Mother only
    result = bridge.evaluate(
        request,
        mother_approved=True,
    )

    assert result.allowed is False
    assert result.decision == BirthAuthorizationDecision.REQUIRE_HUMAN

    # Both approvals
    result = bridge.evaluate(
        request,
        mother_approved=True,
        human_approved=True,
    )

    assert result.allowed is True
    assert result.decision == BirthAuthorizationDecision.AUTHORIZED

    # Missing proposal identity
    result = bridge.evaluate(
        BirthAuthorizationRequest(
            proposal_id="",
            child_brain_id="child-brain-002",
            purpose="research",
        ),
        mother_approved=True,
        human_approved=True,
    )

    assert result.allowed is False
    assert result.decision == BirthAuthorizationDecision.DENIED

    # Missing child identity
    result = bridge.evaluate(
        BirthAuthorizationRequest(
            proposal_id="birth-proposal-003",
            child_brain_id="",
            purpose="research",
        ),
        mother_approved=True,
        human_approved=True,
    )

    assert result.allowed is False

    # Missing purpose
    result = bridge.evaluate(
        BirthAuthorizationRequest(
            proposal_id="birth-proposal-004",
            child_brain_id="child-brain-004",
            purpose="",
        ),
        mother_approved=True,
        human_approved=True,
    )

    assert result.allowed is False

    # Security invariants
    assert not bridge.can_child_authorize_birth()
    assert not bridge.can_mother_authorize_without_human()
    assert not bridge.can_external_model_authorize()
    assert not bridge.can_tool_authorize()
    assert not bridge.can_self_authorize()
    assert not bridge.can_execute_birth()

    assert bridge.requires_mother_approval()
    assert bridge.requires_human_approval()

    print("SAHIBEX CHILD BIRTH AUTHORIZATION BRIDGE TEST: PASS")


if __name__ == "__main__":
    main()
