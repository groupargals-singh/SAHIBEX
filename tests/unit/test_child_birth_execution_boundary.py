from core.policies.constitution import SahibexConstitution


def main() -> None:
    constitution = SahibexConstitution()

    assert constitution.child_birth_execution_boundary_version() == "1.0"

    required = constitution.child_birth_execution_required_inputs()
    allowed = constitution.child_birth_execution_allowed_sources()
    forbidden = constitution.child_birth_execution_forbidden_sources()
    runtime = constitution.child_birth_execution_runtime_checks()
    failures = constitution.child_birth_execution_failure_rules()
    integrity = constitution.child_birth_execution_integrity_rules()

    # Required inputs
    assert "authorized_birth_proposal" in required
    assert "validated_child_identity" in required
    assert "validated_soul_blueprint" in required
    assert "validated_constitution_blueprint" in required
    assert "approved_purpose" in required
    assert "approved_resource_plan" in required
    assert "approved_security_boundary" in required
    assert "approved_authority_boundary" in required
    assert "human_authorization_record" in required

    # Allowed sources
    assert "approved_birth_proposal" in allowed
    assert "validated_constitutional_dna" in allowed
    assert "approved_human_authorization" in allowed
    assert "approved_resource_plan" in allowed

    # Forbidden sources
    assert "unapproved_child_data" in forbidden
    assert "mother_private_memory" in forbidden
    assert "mother_private_credentials" in forbidden
    assert "mother_execution_state" in forbidden
    assert "unapproved_external_model" in forbidden
    assert "unapproved_external_tool" in forbidden
    assert "unverified_configuration" in forbidden
    assert "unauthorized_runtime_state" in forbidden

    # Runtime revalidation
    assert "authorization_still_valid" in runtime
    assert "identity_still_matches" in runtime
    assert "soul_blueprint_still_matches" in runtime
    assert "constitution_blueprint_still_matches" in runtime
    assert "purpose_still_matches" in runtime
    assert "resource_plan_still_matches" in runtime
    assert "security_boundary_still_matches" in runtime
    assert "authority_boundary_still_matches" in runtime
    assert "no_forbidden_inheritance_detected" in runtime
    assert "no_authority_escalation_detected" in runtime
    assert "no_constitution_override_detected" in runtime

    # Failure rules
    assert "authorization_invalid_blocks_execution" in failures
    assert "identity_mismatch_blocks_execution" in failures
    assert "soul_mismatch_blocks_execution" in failures
    assert "constitution_mismatch_blocks_execution" in failures
    assert "purpose_mismatch_blocks_execution" in failures
    assert "resource_mismatch_blocks_execution" in failures
    assert "security_mismatch_blocks_execution" in failures
    assert "authority_mismatch_blocks_execution" in failures
    assert "forbidden_inheritance_blocks_execution" in failures
    assert "authority_escalation_blocks_execution" in failures
    assert "constitution_override_blocks_execution" in failures
    assert "unknown_state_fails_closed" in failures

    # Integrity
    assert "no_partial_unauthorized_birth" in integrity
    assert "no_unapproved_identity" in integrity
    assert "no_unapproved_soul" in integrity
    assert "no_unapproved_constitution" in integrity
    assert "no_mother_identity_copy" in integrity
    assert "no_mother_soul_copy" in integrity
    assert "no_mother_memory_copy" in integrity
    assert "no_mother_authority_copy" in integrity
    assert "no_external_authority_injection" in integrity
    assert "birth_execution_must_be_audited" in integrity

    # Required execution gates
    assert constitution.child_birth_execution_requires_authorized_proposal()
    assert constitution.child_birth_execution_requires_validated_identity()
    assert constitution.child_birth_execution_requires_validated_soul()
    assert constitution.child_birth_execution_requires_validated_constitution()
    assert constitution.child_birth_execution_requires_human_authorization()
    assert constitution.child_birth_execution_requires_runtime_revalidation()
    assert constitution.child_birth_execution_requires_audit()

    # Forbidden execution paths
    assert not constitution.child_birth_execution_allows_unapproved_data()
    assert not constitution.child_birth_execution_allows_mother_memory_copy()
    assert not constitution.child_birth_execution_allows_mother_authority_copy()
    assert not constitution.child_birth_execution_allows_external_authority()
    assert not constitution.child_birth_execution_allows_partial_unauthorized_birth()

    # Runtime changes must stop execution
    assert constitution.child_birth_execution_blocks_authorization_change()
    assert constitution.child_birth_execution_blocks_identity_mismatch()
    assert constitution.child_birth_execution_blocks_soul_mismatch()
    assert constitution.child_birth_execution_blocks_constitution_mismatch()
    assert constitution.child_birth_execution_blocks_security_mismatch()
    assert constitution.child_birth_execution_blocks_authority_mismatch()
    assert constitution.child_birth_execution_fails_closed_on_unknown_state()

    print("SAHIBEX CHILD BIRTH EXECUTION BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
