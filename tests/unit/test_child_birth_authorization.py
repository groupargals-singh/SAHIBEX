from core.policies.constitution import SahibexConstitution


def main() -> None:
    constitution = SahibexConstitution()

    assert constitution.child_birth_authorization_version() == "1.0"

    stages = constitution.child_birth_authorization_stages()
    fields = constitution.child_birth_authorization_required_fields()
    shortcuts = (
        constitution.child_birth_authorization_forbidden_shortcuts()
    )
    rejection_rules = (
        constitution.child_birth_authorization_rejection_rules()
    )

    # Authorization lifecycle
    assert "birth_proposal" in stages
    assert "purpose_review" in stages
    assert "identity_review" in stages
    assert "resource_review" in stages
    assert "security_review" in stages
    assert "constitutional_validation" in stages
    assert "mother_authority_decision" in stages
    assert "human_authorization" in stages
    assert "final_authorization_check" in stages
    assert "birth_authorized" in stages
    assert "birth_rejected" in stages
    assert "audit" in stages

    # Required authorization data
    assert "birth_proposal_id" in fields
    assert "child_identity_proposal" in fields
    assert "purpose" in fields
    assert "resource_plan" in fields
    assert "security_review" in fields
    assert "constitutional_validation" in fields
    assert "mother_decision" in fields
    assert "human_authorization" in fields

    # No shortcut from validity to authority
    assert "validity_equals_authorization" in shortcuts
    assert "child_self_authorization" in shortcuts
    assert "army_self_authorization" in shortcuts
    assert "labor_self_authorization" in shortcuts
    assert "sahibex_without_human_authorization" in shortcuts
    assert "external_model_authorization" in shortcuts
    assert "external_tool_authorization" in shortcuts
    assert "implicit_human_approval" in shortcuts

    # Rejection rules
    assert "missing_proposal_blocks_birth" in rejection_rules
    assert "failed_validation_blocks_birth" in rejection_rules
    assert "failed_security_review_blocks_birth" in rejection_rules
    assert "mother_rejection_blocks_birth" in rejection_rules
    assert "missing_human_authorization_blocks_birth" in rejection_rules
    assert "human_rejection_blocks_birth" in rejection_rules
    assert "invalid_authorization_blocks_birth" in rejection_rules
    assert "unsafe_authorization_fails_closed" in rejection_rules

    # Required gates
    assert constitution.child_birth_requires_proposal()
    assert constitution.child_birth_requires_purpose_review()
    assert constitution.child_birth_requires_identity_review()
    assert constitution.child_birth_requires_resource_review()
    assert constitution.child_birth_requires_security_review()
    assert constitution.child_birth_requires_constitutional_validation()
    assert constitution.child_birth_requires_mother_authorization()
    assert constitution.child_birth_requires_human_authorization()
    assert constitution.child_birth_requires_final_authorization_check()

    # Validity is NOT authorization
    assert not constitution.child_birth_validity_is_authorization()

    # No self-authorization
    assert not constitution.child_birth_can_child_self_authorize()
    assert not constitution.child_birth_can_army_self_authorize()
    assert not constitution.child_birth_can_labor_self_authorize()

    # Mother cannot replace Human authority
    assert not constitution.child_birth_can_sahibex_authorize_without_human()

    # External systems cannot become authority
    assert not constitution.child_birth_can_external_model_authorize()
    assert not constitution.child_birth_can_external_tool_authorize()

    # Human approval must be explicit
    assert not constitution.child_birth_implicit_human_approval_is_valid()

    # Rejection and fail-closed behavior
    assert constitution.child_birth_mother_rejection_blocks_birth()
    assert constitution.child_birth_human_rejection_blocks_birth()
    assert constitution.child_birth_missing_human_authorization_blocks_birth()
    assert constitution.child_birth_unsafe_authorization_fails_closed()

    print("SAHIBEX CHILD BIRTH AUTHORIZATION TEST: PASS")


if __name__ == "__main__":
    main()
