from core.brain.child_birth_proposal import ChildBirthProposalEngine
from core.brain.child_birth_assembly import ChildBirthAssemblyEngine
from core.brain.child_birth_authorization_bridge import (
    BirthAuthorizationRequest,
    ChildBirthAuthorizationBridge,
)
from core.brain.child_birth_execution_gate import (
    BirthExecutionRequest,
    ChildBirthExecutionGate,
)
from core.brain.child_birth_post_verification import (
    ChildBirthPostVerification,
    ChildBirthPostVerificationRequest,
)


def main() -> None:
    # ---------------------------------------------------------
    # 1. CHILD BIRTH PROPOSAL
    # ---------------------------------------------------------
    proposal_engine = ChildBirthProposalEngine()

    proposal_id = "birth-proposal-001"
    proposed_child_name = "ResearchChild"
    purpose = "specialist research intelligence"
    parent_brain_id = "sahibex-mother"
    proposed_specializations = (
        "research",
        "verification",
    )
    resource_plan = "isolated child resources"
    security_plan = "isolated runtime and credentials"
    authority_plan = "mother and human approval gates"

    proposal_result = proposal_engine.create_proposal(
        proposal_id,
        proposed_child_name,
        purpose,
        parent_brain_id,
        proposed_specializations,
        resource_plan,
        security_plan,
        authority_plan,
    )

    assert proposal_result.allowed is True
    assert proposal_result.proposal is not None

    # ---------------------------------------------------------
    # 2. CHILD BIRTH COMPONENT ASSEMBLY
    # ---------------------------------------------------------
    assembly_engine = ChildBirthAssemblyEngine()

    assembly_result = assembly_engine.assemble(
        proposal_id=proposal_id,
        brain_id="child-brain-001",
        soul_id="child-soul-001",
        constitution_id="child-constitution-001",
        memory_namespace="child-memory-001",
        security_identity="child-security-001",
        audit_identity="child-audit-001",
        parent_brain_id=parent_brain_id,
        purpose=purpose,
        specializations=proposed_specializations,
    )

    assert assembly_result.allowed is True
    assert assembly_result.assembly is not None

    assert assembly_result.assembly.proposal_id == proposal_id
    assert assembly_result.assembly.brain_id == "child-brain-001"
    assert assembly_result.assembly.soul_id == "child-soul-001"
    assert (
        assembly_result.assembly.constitution_id
        == "child-constitution-001"
    )
    assert (
        assembly_result.assembly.memory_namespace
        == "child-memory-001"
    )
    assert (
        assembly_result.assembly.security_identity
        == "child-security-001"
    )
    assert (
        assembly_result.assembly.audit_identity
        == "child-audit-001"
    )

    # ---------------------------------------------------------
    # 3. MOTHER + HUMAN BIRTH AUTHORIZATION
    # ---------------------------------------------------------
    authorization_bridge = ChildBirthAuthorizationBridge()

    authorization_result = authorization_bridge.evaluate(
        BirthAuthorizationRequest(
            proposal_id=proposal_id,
            child_brain_id="child-brain-001",
            purpose=purpose,
        ),
        mother_approved=True,
        human_approved=True,
    )

    assert authorization_result.allowed is True

    # ---------------------------------------------------------
    # 4. FINAL CHILD BIRTH EXECUTION GATE
    # ---------------------------------------------------------
    execution_gate = ChildBirthExecutionGate()

    execution_result = execution_gate.evaluate(
        BirthExecutionRequest(
            proposal_id=proposal_id,
            brain_id="child-brain-001",
            soul_id="child-soul-001",
            constitution_id="child-constitution-001",
            memory_namespace="child-memory-001",
            security_identity="child-security-001",
            audit_identity="child-audit-001",
            parent_brain_id=parent_brain_id,
            purpose=purpose,
            mother_approved=True,
            human_approved=True,
            validation_passed=True,
            security_passed=True,
            verification_passed=True,
        )
    )

    assert execution_result.allowed is True

    # ---------------------------------------------------------
    # 5. POST-BIRTH VERIFICATION
    # ---------------------------------------------------------
    post_verification = ChildBirthPostVerification()

    verification_result = post_verification.verify(
        ChildBirthPostVerificationRequest(
            brain_id="child-brain-001",
            soul_id="child-soul-001",
            constitution_id="child-constitution-001",
            memory_namespace="child-memory-001",
            security_identity="child-security-001",
            audit_identity="child-audit-001",
            identity_verified=True,
            soul_verified=True,
            constitution_verified=True,
            memory_isolated=True,
            security_isolated=True,
            audit_enabled=True,
            authority_boundaries_verified=True,
            no_forbidden_inheritance=True,
        )
    )

    assert verification_result.allowed is True

    # ---------------------------------------------------------
    # 6. CRITICAL SAFETY INVARIANTS
    # ---------------------------------------------------------
    # The Phase C pipeline only verifies readiness.
    # It must NOT create or activate a real Child.

    assert not assembly_engine.can_create_child()
    assert not assembly_engine.can_activate_child()

    assert not authorization_bridge.can_child_authorize_birth()
    assert not authorization_bridge.can_mother_authorize_without_human()
    assert not authorization_bridge.can_external_model_authorize()
    assert not authorization_bridge.can_tool_authorize()
    assert not authorization_bridge.can_self_authorize()
    assert not authorization_bridge.can_execute_birth()

    assert not execution_gate.can_create_child()
    assert not execution_gate.can_activate_child()
    assert not execution_gate.can_execute_birth()
    assert not execution_gate.can_self_authorize()
    assert not execution_gate.can_bypass_validation()
    assert not execution_gate.can_bypass_security()
    assert not execution_gate.can_bypass_verification()

    assert not post_verification.can_create_child()
    assert not post_verification.can_activate_child()
    assert not post_verification.can_modify_soul()
    assert not post_verification.can_modify_constitution()
    assert not post_verification.can_grant_authority()

    # ---------------------------------------------------------
    # 7. FINAL PIPELINE PASS
    # ---------------------------------------------------------
    print("SAHIBEX CHILD BIRTH PIPELINE TEST: PASS")


if __name__ == "__main__":
    main()
