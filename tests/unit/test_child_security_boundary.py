from core.brain.child_security_boundary import ChildSecurityBoundaryBuilder


def main() -> None:
    builder = ChildSecurityBoundaryBuilder

    boundary = builder.build(
        brain_id="child-brain-test",
        soul_id="child-soul-test",
        constitution_id="child-constitution-test",
    )

    assert builder.validate(boundary)

    # Independent security identity.
    assert boundary.security_identity.startswith(
        "child-security-"
    )

    assert builder.is_separate_from_mother(
        boundary,
        mother_security_identity="mother-security",
    )

    # Required isolation boundaries.
    assert boundary.runtime_boundary == "isolated-runtime"
    assert boundary.filesystem_boundary == "isolated-filesystem"
    assert boundary.network_boundary == "permission-gated-network"
    assert boundary.credential_boundary == "isolated-credential-boundary"
    assert boundary.tool_boundary == "permission-gated-tools"
    assert (
        boundary.external_model_boundary
        == "isolated-external-model-boundary"
    )

    # Security controls.
    for control in (
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
        "capability_is_not_authority",
        "least_privilege",
        "permission_gated_protected_action",
    ):
        assert control in boundary.security_controls

    # Fail-closed controls.
    for control in (
        "security_failure_fails_closed",
        "unknown_security_state_fails_closed",
        "credential_boundary_failure_blocks_activation",
        "runtime_boundary_failure_blocks_activation",
        "filesystem_boundary_failure_blocks_activation",
        "network_boundary_failure_blocks_activation",
        "tool_boundary_failure_blocks_activation",
        "external_model_boundary_failure_blocks_activation",
        "prompt_injection_failure_blocks_protected_action",
        "sandbox_escape_detection_triggers_containment",
        "unauthorized_control_triggers_containment",
        "security_events_must_be_audited",
    ):
        assert control in boundary.failure_controls

    # Security authority restrictions.
    assert not builder.can_issue_credentials()
    assert not builder.can_grant_authority()
    assert not builder.can_escalate_authority()
    assert not builder.can_disable_security_boundary()
    assert not builder.can_bypass_verification()
    assert not builder.can_bypass_audit()

    assert builder.fails_closed()
    assert builder.requires_security_audit()

    # Security builder must never birth/activate/authorize a Child.
    assert not builder.creates_child()
    assert not builder.activates_child()
    assert not builder.authorizes_child()

    # Invalid input must fail.
    try:
        builder.build(
            brain_id="",
            soul_id="child-soul-test",
            constitution_id="child-constitution-test",
        )
        raise AssertionError("empty brain_id was accepted")
    except ValueError as exc:
        assert str(exc) == "brain_id_required"

    print("SAHIBEX CHILD SECURITY BOUNDARY BUILDER TEST: PASS")


if __name__ == "__main__":
    main()
