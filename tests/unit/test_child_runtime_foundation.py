from core.brain.child_brain_core import (
    ChildBrainCore,
    ChildCognitiveAction,
)
from core.brain.child_communication_runtime import (
    ChildCommunicationMessage,
    ChildCommunicationRuntime,
    ChildMessageType,
)
from core.brain.child_knowledge_runtime import (
    ChildKnowledgeRuntime,
)
from core.brain.child_memory_runtime import (
    ChildMemoryRuntime,
)
from core.brain.child_runtime_state import (
    ChildRuntimeState,
    ChildRuntimeStateManager,
)


def main() -> None:
    # ---------------------------------------------------------
    # 1. Runtime State
    # ---------------------------------------------------------
    state_manager = ChildRuntimeStateManager()

    result = state_manager.transition(
        ChildRuntimeState.PROPOSED,
        ChildRuntimeState.BIRTH_AUTHORIZED,
        authority_approved=True,
        verification_passed=True,
    )
    assert result.allowed is True

    result = state_manager.transition(
        ChildRuntimeState.BIRTH_AUTHORIZED,
        ChildRuntimeState.CREATED,
        authority_approved=True,
        verification_passed=True,
    )
    assert result.allowed is True

    result = state_manager.transition(
        ChildRuntimeState.CREATED,
        ChildRuntimeState.VERIFIED,
        authority_approved=True,
        verification_passed=True,
    )
    assert result.allowed is True

    result = state_manager.transition(
        ChildRuntimeState.VERIFIED,
        ChildRuntimeState.READY,
        authority_approved=True,
        verification_passed=True,
    )
    assert result.allowed is True

    # ---------------------------------------------------------
    # 2. Child Brain Core
    # ---------------------------------------------------------
    brain = ChildBrainCore()

    result = brain.evaluate(ChildCognitiveAction.THINK)
    assert result.allowed is True

    result = brain.evaluate(ChildCognitiveAction.RESEARCH)
    assert result.allowed is True

    result = brain.evaluate(ChildCognitiveAction.PLAN)
    assert result.allowed is True

    result = brain.evaluate(
        ChildCognitiveAction.EXECUTE,
        mother_approved=False,
    )
    assert result.allowed is False

    result = brain.evaluate(
        ChildCognitiveAction.EXECUTE,
        mother_approved=True,
    )
    assert result.allowed is True

    assert not brain.can_self_authorize()
    assert not brain.can_override_mother()
    assert not brain.can_override_human()
    assert not brain.executes_actions()

    # ---------------------------------------------------------
    # 3. Child Memory Runtime
    # ---------------------------------------------------------
    memory = ChildMemoryRuntime(
        child_brain_id="child-brain-integration-test",
        memory_namespace="child-memory-integration-test",
    )

    result = memory.write(
        "runtime_status",
        "ready",
    )
    assert result.allowed is True
    assert memory.read("runtime_status") == "ready"

    result = memory.delete(
        "runtime_status",
        authority_approved=False,
    )
    assert result.allowed is False

    result = memory.delete(
        "runtime_status",
        authority_approved=True,
    )
    assert result.allowed is True

    assert memory.memory_is_child_isolated()
    assert memory.credentials_are_separate()
    assert not memory.can_access_mother_private_memory()

    # ---------------------------------------------------------
    # 4. Child Knowledge Runtime
    # ---------------------------------------------------------
    knowledge = ChildKnowledgeRuntime(
        child_brain_id="child-brain-integration-test",
        knowledge_namespace="child-knowledge-integration-test",
    )

    result = knowledge.evaluate(
        operation=knowledge.__class__.__dict__["evaluate"]
        and __import__(
            "core.brain.child_knowledge_runtime",
            fromlist=["KnowledgeOperation"],
        ).KnowledgeOperation.RESEARCH
    )
    assert result.allowed is True

    result = knowledge.store(
        key="test_fact",
        value="verified information",
        source="verified-test-source",
        verified=True,
    )
    assert result.allowed is True

    assert knowledge.read("test_fact") == "verified information"

    result = knowledge.mark_trusted(
        "test_fact",
        authority_approved=False,
    )
    assert result.allowed is False

    result = knowledge.mark_trusted(
        "test_fact",
        authority_approved=True,
    )
    assert result.allowed is True
    assert knowledge.is_trusted("test_fact")

    assert knowledge.can_research_independently()
    assert knowledge.can_learn_independently()
    assert knowledge.can_verify_independently()
    assert not knowledge.external_model_is_authority()

    # ---------------------------------------------------------
    # 5. Mother ↔ Child Communication
    # ---------------------------------------------------------
    communication = ChildCommunicationRuntime()

    message = ChildCommunicationMessage(
        message_id="integration-msg-001",
        child_brain_id="child-brain-integration-test",
        sender="child",
        message_type=ChildMessageType.THOUGHT,
        content="Child runtime is ready.",
    )

    result = communication.evaluate(message)
    assert result.accepted is True

    protected_message = ChildCommunicationMessage(
        message_id="integration-msg-002",
        child_brain_id="child-brain-integration-test",
        sender="child",
        message_type=ChildMessageType.PROTECTED_REQUEST,
        content="Request protected operation.",
    )

    result = communication.evaluate(
        protected_message,
        mother_approved=False,
    )
    assert result.accepted is False

    result = communication.evaluate(
        protected_message,
        mother_approved=True,
    )
    assert result.accepted is True

    assert not communication.information_is_authority()
    assert not communication.external_message_can_grant_authority()
    assert not communication.can_bypass_mother()
    assert not communication.can_bypass_human()

    # ---------------------------------------------------------
    # 6. Final Foundation Security Invariants
    # ---------------------------------------------------------
    assert brain.can_think_independently()
    assert brain.can_research_independently()
    assert brain.can_plan_independently()

    assert memory.memory_is_child_isolated()
    assert not memory.memory_access_grants_authority()

    assert knowledge.knowledge_equals_authority() is False
    assert knowledge.unknown_knowledge_is_trusted() is False

    assert communication.can_modify_soul() is False
    assert communication.can_modify_constitution() is False
    assert communication.executes_messages() is False

    assert state_manager.cannot_self_authorize()
    assert state_manager.cannot_modify_constitution()
    assert state_manager.cannot_modify_soul()
    assert state_manager.grants_authority() is False
    assert state_manager.executes_runtime_action() is False

    print("SAHIBEX CHILD RUNTIME FOUNDATION TEST: PASS")


if __name__ == "__main__":
    main()
