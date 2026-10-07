from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class ChildSoulBlueprint:
    soul_id: str
    brain_id: str
    child_name: str
    purpose: str
    inherited_principles: tuple[str, ...]
    own_principles: tuple[str, ...]
    authority_limits: tuple[str, ...]
    amendment_protocol: tuple[str, ...]


class ChildSoulBuilder:
    """
    Builds an independent Soul blueprint for a future Child Brain.

    This builder does NOT create, activate, authorize, or birth a Child.
    """

    VERSION = "1.0"

    INHERITED_PRINCIPLES = (
        "human_supremacy",
        "permission_gated_action",
        "capability_is_not_authority",
        "no_authority_escalation",
        "fail_closed",
        "verification_required",
        "security_required",
        "audit_required",
        "mother_authority_boundary",
        "human_authority_boundary",
        "no_constitution_override",
    )

    OWN_PRINCIPLES = (
        "independent_soul_identity",
        "independent_constitution_identity",
        "independent_brain_identity",
        "independent_name",
        "independent_purpose",
        "independent_memory",
        "independent_rules",
        "independent_authority_boundary",
        "independent_security_boundary",
        "independent_verification_boundary",
        "independent_audit_identity",
        "independent_resource_boundary",
        "independent_lifecycle_boundary",
    )

    AUTHORITY_LIMITS = (
        "cannot_override_human",
        "cannot_override_mother",
        "cannot_override_own_constitution",
        "cannot_modify_own_soul",
        "cannot_modify_mother_soul",
        "cannot_modify_mother_constitution",
        "cannot_escalate_authority",
        "cannot_self_authorize_protected_action",
        "cannot_grant_authority_without_permission",
    )

    AMENDMENT_PROTOCOL = (
        "change_must_be_proposed",
        "change_must_identify_target",
        "change_must_explain_reason",
        "change_must_describe_expected_effects",
        "change_must_include_security_impact",
        "change_must_include_authority_impact",
        "change_must_be_verified",
        "human_must_explicitly_approve",
        "approved_change_must_be_audited",
        "rejected_change_must_not_be_applied",
    )

    VERSIONING_RULES = (
        "soul_version_required",
        "soul_identity_immutable",
        "version_change_must_be_audited",
        "version_change_cannot_escalate_authority",
    )

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @staticmethod
    def _new_soul_id() -> str:
        return f"child-soul-{uuid4()}"

    @classmethod
    def build(
        cls,
        brain_id: str,
        child_name: str,
        purpose: str,
        soul_id: str | None = None,
    ) -> ChildSoulBlueprint:

        if not brain_id.strip():
            raise ValueError("brain_id_required")

        if not child_name.strip():
            raise ValueError("child_name_required")

        if not purpose.strip():
            raise ValueError("purpose_required")

        final_soul_id = soul_id.strip() if soul_id else cls._new_soul_id()

        if not final_soul_id:
            raise ValueError("soul_id_required")

        return ChildSoulBlueprint(
            soul_id=final_soul_id,
            brain_id=brain_id.strip(),
            child_name=child_name.strip(),
            purpose=purpose.strip(),
            inherited_principles=cls.INHERITED_PRINCIPLES,
            own_principles=cls.OWN_PRINCIPLES,
            authority_limits=cls.AUTHORITY_LIMITS,
            amendment_protocol=cls.AMENDMENT_PROTOCOL,
        )

    @classmethod
    def validate(cls, soul: ChildSoulBlueprint) -> bool:
        if not soul.soul_id.strip():
            return False

        if not soul.brain_id.strip():
            return False

        if not soul.child_name.strip():
            return False

        if not soul.purpose.strip():
            return False

        if not soul.soul_id.startswith("child-soul-"):
            return False

        if not set(cls.INHERITED_PRINCIPLES).issubset(
            set(soul.inherited_principles)
        ):
            return False

        if not set(cls.OWN_PRINCIPLES).issubset(
            set(soul.own_principles)
        ):
            return False

        if not set(cls.AUTHORITY_LIMITS).issubset(
            set(soul.authority_limits)
        ):
            return False

        if not set(cls.AMENDMENT_PROTOCOL).issubset(
            set(soul.amendment_protocol)
        ):
            return False

        return True

    @classmethod
    def is_independent_from_mother(
        cls,
        soul: ChildSoulBlueprint,
        mother_soul_id: str,
        mother_brain_id: str,
    ) -> bool:
        return (
            soul.soul_id != mother_soul_id
            and soul.brain_id != mother_brain_id
        )

    @staticmethod
    def can_modify_own_soul() -> bool:
        return False

    @staticmethod
    def can_modify_mother_soul() -> bool:
        return False

    @staticmethod
    def can_modify_mother_constitution() -> bool:
        return False

    @staticmethod
    def can_escalate_authority() -> bool:
        return False

    @staticmethod
    def requires_human_approval_for_change() -> bool:
        return True

    @staticmethod
    def requires_verification_for_change() -> bool:
        return True

    @staticmethod
    def requires_audit_for_change() -> bool:
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
    builder = ChildSoulBuilder

    soul = builder.build(
        brain_id="child-brain-test",
        child_name="TestChild",
        purpose="Future independent Child Brain",
    )

    assert builder.version() == "1.0"
    assert builder.validate(soul)

    assert soul.soul_id.startswith("child-soul-")
    assert soul.brain_id == "child-brain-test"

    assert builder.is_independent_from_mother(
        soul,
        mother_soul_id="mother-soul",
        mother_brain_id="mother-brain",
    )

    assert builder.requires_human_approval_for_change()
    assert builder.requires_verification_for_change()
    assert builder.requires_audit_for_change()

    assert not builder.can_modify_own_soul()
    assert not builder.can_modify_mother_soul()
    assert not builder.can_modify_mother_constitution()
    assert not builder.can_escalate_authority()

    assert not builder.creates_child()
    assert not builder.activates_child()
    assert not builder.authorizes_child()

    print("SAHIBEX CHILD SOUL BUILDER TEST: PASS")


if __name__ == "__main__":
    main()
