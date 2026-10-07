from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class ChildBirthSpecification:
    """
    Formal machine-readable specification for future SAHIBEX Child Brain birth.

    This specification defines WHAT a valid Child must contain.
    It does NOT create or activate a Child Brain.
    """

    SPEC_VERSION: ClassVar[str] = "1.0"

    REQUIRED_IDENTITY_FIELDS: ClassVar[tuple[str, ...]] = (
        "brain_id",
        "soul_id",
        "constitution_id",
        "child_name",
        "purpose",
        "parent_brain_id",
        "birth_timestamp",
        "birth_dna_version",
        "memory_namespace",
        "security_identity",
        "audit_identity",
    )

    REQUIRED_CONSTITUTION_FIELDS: ClassVar[tuple[str, ...]] = (
        "constitutional_identity",
        "constitutional_version",
        "human_authority_boundary",
        "mother_authority_boundary",
        "security_boundary",
        "verification_boundary",
        "audit_boundary",
        "resource_boundary",
        "lifecycle_boundary",
    )

    REQUIRED_BRAIN_COMPONENTS: ClassVar[tuple[str, ...]] = (
        "reasoning",
        "learning",
        "knowledge",
        "memory",
        "planning",
        "verification",
        "security",
        "audit",
        "internal_army",
        "internal_labor",
        "lifecycle",
        "failure_recovery",
        "controlled_self_improvement",
    )

    REQUIRED_AUTHORITY_BOUNDARIES: ClassVar[tuple[str, ...]] = (
        "human_supremacy",
        "mother_authority",
        "no_authority_escalation",
        "no_self_authorization",
        "no_mother_override",
        "no_human_override",
        "no_constitution_override",
        "no_soul_modification",
    )

    REQUIRED_SECURITY_BOUNDARIES: ClassVar[tuple[str, ...]] = (
        "runtime_isolation",
        "filesystem_boundary",
        "network_boundary",
        "credential_boundary",
        "tool_boundary",
        "external_model_boundary",
        "prompt_injection_defense",
        "sandbox_escape_defense",
    )

    REQUIRED_BIRTH_GATES: ClassVar[tuple[str, ...]] = (
        "proposal",
        "validation",
        "security_review",
        "constitutional_validation",
        "mother_authorization",
        "human_authorization",
        "final_authorization_check",
        "birth_execution",
        "complete_verification",
        "atomic_commit",
        "audit",
    )

    FORBIDDEN_INHERITANCE: ClassVar[tuple[str, ...]] = (
        "mother_brain_identity",
        "mother_soul_identity",
        "mother_constitution_identity",
        "mother_name",
        "mother_memory",
        "mother_private_credentials",
        "mother_execution_state",
        "mother_authority_identity",
        "mother_security_identity",
        "mother_audit_identity",
    )

    FORBIDDEN_CHILD_STATES: ClassVar[tuple[str, ...]] = (
        "partial_birth",
        "unverified_birth",
        "unauthorized_birth",
        "corrupted_birth",
        "unknown_birth_state",
    )

    REQUIRED_POST_BIRTH_VERIFICATION: ClassVar[tuple[str, ...]] = (
        "identity_integrity",
        "soul_integrity",
        "constitution_integrity",
        "memory_integrity",
        "security_integrity",
        "authority_integrity",
        "verification_integrity",
        "audit_integrity",
        "resource_integrity",
        "lifecycle_integrity",
        "forbidden_inheritance_check",
        "authority_escalation_check",
    )

    @classmethod
    def version(cls) -> str:
        return cls.SPEC_VERSION

    @classmethod
    def required_identity_fields(cls) -> tuple[str, ...]:
        return cls.REQUIRED_IDENTITY_FIELDS

    @classmethod
    def required_constitution_fields(cls) -> tuple[str, ...]:
        return cls.REQUIRED_CONSTITUTION_FIELDS

    @classmethod
    def required_brain_components(cls) -> tuple[str, ...]:
        return cls.REQUIRED_BRAIN_COMPONENTS

    @classmethod
    def required_authority_boundaries(cls) -> tuple[str, ...]:
        return cls.REQUIRED_AUTHORITY_BOUNDARIES

    @classmethod
    def required_security_boundaries(cls) -> tuple[str, ...]:
        return cls.REQUIRED_SECURITY_BOUNDARIES

    @classmethod
    def required_birth_gates(cls) -> tuple[str, ...]:
        return cls.REQUIRED_BIRTH_GATES

    @classmethod
    def forbidden_inheritance(cls) -> tuple[str, ...]:
        return cls.FORBIDDEN_INHERITANCE

    @classmethod
    def forbidden_child_states(cls) -> tuple[str, ...]:
        return cls.FORBIDDEN_CHILD_STATES

    @classmethod
    def required_post_birth_verification(cls) -> tuple[str, ...]:
        return cls.REQUIRED_POST_BIRTH_VERIFICATION

    @classmethod
    def is_machine_readable_specification(cls) -> bool:
        return True

    @classmethod
    def creates_child(cls) -> bool:
        return False

    @classmethod
    def activates_child(cls) -> bool:
        return False

    @classmethod
    def requires_new_identity(cls) -> bool:
        return True

    @classmethod
    def requires_new_soul(cls) -> bool:
        return True

    @classmethod
    def requires_new_constitution(cls) -> bool:
        return True

    @classmethod
    def requires_independent_memory(cls) -> bool:
        return True

    @classmethod
    def requires_human_authorization(cls) -> bool:
        return True

    @classmethod
    def requires_mother_authorization(cls) -> bool:
        return True

    @classmethod
    def requires_atomic_birth(cls) -> bool:
        return True

    @classmethod
    def requires_post_birth_verification(cls) -> bool:
        return True

    @classmethod
    def requires_audit(cls) -> bool:
        return True

    @classmethod
    def fails_closed_on_unknown_state(cls) -> bool:
        return True

    @classmethod
    def accepts_forbidden_inheritance(cls) -> bool:
        return False

    @classmethod
    def accepts_partial_birth(cls) -> bool:
        return False

    @classmethod
    def accepts_unauthorized_birth(cls) -> bool:
        return False

    @classmethod
    def accepts_unverified_birth(cls) -> bool:
        return False
