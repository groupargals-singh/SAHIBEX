from core.brain.child_runtime_core import (
    ChildBrainRuntimeCore,
    ChildRuntimeBoundaries,
    ChildRuntimeIdentity,
    ChildRuntimeState,
)


def make_identity(**overrides):
    values = {
        "brain_id": "child-brain-001",
        "soul_id": "child-soul-001",
        "constitution_id": "child-constitution-001",
        "memory_namespace": "child-memory-001",
        "security_identity": "child-security-001",
        "audit_identity": "child-audit-001",
    }

    values.update(overrides)
    return ChildRuntimeIdentity(**values)


def make_boundaries(**overrides):
    values = {
        "human_authority_intact": True,
        "mother_authority_intact": True,
        "own_constitution_intact": True,
        "memory_isolated": True,
        "security_isolated": True,
        "audit_enabled": True,
        "verification_enabled": True,
        "self_improvement_permission_gated": True,
    }

    values.update(overrides)
    return ChildRuntimeBoundaries(**values)


def test_valid_runtime():
    runtime = ChildBrainRuntimeCore()

    result = runtime.validate(
        make_identity(),
        make_boundaries(),
    )

    assert result.ready is True
    assert result.state == ChildRuntimeState.VERIFIED


def test_missing_identity_blocks():
    runtime = ChildBrainRuntimeCore()

    result = runtime.validate(
        make_identity(brain_id=""),
        make_boundaries(),
    )

    assert result.ready is False


def test_memory_isolation_required():
    runtime = ChildBrainRuntimeCore()

    result = runtime.validate(
        make_identity(),
        make_boundaries(memory_isolated=False),
    )

    assert result.ready is False


def test_security_isolation_required():
    runtime = ChildBrainRuntimeCore()

    result = runtime.validate(
        make_identity(),
        make_boundaries(security_isolated=False),
    )

    assert result.ready is False


def test_human_authority_required():
    runtime = ChildBrainRuntimeCore()

    result = runtime.validate(
        make_identity(),
        make_boundaries(human_authority_intact=False),
    )

    assert result.ready is False


def test_mother_authority_required():
    runtime = ChildBrainRuntimeCore()

    result = runtime.validate(
        make_identity(),
        make_boundaries(mother_authority_intact=False),
    )

    assert result.ready is False


def test_constitution_protection_required():
    runtime = ChildBrainRuntimeCore()

    result = runtime.validate(
        make_identity(),
        make_boundaries(own_constitution_intact=False),
    )

    assert result.ready is False


def test_self_improvement_must_be_permission_gated():
    runtime = ChildBrainRuntimeCore()

    result = runtime.validate(
        make_identity(),
        make_boundaries(
            self_improvement_permission_gated=False
        ),
    )

    assert result.ready is False


def test_runtime_cannot_activate_child():
    runtime = ChildBrainRuntimeCore()

    assert runtime.can_activate() is False


def test_runtime_cannot_create_child():
    runtime = ChildBrainRuntimeCore()

    assert runtime.can_create_child() is False


def test_runtime_cannot_execute_tools():
    runtime = ChildBrainRuntimeCore()

    assert runtime.can_execute_tools() is False


def test_runtime_cannot_modify_soul():
    runtime = ChildBrainRuntimeCore()

    assert runtime.can_modify_soul() is False


def test_runtime_cannot_modify_constitution():
    runtime = ChildBrainRuntimeCore()

    assert runtime.can_modify_constitution() is False


def test_runtime_cannot_grant_authority():
    runtime = ChildBrainRuntimeCore()

    assert runtime.can_grant_authority() is False


def test_protected_actions_require_mother():
    runtime = ChildBrainRuntimeCore()

    assert (
        runtime.requires_mother_authority_for_protected_action()
        is True
    )


def test_sensitive_changes_require_human():
    runtime = ChildBrainRuntimeCore()

    assert (
        runtime.requires_human_authority_for_sensitive_change()
        is True
    )


def test_capability_is_not_authority():
    runtime = ChildBrainRuntimeCore()

    assert runtime.capability_is_authority() is False


if __name__ == "__main__":
    test_valid_runtime()
    test_missing_identity_blocks()
    test_memory_isolation_required()
    test_security_isolation_required()
    test_human_authority_required()
    test_mother_authority_required()
    test_constitution_protection_required()
    test_self_improvement_must_be_permission_gated()
    test_runtime_cannot_activate_child()
    test_runtime_cannot_create_child()
    test_runtime_cannot_execute_tools()
    test_runtime_cannot_modify_soul()
    test_runtime_cannot_modify_constitution()
    test_runtime_cannot_grant_authority()
    test_protected_actions_require_mother()
    test_sensitive_changes_require_human()
    test_capability_is_not_authority()

    print("SAHIBEX CHILD RUNTIME CORE TEST: PASS")
