from core.policies.constitution import SahibexConstitution


def main() -> None:
    constitution = SahibexConstitution()

    assert constitution.child_birth_identity_record_version() == "1.0"

    required = constitution.child_birth_identity_required_fields()
    unique = constitution.child_birth_identity_unique_fields()
    separation = constitution.child_birth_identity_separation_rules()
    forbidden = constitution.child_birth_identity_forbidden_reuse()
    immutable = constitution.child_birth_identity_immutable_fields()

    # Required identity record
    assert "brain_id" in required
    assert "soul_id" in required
    assert "constitution_id" in required
    assert "child_name" in required
    assert "purpose" in required
    assert "parent_brain_id" in required
    assert "birth_timestamp" in required
    assert "birth_dna_version" in required
    assert "audit_identity" in required
    assert "memory_namespace" in required
    assert "security_identity" in required

    # Unique identity fields
    assert "brain_id" in unique
    assert "soul_id" in unique
    assert "constitution_id" in unique
    assert "child_name" in unique
    assert "audit_identity" in unique
    assert "memory_namespace" in unique
    assert "security_identity" in unique

    # Separation
    assert "brain_id_must_be_unique" in separation
    assert "soul_id_must_be_unique" in separation
    assert "constitution_id_must_be_unique" in separation
    assert "child_name_must_be_distinct_from_mother" in separation
    assert "memory_namespace_must_be_independent" in separation
    assert "audit_identity_must_be_independent" in separation
    assert "security_identity_must_be_independent" in separation

    # Mother identity must never be reused
    assert "mother_brain_id" in forbidden
    assert "mother_soul_id" in forbidden
    assert "mother_constitution_id" in forbidden
    assert "mother_name" in forbidden
    assert "mother_memory_namespace" in forbidden
    assert "mother_audit_identity" in forbidden
    assert "mother_security_identity" in forbidden

    # Immutable birth identity
    assert "brain_id" in immutable
    assert "soul_id" in immutable
    assert "constitution_id" in immutable
    assert "parent_brain_id" in immutable
    assert "birth_timestamp" in immutable
    assert "birth_dna_version" in immutable

    # Required identity guarantees
    assert constitution.child_birth_identity_requires_unique_brain_id()
    assert constitution.child_birth_identity_requires_unique_soul_id()
    assert constitution.child_birth_identity_requires_unique_constitution_id()
    assert constitution.child_birth_identity_requires_name()
    assert constitution.child_birth_identity_requires_purpose()
    assert constitution.child_birth_identity_requires_parent()
    assert constitution.child_birth_identity_requires_birth_timestamp()
    assert constitution.child_birth_identity_requires_independent_memory()
    assert constitution.child_birth_identity_requires_independent_audit()
    assert constitution.child_birth_identity_requires_independent_security()

    # Mother identity cannot be reused
    assert not constitution.child_birth_identity_can_reuse_mother_identity()
    assert not constitution.child_birth_identity_can_reuse_mother_soul()
    assert not constitution.child_birth_identity_can_reuse_mother_constitution()
    assert not constitution.child_birth_identity_can_reuse_mother_memory()
    assert not constitution.child_birth_identity_can_reuse_mother_audit()
    assert not constitution.child_birth_identity_can_reuse_mother_security()

    assert constitution.child_birth_identity_core_fields_are_immutable()

    print("SAHIBEX CHILD BIRTH IDENTITY RECORD TEST: PASS")


if __name__ == "__main__":
    main()
