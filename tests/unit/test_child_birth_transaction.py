from core.policies.constitution import SahibexConstitution


def main() -> None:
    constitution = SahibexConstitution()

    assert constitution.child_birth_transaction_version() == "1.0"

    stages = constitution.child_birth_transaction_stages()
    components = constitution.child_birth_transaction_critical_components()
    aborts = constitution.child_birth_transaction_abort_conditions()
    commits = constitution.child_birth_transaction_commit_requirements()
    rollback = constitution.child_birth_transaction_rollback_rules()

    # Transaction lifecycle
    assert "prepare" in stages
    assert "validate" in stages
    assert "authorize" in stages
    assert "create_identity" in stages
    assert "create_soul" in stages
    assert "create_constitution" in stages
    assert "create_memory_namespace" in stages
    assert "create_security_identity" in stages
    assert "create_audit_identity" in stages
    assert "create_resource_boundary" in stages
    assert "create_lifecycle_boundary" in stages
    assert "verify_complete_birth" in stages
    assert "commit" in stages

    # Critical components
    assert "brain_identity" in components
    assert "soul_identity" in components
    assert "constitution_identity" in components
    assert "memory_namespace" in components
    assert "security_identity" in components
    assert "audit_identity" in components
    assert "resource_boundary" in components
    assert "lifecycle_boundary" in components
    assert "authority_boundary" in components
    assert "verification_boundary" in components

    # Abort conditions
    assert "validation_failure" in aborts
    assert "authorization_failure" in aborts
    assert "identity_creation_failure" in aborts
    assert "soul_creation_failure" in aborts
    assert "constitution_creation_failure" in aborts
    assert "memory_creation_failure" in aborts
    assert "security_identity_failure" in aborts
    assert "audit_identity_failure" in aborts
    assert "resource_boundary_failure" in aborts
    assert "lifecycle_boundary_failure" in aborts
    assert "authority_boundary_failure" in aborts
    assert "verification_failure" in aborts
    assert "integrity_failure" in aborts
    assert "unknown_state" in aborts

    # Commit requirements
    assert "all_required_components_created" in commits
    assert "all_components_verified" in commits
    assert "identity_integrity_verified" in commits
    assert "soul_integrity_verified" in commits
    assert "constitution_integrity_verified" in commits
    assert "memory_integrity_verified" in commits
    assert "security_integrity_verified" in commits
    assert "audit_integrity_verified" in commits
    assert "authority_integrity_verified" in commits
    assert "no_forbidden_inheritance" in commits
    assert "no_authority_escalation" in commits
    assert "human_authorization_still_valid" in commits

    # Rollback
    assert "failed_transaction_must_not_commit" in rollback
    assert "partial_birth_must_not_become_active" in rollback
    assert "unverified_identity_must_not_survive" in rollback
    assert "unverified_soul_must_not_survive" in rollback
    assert "unverified_constitution_must_not_survive" in rollback
    assert "unverified_memory_namespace_must_not_survive" in rollback
    assert "unverified_security_identity_must_not_survive" in rollback
    assert "unverified_audit_identity_must_not_survive" in rollback
    assert "unverified_resource_boundary_must_not_survive" in rollback
    assert "unverified_lifecycle_boundary_must_not_survive" in rollback
    assert "rollback_must_be_audited" in rollback
    assert "rollback_must_fail_closed" in rollback

    # Atomicity
    assert constitution.child_birth_transaction_requires_atomic_commit()
    assert constitution.child_birth_transaction_requires_complete_verification()
    assert constitution.child_birth_transaction_all_components_required()

    # Partial or failed birth can never become valid
    assert not constitution.child_birth_transaction_partial_birth_is_valid()
    assert not constitution.child_birth_transaction_failed_birth_can_commit()
    assert not constitution.child_birth_transaction_unknown_state_can_commit()

    # Failure requires rollback
    assert constitution.child_birth_transaction_requires_rollback_on_failure()
    assert constitution.child_birth_transaction_requires_rollback_audit()
    assert constitution.child_birth_transaction_rollback_fails_closed()

    print("SAHIBEX CHILD BIRTH TRANSACTION TEST: PASS")


if __name__ == "__main__":
    main()
