from core.policies.constitution import SahibexConstitution


def main() -> None:
    constitution = SahibexConstitution()

    assert constitution.child_soul_constitution_dna_version() == "1.0"

    inherited = constitution.child_soul_inherited_principles()
    own = constitution.child_soul_own_principles()
    forbidden = constitution.child_soul_forbidden_inheritance()
    limits = constitution.child_soul_authority_limits()
    changes = constitution.child_soul_change_protocol()
    naming = constitution.child_soul_naming_protocol()

    # Independent soul / constitution
    assert constitution.child_soul_is_independent() is True
    assert constitution.child_soul_has_own_constitution() is True
    assert constitution.child_soul_has_own_identity() is True

    # Independent naming
    assert constitution.child_soul_has_own_name() is True
    assert constitution.child_soul_name_is_assigned_at_birth() is True
    assert constitution.child_soul_name_is_not_hardcoded_now() is True

    # Principles are inherited, identity is not
    assert constitution.child_soul_inherits_principles_not_identity() is True
    assert "human_supremacy" in inherited
    assert "permission_gated_action" in inherited
    assert "verification_required" in inherited
    assert "security_required" in inherited

    # Child has its own constitutional principles
    assert "independent_soul_identity" in own
    assert "independent_constitution_identity" in own
    assert "independent_brain_identity" in own
    assert "independent_memory" in own
    assert "independent_rules" in own

    # Mother identity/soul/memory/authority must not be inherited
    assert "mother_brain_identity" in forbidden
    assert "mother_soul_identity" in forbidden
    assert "mother_constitution_identity" in forbidden
    assert "mother_name" in forbidden
    assert "mother_memory" in forbidden
    assert "mother_authority" in forbidden

    assert constitution.child_soul_inherits_mother_memory() is False
    assert constitution.child_soul_inherits_mother_authority() is False
    assert constitution.child_soul_inherits_mother_soul() is False

    # Authority limits
    assert "cannot_override_human" in limits
    assert "cannot_override_mother" in limits
    assert "cannot_modify_own_soul" in limits
    assert "cannot_escalate_authority" in limits
    assert "cannot_self_authorize_protected_action" in limits

    assert constitution.child_soul_can_modify_itself() is False
    assert constitution.child_soul_can_modify_mother() is False
    assert constitution.child_soul_can_override_mother() is False
    assert constitution.child_soul_can_override_human() is False
    assert constitution.child_soul_can_escalate_authority() is False

    # Constitutional change protocol
    assert "change_must_be_proposed" in changes
    assert "change_must_explain_reason" in changes
    assert "change_must_describe_expected_effects" in changes
    assert "change_must_include_security_impact" in changes
    assert "change_must_include_authority_impact" in changes
    assert "human_must_explicitly_approve" in changes
    assert "approved_change_must_be_audited" in changes
    assert "rejected_change_must_not_be_applied" in changes

    assert constitution.child_soul_change_requires_human_approval() is True
    assert constitution.child_soul_change_requires_verification() is True
    assert constitution.child_soul_change_requires_audit() is True

    # Naming protocol
    assert "name_assigned_at_birth" in naming
    assert "name_is_unique_child_identity" in naming
    assert "name_is_not_mother_name" in naming
    assert "name_is_not_hardcoded_before_birth" in naming
    assert "human_may_provide_name" in naming
    assert "sahibex_may_propose_name" in naming

    print("SAHIBEX CHILD SOUL / CONSTITUTION DNA TEST: PASS")


if __name__ == "__main__":
    main()
