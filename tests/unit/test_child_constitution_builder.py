from core.brain.child_constitution_builder import ChildConstitutionBuilder


def main() -> None:
    builder = ChildConstitutionBuilder

    constitution = builder.build(
        brain_id="child-brain-test",
        soul_id="child-soul-test",
        child_name="TestChild",
        purpose="Independent future Child Brain",
    )

    assert builder.validate(constitution)

    # Independent constitutional identity.
    assert constitution.constitution_id.startswith(
        "child-constitution-"
    )
    assert constitution.brain_id == "child-brain-test"
    assert constitution.soul_id == "child-soul-test"

    # Mother identity must not be reused.
    assert builder.is_independent_from_mother(
        constitution,
        mother_constitution_id="mother-constitution",
        mother_brain_id="mother-brain",
    )

    # Autonomous cognitive actions.
    for action in (
        "think",
        "research",
        "read",
        "analyze",
        "learn",
        "plan",
        "verify",
        "propose",
    ):
        assert action in constitution.autonomous_actions

    # Protected actions.
    for action in (
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
    ):
        assert action in constitution.protected_actions

    # Authority restrictions.
    for action in (
        "override_human",
        "override_mother",
        "self_authorize_protected_action",
        "modify_own_soul",
        "modify_own_constitution",
        "modify_mother_soul",
        "modify_mother_constitution",
        "bypass_verification",
        "bypass_security",
        "bypass_audit",
    ):
        assert action in constitution.authority_forbidden_actions

    # Security boundaries.
    for boundary in (
        "isolated_security_identity",
        "isolated_credentials",
        "isolated_runtime_boundary",
        "sandbox_boundary",
        "filesystem_boundary",
        "network_boundary",
        "tool_boundary",
        "external_model_boundary",
        "prompt_injection_defense",
        "sandbox_escape_defense",
    ):
        assert boundary in constitution.security_boundaries

    # Verification.
    assert "identity_verification" in constitution.verification_rules
    assert "soul_verification" in constitution.verification_rules
    assert "constitution_verification" in constitution.verification_rules
    assert "security_verification" in constitution.verification_rules
    assert "authority_verification" in constitution.verification_rules
    assert "verification_failure_blocks_commit" in constitution.verification_rules

    # Amendment control.
    assert "change_must_be_proposed" in constitution.amendment_rules
    assert "security_impact_required" in constitution.amendment_rules
    assert "authority_impact_required" in constitution.amendment_rules
    assert "human_approval_required" in constitution.amendment_rules
    assert "application_must_be_audited" in constitution.amendment_rules
    assert "rejected_change_must_not_apply" in constitution.amendment_rules
    assert "no_authority_escalation" in constitution.amendment_rules

    # Constitutional authority boundaries.
    assert not builder.can_modify_own_constitution()
    assert not builder.can_modify_mother_constitution()
    assert not builder.can_override_mother()
    assert not builder.can_override_human()
    assert not builder.can_escalate_authority()

    assert builder.requires_human_approval_for_amendment()
    assert builder.requires_verification_for_amendment()
    assert builder.requires_audit_for_amendment()

    # Builder must never create or activate a Child.
    assert not builder.creates_child()
    assert not builder.activates_child()
    assert not builder.authorizes_child()

    # Invalid input must fail.
    try:
        builder.build(
            brain_id="",
            soul_id="child-soul-test",
            child_name="Invalid",
            purpose="Invalid",
        )
        raise AssertionError("empty brain_id was accepted")
    except ValueError as exc:
        assert str(exc) == "brain_id_required"

    print("SAHIBEX CHILD CONSTITUTION BUILDER TEST: PASS")


if __name__ == "__main__":
    main()
