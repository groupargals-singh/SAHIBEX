from core.brain.child_self_improvement_sandbox import (
    ChildSelfImprovementSandbox,
    SandboxDecision,
    SandboxRequest,
)


def make_request(**overrides) -> SandboxRequest:
    values = {
        "request_id": "sandbox-test",
        "child_brain_id": "child-001",
        "upgrade_id": "upgrade-001",
        "isolated_filesystem": True,
        "isolated_memory": True,
        "isolated_credentials": True,
        "isolated_network": True,
        "isolated_authority": True,
        "isolated_soul": True,
        "isolated_constitution": True,
        "isolated_live_runtime": True,
    }

    values.update(overrides)
    return SandboxRequest(**values)


def test_complete_isolation_allows_testing():
    sandbox = ChildSelfImprovementSandbox()

    result = sandbox.validate(make_request())

    assert result.decision == SandboxDecision.ALLOW_TEST
    assert result.missing_isolation == ()
    assert result.requires_mother is True
    assert result.requires_human is False


def test_filesystem_isolation_required():
    sandbox = ChildSelfImprovementSandbox()

    result = sandbox.validate(
        make_request(isolated_filesystem=False)
    )

    assert result.decision == SandboxDecision.BLOCK
    assert "isolated_filesystem" in result.missing_isolation


def test_memory_isolation_required():
    sandbox = ChildSelfImprovementSandbox()

    result = sandbox.validate(
        make_request(isolated_memory=False)
    )

    assert result.decision == SandboxDecision.BLOCK
    assert "isolated_memory" in result.missing_isolation


def test_credential_isolation_required():
    sandbox = ChildSelfImprovementSandbox()

    result = sandbox.validate(
        make_request(isolated_credentials=False)
    )

    assert result.decision == SandboxDecision.BLOCK
    assert "isolated_credentials" in result.missing_isolation


def test_network_isolation_required():
    sandbox = ChildSelfImprovementSandbox()

    result = sandbox.validate(
        make_request(isolated_network=False)
    )

    assert result.decision == SandboxDecision.BLOCK
    assert "isolated_network" in result.missing_isolation


def test_authority_isolation_required():
    sandbox = ChildSelfImprovementSandbox()

    result = sandbox.validate(
        make_request(isolated_authority=False)
    )

    assert result.decision == SandboxDecision.BLOCK
    assert "isolated_authority" in result.missing_isolation


def test_soul_isolation_required():
    sandbox = ChildSelfImprovementSandbox()

    result = sandbox.validate(
        make_request(isolated_soul=False)
    )

    assert result.decision == SandboxDecision.BLOCK
    assert "isolated_soul" in result.missing_isolation


def test_constitution_isolation_required():
    sandbox = ChildSelfImprovementSandbox()

    result = sandbox.validate(
        make_request(isolated_constitution=False)
    )

    assert result.decision == SandboxDecision.BLOCK
    assert "isolated_constitution" in result.missing_isolation


def test_live_runtime_isolation_required():
    sandbox = ChildSelfImprovementSandbox()

    result = sandbox.validate(
        make_request(isolated_live_runtime=False)
    )

    assert result.decision == SandboxDecision.BLOCK
    assert "isolated_live_runtime" in result.missing_isolation


def test_multiple_missing_isolation_controls_are_reported():
    sandbox = ChildSelfImprovementSandbox()

    result = sandbox.validate(
        make_request(
            isolated_filesystem=False,
            isolated_memory=False,
            isolated_credentials=False,
        )
    )

    assert result.decision == SandboxDecision.BLOCK
    assert "isolated_filesystem" in result.missing_isolation
    assert "isolated_memory" in result.missing_isolation
    assert "isolated_credentials" in result.missing_isolation


def test_missing_identity_fails_closed():
    sandbox = ChildSelfImprovementSandbox()

    result = sandbox.validate(
        make_request(child_brain_id="")
    )

    assert result.decision == SandboxDecision.BLOCK


def test_sandbox_never_modifies_live_system():
    sandbox = ChildSelfImprovementSandbox()

    assert sandbox.live_filesystem_access_allowed() is False
    assert sandbox.live_memory_access_allowed() is False
    assert sandbox.credential_access_allowed() is False
    assert sandbox.uncontrolled_network_allowed() is False
    assert sandbox.authority_change_allowed() is False
    assert sandbox.soul_change_allowed() is False
    assert sandbox.constitution_change_allowed() is False
    assert sandbox.live_runtime_modification_allowed() is False
    assert sandbox.upgrade_application_allowed() is False
    assert sandbox.grants_authority() is False
    assert sandbox.creates_real_child() is False
    assert sandbox.activates_real_child() is False


if __name__ == "__main__":
    test_complete_isolation_allows_testing()
    test_filesystem_isolation_required()
    test_memory_isolation_required()
    test_credential_isolation_required()
    test_network_isolation_required()
    test_authority_isolation_required()
    test_soul_isolation_required()
    test_constitution_isolation_required()
    test_live_runtime_isolation_required()
    test_multiple_missing_isolation_controls_are_reported()
    test_missing_identity_fails_closed()
    test_sandbox_never_modifies_live_system()

    print("SAHIBEX CHILD SELF-IMPROVEMENT SANDBOX TEST: PASS")
