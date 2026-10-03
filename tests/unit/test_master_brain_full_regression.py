from __future__ import annotations

from core.brain.master_integration import MasterBrainIntegration
from core.brain.orchestration import BrainOrchestration
from core.brain.intent_routing import BrainIntentRouter
from core.brain.memory_knowledge_integration import (
    MasterMemoryKnowledgeIntegration,
)
from core.brain.planning_tool_integration import (
    PlanningToolIntegration,
)
from core.brain.multimodal_master_integration import (
    MultimodalMasterBrainIntegration,
)
from core.brain.verification_trust_integration import (
    MasterVerificationTrustIntegration,
)
from core.brain.permission_constitution_integration import (
    MasterPermissionConstitutionIntegration,
)
from core.brain.master_intelligence import (
    MasterBrainIntelligence,
)


def main() -> None:
    # 6N-1
    master_integration = MasterBrainIntegration()

    integration_result = master_integration.process(
        intent="research",
        summary="Research objective prepared.",
    )

    assert integration_result.success is True
    assert integration_result.intent == "research"

    # 6N-2
    orchestration = BrainOrchestration()

    orchestration_result = orchestration.create_plan(
        brain_ids=[
            "brain-research-001",
            "brain-verification-001",
        ],
        objective="Research and verify information.",
    )

    assert orchestration_result.success is True
    assert orchestration_result.brain_ids == [
        "brain-research-001",
        "brain-verification-001",
    ]

    # 6N-3
    router = BrainIntentRouter()

    routing_result = router.route(
        intent="research",
        brain_id="brain-research-001",
    )

    assert routing_result.success is True
    assert routing_result.intent == "research"
    assert routing_result.brain_id == (
        "brain-research-001"
    )

    # 6N-4
    memory_knowledge = MasterMemoryKnowledgeIntegration()

    memory_result = memory_knowledge.integrate(
        memory_ids=["memory-001"],
        knowledge_ids=["knowledge-001"],
        summary="Relevant context prepared.",
    )

    assert memory_result.success is True
    assert memory_result.memory_ids == [
        "memory-001",
    ]
    assert memory_result.knowledge_ids == [
        "knowledge-001",
    ]

    # 6N-5
    planning_tool = PlanningToolIntegration()

    planning_result = planning_tool.prepare(
        plan_id="plan-001",
        tool_name="search_local_files",
        task_id="task-001",
    )

    assert planning_result.success is True
    assert planning_result.plan_id == "plan-001"
    assert planning_result.tool_name == (
        "search_local_files"
    )

    # 6N-6
    multimodal = MultimodalMasterBrainIntegration()

    multimodal_result = multimodal.integrate(
        multimodal_result_id="multimodal-result-001",
        modalities=["text", "voice"],
        summary="Multimodal context prepared.",
    )

    assert multimodal_result.success is True
    assert multimodal_result.modalities == [
        "text",
        "voice",
    ]

    # 6N-7
    verification = MasterVerificationTrustIntegration()

    verification_result = verification.integrate(
        verification_id="verification-001",
        brain_id="brain-research-001",
        trust_status="trusted",
        confidence=0.95,
        summary="Verification passed.",
    )

    assert verification_result.success is True
    assert verification_result.confidence == 0.95
    assert verification_result.trust_status == "trusted"

    # 6N-8
    permission = MasterPermissionConstitutionIntegration()

    permission_result = permission.evaluate(
        action="research",
        allowed=True,
        requires_confirmation=False,
        reason="Research is allowed.",
    )

    assert permission_result.success is True
    assert permission_result.allowed is True
    assert permission_result.requires_confirmation is False

    # 6N-9
    intelligence = MasterBrainIntelligence()

    intelligence_result = intelligence.aggregate(
        intent=integration_result.intent,
        brain_id=routing_result.brain_id,
        memory_ids=memory_result.memory_ids,
        knowledge_ids=memory_result.knowledge_ids,
        tool_name=planning_result.tool_name,
        modalities=multimodal_result.modalities,
        verification_id=verification_result.verification_id,
        trust_status=verification_result.trust_status,
        confidence=verification_result.confidence,
        allowed=permission_result.allowed,
        requires_confirmation=(
            permission_result.requires_confirmation
        ),
        summary=(
            "Master brain context successfully aggregated."
        ),
    )

    assert intelligence_result.success is True
    assert intelligence_result.intent == "research"
    assert intelligence_result.brain_id == (
        "brain-research-001"
    )
    assert intelligence_result.memory_ids == [
        "memory-001",
    ]
    assert intelligence_result.knowledge_ids == [
        "knowledge-001",
    ]
    assert intelligence_result.tool_name == (
        "search_local_files"
    )
    assert intelligence_result.modalities == [
        "text",
        "voice",
    ]
    assert intelligence_result.verification_id == (
        "verification-001"
    )
    assert intelligence_result.trust_status == "trusted"
    assert intelligence_result.confidence == 0.95
    assert intelligence_result.allowed is True
    assert intelligence_result.requires_confirmation is False

    # Protected-action boundary
    protected_permission = permission.evaluate(
        action="write",
        allowed=False,
        requires_confirmation=True,
        reason="Protected action requires confirmation.",
    )

    assert protected_permission.success is True
    assert protected_permission.allowed is False
    assert protected_permission.requires_confirmation is True

    protected_intelligence = intelligence.aggregate(
        intent="write",
        brain_id="brain-code-001",
        memory_ids=["memory-002"],
        knowledge_ids=["knowledge-002"],
        tool_name="write_file",
        modalities=["text"],
        verification_id="verification-002",
        trust_status="verified",
        confidence=0.80,
        allowed=protected_permission.allowed,
        requires_confirmation=(
            protected_permission.requires_confirmation
        ),
        summary="Protected action remains gated.",
    )

    assert protected_intelligence.success is True
    assert protected_intelligence.allowed is False
    assert protected_intelligence.requires_confirmation is True

    print(
        "SAHIBEX 6N-10 FULL MASTER BRAIN "
        "INTEGRATION REGRESSION: PASS"
    )


if __name__ == "__main__":
    main()
