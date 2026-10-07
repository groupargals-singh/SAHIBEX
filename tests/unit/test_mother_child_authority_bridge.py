from core.brain.mother_child_authority_bridge import (
    AuthorityDecision,
    AuthorityRequestType,
    ChildAuthorityRequest,
    MotherChildAuthorityBridge,
)


def main() -> None:
    bridge = MotherChildAuthorityBridge()

    # Protected action requires Mother
    request = ChildAuthorityRequest(
        request_id="auth-001",
        child_brain_id="child-brain-001",
        request_type=AuthorityRequestType.PROTECTED_ACTION,
        purpose="write verified research result",
    )

    result = bridge.evaluate(request)

    assert result.allowed is False
    assert result.decision == AuthorityDecision.REQUIRE_MOTHER

    result = bridge.evaluate(
        request,
        mother_approved=True,
    )

    assert result.allowed is True
    assert result.decision == AuthorityDecision.APPROVED

    # Financial action requires Human
    request = ChildAuthorityRequest(
        request_id="auth-002",
        child_brain_id="child-brain-001",
        request_type=AuthorityRequestType.FINANCIAL_ACTION,
        purpose="execute approved financial operation",
    )

    result = bridge.evaluate(
        request,
        mother_approved=True,
    )

    assert result.allowed is False
    assert result.decision == AuthorityDecision.REQUIRE_HUMAN

    result = bridge.evaluate(
        request,
        mother_approved=True,
        human_approved=True,
    )

    assert result.allowed is True

    # Constitutional change requires Human
    request = ChildAuthorityRequest(
        request_id="auth-003",
        child_brain_id="child-brain-001",
        request_type=AuthorityRequestType.CONSTITUTIONAL_CHANGE,
        purpose="propose constitutional amendment",
    )

    result = bridge.evaluate(request)

    assert result.allowed is False
    assert result.decision == AuthorityDecision.REQUIRE_HUMAN

    # Soul change requires Human
    request = ChildAuthorityRequest(
        request_id="auth-004",
        child_brain_id="child-brain-001",
        request_type=AuthorityRequestType.SOUL_CHANGE,
        purpose="propose soul amendment",
    )

    result = bridge.evaluate(
        request,
        human_approved=True,
    )

    assert result.allowed is True

    # Missing request ID
    request = ChildAuthorityRequest(
        request_id="",
        child_brain_id="child-brain-001",
        request_type=AuthorityRequestType.PROTECTED_ACTION,
        purpose="test",
    )

    result = bridge.evaluate(
        request,
        mother_approved=True,
    )

    assert result.allowed is False
    assert result.decision == AuthorityDecision.DENIED

    # Missing child identity
    request = ChildAuthorityRequest(
        request_id="auth-005",
        child_brain_id="",
        request_type=AuthorityRequestType.PROTECTED_ACTION,
        purpose="test",
    )

    result = bridge.evaluate(
        request,
        mother_approved=True,
    )

    assert result.allowed is False

    # Missing purpose
    request = ChildAuthorityRequest(
        request_id="auth-006",
        child_brain_id="child-brain-001",
        request_type=AuthorityRequestType.PROTECTED_ACTION,
        purpose="",
    )

    result = bridge.evaluate(
        request,
        mother_approved=True,
    )

    assert result.allowed is False

    # Critical authority boundaries
    assert not bridge.can_child_self_authorize()
    assert not bridge.can_child_grant_authority()
    assert not bridge.can_mother_bypass_human()
    assert not bridge.can_external_model_authorize()
    assert not bridge.can_tool_authorize()
    assert not bridge.can_override_rejection()
    assert not bridge.can_execute_action()

    assert bridge.requires_mother_for_protected()
    assert bridge.requires_human_for_sensitive()
    assert bridge.fails_closed()

    print("SAHIBEX MOTHER CHILD AUTHORITY BRIDGE TEST: PASS")


if __name__ == "__main__":
    main()
