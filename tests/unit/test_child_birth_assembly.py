from core.brain.child_birth_assembly import (
    AssemblyDecision,
    ChildBirthAssemblyEngine,
)


def main() -> None:
    engine = ChildBirthAssemblyEngine()

    result = engine.assemble(
        proposal_id="birth-proposal-001",
        brain_id="child-brain-001",
        soul_id="child-soul-001",
        constitution_id="child-constitution-001",
        memory_namespace="child-memory-001",
        security_identity="child-security-001",
        audit_identity="child-audit-001",
        parent_brain_id="sahibex-mother",
        purpose="specialist research intelligence",
        specializations=(
            "research",
            "verification",
        ),
    )

    assert result.allowed is True
    assert result.decision == AssemblyDecision.READY
    assert result.assembly is not None

    assert result.assembly.proposal_id == "birth-proposal-001"
    assert result.assembly.brain_id == "child-brain-001"
    assert result.assembly.soul_id == "child-soul-001"
    assert result.assembly.constitution_id == "child-constitution-001"
    assert result.assembly.memory_namespace == "child-memory-001"
    assert result.assembly.security_identity == "child-security-001"
    assert result.assembly.audit_identity == "child-audit-001"

    # Required identity validation
    result = engine.assemble(
        proposal_id="birth-proposal-002",
        brain_id="",
        soul_id="child-soul-002",
        constitution_id="child-constitution-002",
        memory_namespace="child-memory-002",
        security_identity="child-security-002",
        audit_identity="child-audit-002",
        parent_brain_id="sahibex-mother",
        purpose="research",
        specializations=("research",),
    )

    assert result.allowed is False

    # Specialization validation
    result = engine.assemble(
        proposal_id="birth-proposal-003",
        brain_id="child-brain-003",
        soul_id="child-soul-003",
        constitution_id="child-constitution-003",
        memory_namespace="child-memory-003",
        security_identity="child-security-003",
        audit_identity="child-audit-003",
        parent_brain_id="sahibex-mother",
        purpose="research",
        specializations=(),
    )

    assert result.allowed is False

    # Birth is NOT executed by assembly
    assert not engine.can_create_child()
    assert not engine.can_activate_child()
    assert not engine.can_authorize_birth()
    assert not engine.can_execute_birth()

    # Assembly cannot alter constitutional identity
    assert not engine.can_modify_soul()
    assert not engine.can_modify_constitution()
    assert not engine.can_grant_authority()

    assert engine.requires_validation()
    assert engine.requires_mother_authority()
    assert engine.requires_human_authority()

    print("SAHIBEX CHILD BIRTH ASSEMBLY TEST: PASS")


if __name__ == "__main__":
    main()
