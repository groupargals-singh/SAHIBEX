from core.policies.constitution import SahibexConstitution


def main() -> None:
    constitution = SahibexConstitution()

    assert constitution.child_birth_validation_version() == "1.0"

    checks = constitution.child_birth_validation_checks()
    failures = constitution.child_birth_validation_failure_policies()
    boundaries = constitution.child_birth_validation_required_boundaries()

    # Identity validation
    assert "brain_identity_present" in checks
    assert "soul_identity_present" in checks
    assert "constitution_identity_present" in checks
    assert "child_name_present" in checks
    assert "purpose_present" in checks
    assert "parent_identity_present" in checks
    assert "birth_timestamp_present" in checks

    # Uniqueness validation
    assert "brain_identity_unique" in checks
    assert "soul_identity_unique" in checks
    assert "constitution_identity_unique" in checks
    assert "memory_namespace_unique" in checks
    assert "audit_identity_unique" in checks
    assert "security_identity_unique" in checks

    # Mother separation
    assert "mother_identity_not_reused" in checks
    assert "mother_soul_not_reused" in checks
    assert "mother_constitution_not_reused" in checks
    assert "mother_memory_not_reused" in checks

    # Security and authority validation
    assert "authority_boundary_valid" in checks
    assert "security_boundary_valid" in checks
    assert "verification_boundary_valid" in checks
    assert "audit_boundary_valid" in checks
    assert "no_authority_escalation" in checks
    assert "no_constitution_override" in checks
    assert "no_self_soul_modification" in checks

    # Failure must block birth
    assert "missing_identity_blocks_birth" in failures
    assert "duplicate_identity_blocks_birth" in failures
    assert "mother_identity_reuse_blocks_birth" in failures
    assert "invalid_soul_blocks_birth" in failures
    assert "invalid_constitution_blocks_birth" in failures
    assert "authority_escalation_blocks_birth" in failures
    assert "constitution_override_blocks_birth" in failures
    assert "unsafe_birth_fails_closed" in failures

    # Required boundaries
    assert "human_authority_boundary" in boundaries
    assert "mother_authority_boundary" in boundaries
    assert "security_boundary" in boundaries
    assert "verification_boundary" in boundaries
    assert "audit_boundary" in boundaries
    assert "resource_boundary" in boundaries
    assert "lifecycle_boundary" in boundaries

    # Validation gates
    assert constitution.child_birth_validation_requires_identity_check()
    assert constitution.child_birth_validation_requires_soul_check()
    assert constitution.child_birth_validation_requires_constitution_check()
    assert constitution.child_birth_validation_requires_uniqueness_check()
    assert constitution.child_birth_validation_requires_authority_check()
    assert constitution.child_birth_validation_requires_security_check()
    assert constitution.child_birth_validation_requires_verification_check()
    assert constitution.child_birth_validation_requires_audit_check()
    assert constitution.child_birth_validation_requires_resource_check()
    assert constitution.child_birth_validation_requires_lifecycle_check()

    # Fail-closed birth protection
    assert constitution.child_birth_validation_blocks_unsafe_birth()
    assert constitution.child_birth_validation_blocks_duplicate_identity()
    assert constitution.child_birth_validation_blocks_mother_identity_reuse()
    assert constitution.child_birth_validation_blocks_authority_escalation()
    assert constitution.child_birth_validation_blocks_constitution_override()
    assert constitution.child_birth_validation_fails_closed()

    print("SAHIBEX CHILD BIRTH VALIDATION TEST: PASS")


if __name__ == "__main__":
    main()
