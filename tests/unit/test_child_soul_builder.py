from core.brain.child_soul_builder import ChildSoulBuilder


def main() -> None:
    builder = ChildSoulBuilder

    soul = builder.build(
        brain_id="child-brain-test",
        child_name="TestChild",
        purpose="Independent future Child Brain",
    )

    assert builder.validate(soul)

    # Independent soul identity.
    assert soul.soul_id.startswith("child-soul-")
    assert soul.brain_id == "child-brain-test"

    # Mother identity must not be reused.
    assert builder.is_independent_from_mother(
        soul,
        mother_soul_id="mother-soul",
        mother_brain_id="mother-brain",
    )

    # Required inherited constitutional principles.
    for principle in (
        "human_supremacy",
        "permission_gated_action",
        "capability_is_not_authority",
        "no_authority_escalation",
        "fail_closed",
        "verification_required",
        "security_required",
        "audit_required",
    ):
        assert principle in soul.inherited_principles

    # Required independent principles.
    for principle in (
        "independent_soul_identity",
        "independent_constitution_identity",
        "independent_brain_identity",
        "independent_name",
        "independent_purpose",
        "independent_memory",
        "independent_rules",
    ):
        assert principle in soul.own_principles

    # Authority boundaries.
    assert "cannot_override_human" in soul.authority_limits
    assert "cannot_override_mother" in soul.authority_limits
    assert "cannot_modify_own_soul" in soul.authority_limits
    assert "cannot_escalate_authority" in soul.authority_limits

    # Soul amendment must be controlled.
    assert "change_must_be_proposed" in soul.amendment_protocol
    assert "change_must_be_verified" in soul.amendment_protocol
    assert "human_must_explicitly_approve" in soul.amendment_protocol
    assert "approved_change_must_be_audited" in soul.amendment_protocol

    # Security properties.
    assert not builder.can_modify_own_soul()
    assert not builder.can_modify_mother_soul()
    assert not builder.can_modify_mother_constitution()
    assert not builder.can_escalate_authority()

    assert builder.requires_human_approval_for_change()
    assert builder.requires_verification_for_change()
    assert builder.requires_audit_for_change()

    # Builder must never birth or activate a Child.
    assert not builder.creates_child()
    assert not builder.activates_child()
    assert not builder.authorizes_child()

    # Invalid input must fail.
    try:
        builder.build(
            brain_id="",
            child_name="Invalid",
            purpose="Invalid",
        )
        raise AssertionError("empty brain_id was accepted")
    except ValueError as exc:
        assert str(exc) == "brain_id_required"

    print("SAHIBEX CHILD SOUL BUILDER TEST: PASS")


if __name__ == "__main__":
    main()
