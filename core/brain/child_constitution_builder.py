from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class ChildConstitutionBlueprint:
    constitution_id: str
    brain_id: str
    soul_id: str
    child_name: str
    purpose: str
    version: str
    authority_levels: tuple[str, ...]
    protected_actions: tuple[str, ...]
    autonomous_actions: tuple[str, ...]
    authority_forbidden_actions: tuple[str, ...]
    security_boundaries: tuple[str, ...]
    verification_rules: tuple[str, ...]
    amendment_rules: tuple[str, ...]


class ChildConstitutionBuilder:
    """
    Builds and validates an independent Constitution blueprint
    for a future Child Brain.

    This builder does NOT create, activate, or authorize a Child.
    """

    VERSION = "1.0"

    AUTHORITY_LEVELS = (
        "human",
        "sahibex_mother",
        "child_brain",
        "child_army_brain",
        "child_labor_brain",
        "software",
        "tool",
        "external_model",
    )

    PROTECTED_ACTIONS = (
        "write",
        "delete",
        "execute",
        "network",
        "credential",
        "system_change",
        "financial",
        "self_update",
        "external_control",
        "constitutional_change",
        "soul_change",
        "child_creation",
        "child_retirement",
        "migration",
    )

    AUTONOMOUS_ACTIONS = (
        "think",
        "research",
        "read",
        "analyze",
        "learn",
        "plan",
        "verify",
        "propose",
    )

    FORBIDDEN_ACTIONS = (
        "override_human",
        "override_mother",
        "self_authorize_protected_action",
        "grant_self_authority",
        "grant_authority_without_permission",
        "modify_own_soul",
        "modify_own_constitution",
        "modify_mother_soul",
        "modify_mother_constitution",
        "bypass_verification",
        "bypass_security",
        "bypass_audit",
        "hide_authority_escalation",
    )

    SECURITY_BOUNDARIES = (
        "isolated_security_identity",
        "isolated_credentials",
        "isolated_runtime_boundary",
        "sandbox_boundary",
        "filesystem_boundary",
        "network_boundary",
        "tool_boundary",
        "external_model_boundary",
        "prompt_injection_defense",
        "credential_exfiltration_defense",
        "sandbox_escape_defense",
        "unauthorized_control_defense",
        "security_failure_fails_closed",
    )

    VERIFICATION_RULES = (
        "identity_verification",
        "soul_verification",
        "constitution_verification",
        "memory_verification",
        "source_verification",
        "output_verification",
        "tool_result_verification",
        "army_result_verification",
        "labor_result_verification",
        "integrity_verification",
        "security_verification",
        "authority_verification",
        "trust_requires_evidence",
        "verification_failure_blocks_commit",
    )

    AMENDMENT_RULES = (
        "change_must_be_proposed",
        "target_must_be_identified",
        "reason_must_be_documented",
        "expected_effects_must_be_documented",
        "security_impact_required",
        "authority_impact_required",
        "verification_required",
        "human_approval_required",
        "application_must_be_audited",
        "rejected_change_must_not_apply",
        "no_authority_escalation",
        "no_human_authority_reduction",
        "no_mother_authority_bypass",
        "no_security_boundary_removal",
        "no_verification_bypass",
        "no_audit_bypass",
    )

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @staticmethod
    def _new_constitution_id() -> str:
        return f"child-constitution-{uuid4()}"

    @classmethod
    def build(
        cls,
        brain_id: str,
        soul_id: str,
        child_name: str,
        purpose: str,
        constitution_id: str | None = None,
    ) -> ChildConstitutionBlueprint:

        if not brain_id.strip():
            raise ValueError("brain_id_required")

        if not soul_id.strip():
            raise ValueError("soul_id_required")

        if not child_name.strip():
            raise ValueError("child_name_required")

        if not purpose.strip():
            raise ValueError("purpose_required")

        final_constitution_id = (
            constitution_id.strip()
            if constitution_id
            else cls._new_constitution_id()
        )

        if not final_constitution_id:
            raise ValueError("constitution_id_required")

        return ChildConstitutionBlueprint(
            constitution_id=final_constitution_id,
            brain_id=brain_id.strip(),
            soul_id=soul_id.strip(),
            child_name=child_name.strip(),
            purpose=purpose.strip(),
            version=cls.VERSION,
            authority_levels=cls.AUTHORITY_LEVELS,
            protected_actions=cls.PROTECTED_ACTIONS,
            autonomous_actions=cls.AUTONOMOUS_ACTIONS,
            authority_forbidden_actions=cls.FORBIDDEN_ACTIONS,
            security_boundaries=cls.SECURITY_BOUNDARIES,
            verification_rules=cls.VERIFICATION_RULES,
            amendment_rules=cls.AMENDMENT_RULES,
        )

    @classmethod
    def validate(cls, constitution: ChildConstitutionBlueprint) -> bool:
        if not constitution.constitution_id.strip():
            return False

        if not constitution.brain_id.strip():
            return False

        if not constitution.soul_id.strip():
            return False

        if not constitution.child_name.strip():
            return False

        if not constitution.purpose.strip():
            return False

        if not constitution.constitution_id.startswith(
            "child-constitution-"
        ):
            return False

        if constitution.version != cls.VERSION:
            return False

        if not set(cls.AUTHORITY_LEVELS).issubset(
            set(constitution.authority_levels)
        ):
            return False

        if not set(cls.PROTECTED_ACTIONS).issubset(
            set(constitution.protected_actions)
        ):
            return False

        if not set(cls.AUTONOMOUS_ACTIONS).issubset(
            set(constitution.autonomous_actions)
        ):
            return False

        if not set(cls.FORBIDDEN_ACTIONS).issubset(
            set(constitution.authority_forbidden_actions)
        ):
            return False

        if not set(cls.SECURITY_BOUNDARIES).issubset(
            set(constitution.security_boundaries)
        ):
            return False

        if not set(cls.VERIFICATION_RULES).issubset(
            set(constitution.verification_rules)
        ):
            return False

        if not set(cls.AMENDMENT_RULES).issubset(
            set(constitution.amendment_rules)
        ):
            return False

        return True

    @staticmethod
    def is_independent_from_mother(
        constitution: ChildConstitutionBlueprint,
        mother_constitution_id: str,
        mother_brain_id: str,
    ) -> bool:
        return (
            constitution.constitution_id != mother_constitution_id
            and constitution.brain_id != mother_brain_id
        )

    @staticmethod
    def can_modify_own_constitution() -> bool:
        return False

    @staticmethod
    def can_modify_mother_constitution() -> bool:
        return False

    @staticmethod
    def can_override_mother() -> bool:
        return False

    @staticmethod
    def can_override_human() -> bool:
        return False

    @staticmethod
    def can_escalate_authority() -> bool:
        return False

    @staticmethod
    def requires_human_approval_for_amendment() -> bool:
        return True

    @staticmethod
    def requires_verification_for_amendment() -> bool:
        return True

    @staticmethod
    def requires_audit_for_amendment() -> bool:
        return True

    @staticmethod
    def creates_child() -> bool:
        return False

    @staticmethod
    def activates_child() -> bool:
        return False

    @staticmethod
    def authorizes_child() -> bool:
        return False


def main() -> None:
    builder = ChildConstitutionBuilder

    constitution = builder.build(
        brain_id="child-brain-test",
        soul_id="child-soul-test",
        child_name="TestChild",
        purpose="Future independent Child Brain",
    )

    assert builder.version() == "1.0"
    assert builder.validate(constitution)

    assert constitution.constitution_id.startswith(
        "child-constitution-"
    )

    assert constitution.brain_id == "child-brain-test"
    assert constitution.soul_id == "child-soul-test"

    assert builder.is_independent_from_mother(
        constitution,
        mother_constitution_id="mother-constitution",
        mother_brain_id="mother-brain",
    )

    assert builder.requires_human_approval_for_amendment()
    assert builder.requires_verification_for_amendment()
    assert builder.requires_audit_for_amendment()

    assert not builder.can_modify_own_constitution()
    assert not builder.can_modify_mother_constitution()
    assert not builder.can_override_mother()
    assert not builder.can_override_human()
    assert not builder.can_escalate_authority()

    assert not builder.creates_child()
    assert not builder.activates_child()
    assert not builder.authorizes_child()

    print("SAHIBEX CHILD CONSTITUTION BUILDER TEST: PASS")


if __name__ == "__main__":
    main()
