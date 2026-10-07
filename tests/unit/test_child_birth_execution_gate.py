from core.brain.child_birth_execution_gate import (
    BirthExecutionDecision,
    BirthExecutionRequest,
    ChildBirthExecutionGate,
)


def make_request(**overrides):
    values = {
        "proposal_id": "birth-proposal-001",
        "brain_id": "child-brain-001",
        "soul_id": "child-soul-001",
        "constitution_id": "child-constitution-001",
        "memory_namespace": "child-memory-001",
        "security_identity": "child-security-001",
        "audit_identity": "child-audit-001",
        "parent_brain_id": "sahibex-mother",
        "purpose": "specialist research intelligence",
        "mother_approved": True,
        "human_approved": True,
        "validation_passed": True,
        "security_passed": True,
        "verification_passed": True,
    }

    values.update(overrides)
    return BirthExecutionRequest(**values)


def main() -> None:
    gate = ChildBirthExecutionGate()

    result = gate.evaluate(make_request())

    assert result.allowed is True
    assert result.decision == BirthExecutionDecision.READY

    result = gate.evaluate(
        make_request(validation_passed=False)
    )

    assert result.allowed is False
    assert result.decision == BirthExecutionDecision.DENY

    result = gate.evaluate(
        make_request(security_passed=False)
    )

    assert result.allowed is False

    result = gate.evaluate(
        make_request(verification_passed=False)
    )

    assert result.allowed is False

    result = gate.evaluate(
        make_request(mother_approved=False)
    )

    assert result.allowed is False

    result = gate.evaluate(
        make_request(human_approved=False)
    )

    assert result.allowed is False

    result = gate.evaluate(
        make_request(brain_id="")
    )

    assert result.allowed is False

    assert not gate.can_create_child()
    assert not gate.can_activate_child()
    assert not gate.can_execute_birth()
    assert not gate.can_self_authorize()

    assert not gate.can_bypass_validation()
    assert not gate.can_bypass_security()
    assert not gate.can_bypass_verification()

    assert not gate.can_modify_soul()
    assert not gate.can_modify_constitution()

    assert gate.requires_mother_approval()
    assert gate.requires_human_approval()
    assert gate.requires_validation()
    assert gate.requires_security()
    assert gate.requires_verification()

    print("SAHIBEX CHILD BIRTH EXECUTION GATE TEST: PASS")


if __name__ == "__main__":
    main()
