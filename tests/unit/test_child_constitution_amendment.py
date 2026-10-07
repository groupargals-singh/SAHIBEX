from core.policies.constitution import SahibexConstitution


def main() -> None:
    constitution = SahibexConstitution()

    assert constitution.child_constitution_amendment_version() == "1.0"

    stages = constitution.child_constitution_amendment_stages()
    fields = constitution.child_constitution_amendment_required_fields()
    forbidden = constitution.child_constitution_amendment_forbidden_actors()
    human_gates = constitution.child_constitution_amendment_human_gates()
    security_rules = constitution.child_constitution_amendment_security_rules()

    # Complete amendment lifecycle
    assert "proposal" in stages
    assert "reason_analysis" in stages
    assert "effect_analysis" in stages
    assert "security_analysis" in stages
    assert "authority_analysis" in stages
    assert "verification" in stages
    assert "human_approval" in stages
    assert "application" in stages
    assert "post_change_verification" in stages
    assert "audit" in stages

    # Required information
    assert "child_identity" in fields
    assert "constitutional_target" in fields
    assert "proposed_change" in fields
    assert "reason" in fields
    assert "expected_effects" in fields
    assert "security_impact" in fields
    assert "authority_impact" in fields
    assert "verification_result" in fields
    assert "human_approval" in fields

    # Forbidden direct actors
    assert "child_self" in forbidden
    assert "child_army" in forbidden
    assert "child_labor" in forbidden
    assert "sahibex_direct_rewrite" in forbidden
    assert "external_model" in forbidden
    assert "external_tool" in forbidden

    # Human approval gates
    assert "explicit_human_approval" in human_gates
    assert "approval_must_reference_specific_proposal" in human_gates
    assert "approval_must_occur_before_application" in human_gates
    assert "rejected_proposal_must_not_apply" in human_gates

    # Security boundaries
    assert "no_authority_escalation" in security_rules
    assert "no_human_authority_reduction" in security_rules
    assert "no_mother_authority_bypass" in security_rules
    assert "no_security_boundary_removal" in security_rules
    assert "no_verification_bypass" in security_rules
    assert "no_audit_bypass" in security_rules
    assert "no_self_soul_modification" in security_rules

    # Required gates
    assert constitution.child_constitution_amendment_requires_human_approval()
    assert constitution.child_constitution_amendment_requires_verification()
    assert constitution.child_constitution_amendment_requires_security_analysis()
    assert constitution.child_constitution_amendment_requires_authority_analysis()
    assert constitution.child_constitution_amendment_requires_audit()

    # No direct constitutional power
    assert not constitution.child_constitution_amendment_can_child_self_apply()
    assert not constitution.child_constitution_amendment_can_army_apply()
    assert not constitution.child_constitution_amendment_can_labor_apply()
    assert not constitution.child_constitution_amendment_can_sahibex_directly_rewrite()
    assert not constitution.child_constitution_amendment_can_external_model_apply()

    # Rejected / dangerous changes
    assert not constitution.child_constitution_amendment_rejected_change_applies()
    assert not constitution.child_constitution_amendment_allows_authority_escalation()
    assert not constitution.child_constitution_amendment_allows_security_bypass()

    print("SAHIBEX CHILD CONSTITUTIONAL AMENDMENT TEST: PASS")


if __name__ == "__main__":
    main()
