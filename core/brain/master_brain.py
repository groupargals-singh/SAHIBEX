from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.brain.context import ContextManager
from core.brain.intent import IntentEngine
from core.brain.mother_learning_integration import MotherLearningIntegration
from core.brain.mother_decision_context import MotherDecisionContext
from core.brain.mother_runtime_state import (
    MotherBrainState,
    MotherRuntimeState,
)
from core.brain.mother_operational_integration import (
    MotherOperationalIntegration,
)
from core.brain.mother_reasoning_integration import (
    MotherReasoningIntegration,
)
from core.brain.mother_research_integration import (
    MotherResearchIntegration,
)
from core.brain.permission_constitution_integration import (
    MasterPermissionConstitutionIntegration,
)
from core.brain.verification_trust_integration import (
    MasterVerificationTrustIntegration,
)
from core.orchestrator.planner import MasterPlanner, PlanStep
from core.orchestrator.task_state import TaskPriority
from core.policies.approval import ActionType, PermissionEngine
from core.brain.permission_gateway import PermissionGateway
from tools.human_approval import HumanApprovalGateway
from core.policies.constitution import (
    ActionClass,
    ActionDecision,
    SahibexConstitution,
)
from verification.verifier import VerificationEngine
from core.brain.root_identity import SahibexRootIdentity
from core.brain.root_instance import SahibexRootInstanceIdentity
from core.brain.memory_brain import MemoryBrain
from core.brain.knowledge_brain import KnowledgeBrain
from core.brain.research_learning_brain import ResearchLearningBrain
from core.brain.tool_brain import ToolBrain
from core.agent.autonomous_work_brain import AutonomousWorkBrain
from core.agent_goal import AgentGoal
from core.brain.specialist_child_manager import SpecialistChildBrainManager

@dataclass(frozen=True)
class BrainResult:
    success: bool
    message: str
    intent: str
    intent_confidence: float
    action: str
    action_confidence: float
    risk: str
    permission_allowed: bool
    confirmation_required: bool
    authority_decision: str
    plan_created: bool
    task_count: int
    goal_id: str | None
    verification_status: str
    metadata: dict[str, Any] = field(default_factory=dict)


class MasterBrain:
    """
    Central coordination layer of SAHIBEX.

    Pipeline:

        User Request
            ↓
        Intent
            ↓
        Explicit Action Detection
            ↓
        Constitution
            ↓
        Permission
            ↓
        Permission/Constitution Integration
            ↓
        Verification
            ↓
        Verification/Trust Integration
            ↓
        Mother Reasoning
            ↓
        Mother Research / Learning / Operational Runtime
            ↓
        Planning
            ↓
        Context
    """

    INTENT_ACTION_MAP = {
        "system_status": (
            ActionType.RESPOND,
            ActionClass.THINK,
        ),
        "search": (
            ActionType.RESEARCH,
            ActionClass.RESEARCH,
        ),
        "learn": (
            ActionType.RESPOND,
            ActionClass.THINK,
        ),
        "create": (
            ActionType.CREATE,
            ActionClass.THINK,
        ),
        "explain": (
            ActionType.RESPOND,
            ActionClass.THINK,
        ),
        "code": (
            ActionType.CREATE,
            ActionClass.THINK,
        ),
        "file_operation": (
            ActionType.READ_FILE,
            ActionClass.READ,
        ),
        "general_request": (
            ActionType.RESPOND,
            ActionClass.THINK,
        ),
        "empty": (
            ActionType.RESPOND,
            ActionClass.THINK,
        ),
    }

    def __init__(
        self,
        *,
        intent_engine: IntentEngine | None = None,
        context_manager: ContextManager | None = None,
        planner: MasterPlanner | None = None,
        constitution: SahibexConstitution | None = None,
        permission_engine: PermissionEngine | None = None,
        human_approval: HumanApprovalGateway | None = None,
        permission_gateway: PermissionGateway | None = None,
        verification_engine: VerificationEngine | None = None,
        mother_operational: MotherOperationalIntegration | None = None,
        mother_reasoning: MotherReasoningIntegration | None = None,
        mother_research: MotherResearchIntegration | None = None,
        mother_learning: MotherLearningIntegration | None = None,
    ) -> None:
        self.root_identity = SahibexRootIdentity()

        if not self.root_identity.validate():
            raise RuntimeError(
                "SAHIBEX root identity integrity validation failed."
            )
        self.root_instance_identity = SahibexRootInstanceIdentity(
            root_identity=self.root_identity,
        )

        if not self.root_instance_identity.validate():
            raise RuntimeError(
                "SAHIBEX root instance identity integrity validation failed."
            )
        self.intent_engine = (
            intent_engine
            if intent_engine is not None
            else IntentEngine()
        )

        self.context = (
            context_manager
            if context_manager is not None
            else ContextManager()
        )

        self.planner = (
            planner
            if planner is not None
            else MasterPlanner()
        )

        self.constitution = (
            constitution
            if constitution is not None
            else SahibexConstitution()
        )

        self.permission = (
            permission_engine
            if permission_engine is not None
            else PermissionEngine()
        )
        self.permission_gateway = (
            permission_gateway
            if permission_gateway is not None
            else PermissionGateway(
        permission_engine=self.permission,
            )
        )
        self.human_approval = (
            human_approval
            if human_approval is not None
            else HumanApprovalGateway(
        constitution=self.constitution,
            )
        )

        self.verification = (
            verification_engine
            if verification_engine is not None
            else VerificationEngine()
        )

        self.permission_constitution_integration = (
            MasterPermissionConstitutionIntegration()
        )

        self.verification_trust_integration = (
            MasterVerificationTrustIntegration()
        )

        # Phase 9: secure specialist Child-Brain runtime. The manager
        # binds only the Mother identity; protected authority remains
        # with the existing Constitution/permission pipeline.
        self.specialist_child_brains = SpecialistChildBrainManager()

        self.mother_operational = (
            mother_operational
            if mother_operational is not None
            else MotherOperationalIntegration()
        )

        self.mother_reasoning = (
            mother_reasoning
            if mother_reasoning is not None
            else MotherReasoningIntegration()
        )

        self.mother_research = (
            mother_research
            if mother_research is not None
            else MotherResearchIntegration()
        )

        self.mother_learning = (
            mother_learning
            if mother_learning is not None
            else MotherLearningIntegration(
                research=self.mother_research
            )
        )

        self.runtime_state = MotherBrainState()
        self.memory_brain = MemoryBrain(storage=self.mother_operational.storage)
        self.knowledge_brain = KnowledgeBrain(storage=self.mother_operational.storage)
        self.research_learning_brain = ResearchLearningBrain(
            research=self.mother_research,
            learning=self.mother_learning,
        )
        self.tool_brain = ToolBrain(
            permission_engine=self.permission,
        )
        self.autonomous_work_brain = AutonomousWorkBrain()

    def run_autonomous_work(
        self,
        goal: AgentGoal,
        *,
        execute_step,
        verify_step,
        user_confirmation: bool = False,
        job_id: str | None = None,
        runtime_id: str = "main",
        max_steps: int = 100,
    ):
        """Run a permission-governed multi-step goal through Phase 7."""
        return self.autonomous_work_brain.run(
            goal,
            execute_step=execute_step,
            verify_step=verify_step,
            user_confirmation=user_confirmation,
            job_id=job_id,
            runtime_id=runtime_id,
            max_steps=max_steps,
        )

    def process(
        self,
        text: str,
        *,
        user_confirmation: bool = False,
    ) -> BrainResult:
        self.runtime_state = MotherBrainState()

        # ---------------------------------------------------------
        # EMPTY REQUEST
        # ---------------------------------------------------------
        if not isinstance(text, str) or not text.strip():
            self.runtime_state.request = text
            self.runtime_state.transition(
                MotherRuntimeState.RECEIVING
            )
            self.runtime_state.block(
                "Empty request."
            )

            result = BrainResult(
                success=False,
                message="Empty request.",
                intent="empty",
                intent_confidence=1.0,
                action="respond",
                action_confidence=1.0,
                risk="low",
                permission_allowed=False,
                confirmation_required=False,
                authority_decision=ActionDecision.DENY.value,
                plan_created=False,
                task_count=0,
                goal_id=None,
                verification_status="NOT_EXECUTED",
            )

            self._record_context(text, result)
            return result

        # ---------------------------------------------------------
        # RECEIVE REQUEST
        # ---------------------------------------------------------
        self.runtime_state.begin(text)

        # ---------------------------------------------------------
        # INTENT
        # ---------------------------------------------------------
        intent_result = self.intent_engine.detect(text)

        self.runtime_state.transition(
            MotherRuntimeState.UNDERSTANDING
        )

        self.runtime_state.set_request_context(
            intent=intent_result.intent,
            action="",
            risk="",
        )

        # ---------------------------------------------------------
        # ACTION CLASSIFICATION
        # ---------------------------------------------------------
        action, constitution_action = self._classify_action(
            text,
            intent_result.intent,
        )

        action_confidence = self._action_confidence(
            text,
            action,
        )

        risk = self.permission.RISK_MAP[action]

        self.runtime_state.set_request_context(
            intent=intent_result.intent,
            action=action.value,
            risk=risk.value,
        )

        # ---------------------------------------------------------
        # AUTHORIZATION
        # ---------------------------------------------------------
        self.runtime_state.transition(
            MotherRuntimeState.AUTHORIZING
        )

        authority = self.human_approval.check(
            constitution_action,
            user_confirmation=user_confirmation,
        )

        permission = self.permission_gateway.check(
            action,
            confirmation=user_confirmation,
        )

        # ---------------------------------------------------------
        # PERMISSION / CONSTITUTION INTEGRATION
        # ---------------------------------------------------------
        permission_constitution_integration = (
            self.permission_constitution_integration.evaluate(
                action=action.value,
                allowed=permission.allowed,
                requires_confirmation=(
                    permission.requires_confirmation
                ),
                reason=permission.reason,
            )
        )

        # ---------------------------------------------------------
        # VERIFICATION
        # ---------------------------------------------------------
        verification = self.verification.verify(
            intent=intent_result.intent,
            intent_confidence=intent_result.confidence,
            action=action,
            action_confidence=action_confidence,
            risk=risk,
            permission_allowed=permission.allowed,
            confirmation_required=(
                permission.requires_confirmation
            ),
        )

        self.runtime_state.set_authority(
            permission_allowed=permission.allowed,
            confirmation_required=(
                permission.requires_confirmation
            ),
        )

        self.runtime_state.transition(
            MotherRuntimeState.VERIFYING
        )

        self.runtime_state.set_verification(
            verification.status
        )

        # ---------------------------------------------------------
        # VERIFICATION / TRUST INTEGRATION
        # ---------------------------------------------------------
        verification_trust_integration = (
            self.verification_trust_integration.integrate(
                verification_id=(
                    f"master-verification-{intent_result.intent}"
                ),
                brain_id=self.root_identity.BRAIN_ID,
                trust_status=(
                    "verified"
                    if verification.verified
                    else "unverified"
                ),
                confidence=float(
                    verification.confidence
                    if hasattr(
                        verification,
                        "confidence",
                    )
                    else intent_result.confidence
                ),
                summary=(
                    "Master Brain verification status: "
                    f"{verification.status}"
                ),
            )
        )

        # ---------------------------------------------------------
        # CONSTITUTION DENIAL
        # ---------------------------------------------------------
        if authority.decision == ActionDecision.DENY:
            self.runtime_state.block(
                authority.reason
            )

            result = self._blocked_result(
                text=text,
                intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                action=action,
                action_confidence=action_confidence,
                risk=risk.value,
                authority_decision=authority.decision.value,
                confirmation_required=False,
                message=authority.reason,
                verification_status=verification.status,
            )

            self._record_context(text, result)
            return result

        # ---------------------------------------------------------
        # PROTECTED ACTION WITHOUT CONFIRMATION
        # ---------------------------------------------------------
        if (
            authority.decision
            == ActionDecision.REQUIRE_CONFIRMATION
            and not user_confirmation
        ):
            self.runtime_state.block(
                "Protected action requires explicit user confirmation."
            )

            result = self._blocked_result(
                text=text,
                intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                action=action,
                action_confidence=action_confidence,
                risk=risk.value,
                authority_decision=authority.decision.value,
                confirmation_required=True,
                message=(
                    "Protected action requires explicit "
                    "user confirmation."
                ),
            )

            self._record_context(text, result)
            return result

        # ---------------------------------------------------------
        # PERMISSION BLOCK
        # ---------------------------------------------------------
        if not permission.allowed:
            self.runtime_state.block(
                permission.reason
            )

            result = self._blocked_result(
                text=text,
                intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                action=action,
                action_confidence=action_confidence,
                risk=risk.value,
                authority_decision=authority.decision.value,
                confirmation_required=(
                    permission.requires_confirmation
                ),
                message=permission.reason,
            )

            self._record_context(text, result)
            return result

        # ---------------------------------------------------------
        # VERIFICATION BLOCK
        # ---------------------------------------------------------
        if not verification.verified:
            self.runtime_state.block(
                "Request failed safety verification."
            )

            result = self._blocked_result(
                text=text,
                intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                action=action,
                action_confidence=action_confidence,
                risk=risk.value,
                authority_decision=authority.decision.value,
                confirmation_required=(
                    permission.requires_confirmation
                ),
                message=(
                    "Request failed safety verification."
                ),
                verification_status=verification.status,
            )

            self._record_context(text, result)
            return result

        # ---------------------------------------------------------
        # MOTHER COMBINED DECISION CONTEXT
        # ---------------------------------------------------------
        self.runtime_state.transition(
            MotherRuntimeState.CONTEXTUALIZING
        )

        decision_retrieval = (
            self.mother_operational.memory_knowledge.retrieve(
                query=text,
            )
        )

        decision_context = MotherDecisionContext(
            request=text,
            intent=intent_result.intent,
            conversation_summary=self.context.summary(),
            memory_ids=tuple(
                decision_retrieval.memory_ids
            ),
            knowledge_ids=tuple(
                decision_retrieval.knowledge_ids
            ),
            memory_items=tuple(
                decision_retrieval.memories
            ),
            knowledge_items=tuple(
                decision_retrieval.knowledge
            ),
            retrieval_id=decision_retrieval.retrieval_id,
            retrieval_summary=decision_retrieval.summary,
            research_available=True,
            learning_available=True,
        )

        # ---------------------------------------------------------
        # MOTHER REASONING
        # ---------------------------------------------------------
        self.runtime_state.transition(
            MotherRuntimeState.REASONING
        )

        self.runtime_state.set_operation(
            "mother_reasoning"
        )

        reasoning_result = (
            self.mother_reasoning.analyze_approved_request(
                user_input=text,
                intent=intent_result.intent,
                action=action.value,
            )
        )

        if not reasoning_result.success:
            self.runtime_state.fail(
                "Mother Brain reasoning integration failed."
            )

            result = self._blocked_result(
                text=text,
                intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                action=action,
                action_confidence=action_confidence,
                risk=risk.value,
                authority_decision=authority.decision.value,
                confirmation_required=(
                    permission.requires_confirmation
                ),
                message=(
                    "Mother Brain reasoning integration failed."
                ),
                verification_status=verification.status,
                permission_allowed=permission.allowed,
            )

            self._record_context(text, result)
            return result

        # ---------------------------------------------------------
        # MASTER PLAN (created BEFORE execution)
        # ---------------------------------------------------------
        # The plan is now a true control point between reasoning and
        # execution. A request must have a concrete goal/task graph
        # before research, learning, or operational work can run.
        self.runtime_state.transition(
            MotherRuntimeState.PLANNING
        )
        self.runtime_state.set_operation(
            "master_planner"
        )
        plan = self._build_plan(
            text,
            intent_result.intent,
        )

        # ---------------------------------------------------------
        # MOTHER RESEARCH / LEARNING / OPERATIONAL RUNTIME
        # ---------------------------------------------------------
        self.runtime_state.transition(
            MotherRuntimeState.EXECUTING
        )

        operational_result = None
        research_result = None
        learning_result = None

        # ---------------------------------------------------------
        # RESEARCH
        # ---------------------------------------------------------
        if intent_result.intent == "search":
            self.runtime_state.set_operation(
                "mother_research"
            )

            research_result = (
                self.mother_research.research(
                    query=text,
                    confirmation=user_confirmation,
                )
            )

            if not research_result.success:
                self.runtime_state.fail(
                    research_result.error
                    or "Research execution failed."
                )

                result = self._blocked_result(
                    text=text,
                    intent=intent_result.intent,
                    intent_confidence=intent_result.confidence,
                    action=action,
                    action_confidence=action_confidence,
                    risk=risk.value,
                    authority_decision=authority.decision.value,
                    confirmation_required=(
                        permission.requires_confirmation
                    ),
                    message=(
                        research_result.error
                        or "Research execution failed."
                    ),
                    verification_status=(
                        research_result.verification_status
                    ),
                    permission_allowed=permission.allowed,
                    plan=plan,
                )

                self._record_context(text, result)
                return result

        # ---------------------------------------------------------
        # LEARNING
        # ---------------------------------------------------------
        elif intent_result.intent == "learn":
            self.runtime_state.set_operation(
                "mother_learning"
            )

            learning_result = (
                self.mother_learning.learn(
                    topic=text,
                    confirmation=user_confirmation,
                )
            )

            if not learning_result.success:
                self.runtime_state.fail(
                    learning_result.error
                    or "Learning execution failed."
                )

                result = self._blocked_result(
                    text=text,
                    intent=intent_result.intent,
                    intent_confidence=intent_result.confidence,
                    action=action,
                    action_confidence=action_confidence,
                    risk=risk.value,
                    authority_decision=authority.decision.value,
                    confirmation_required=(
                        permission.requires_confirmation
                    ),
                    message=(
                        learning_result.error
                        or "Learning execution failed."
                    ),
                    verification_status=(
                        learning_result.verification_status
                    ),
                    permission_allowed=permission.allowed,
                    plan=plan,
                )

                self._record_context(text, result)
                return result

        # ---------------------------------------------------------
        # OPERATIONAL RUNTIME
        # ---------------------------------------------------------
        elif intent_result.intent in {
            "system_status",
            "explain",
            "general_request",
            "create",
            "code",
        }:
            self.runtime_state.set_operation(
                "mother_operational"
            )

            operational_result = (
                self.mother_operational.process_approved_request(
                    objective=text,
                    intent=intent_result.intent,
                    provider=self.mother_operational.default_provider,
                )
            )

            if not operational_result.success:
                self.runtime_state.fail(
                    operational_result.response
                )

                result = self._blocked_result(
                    text=text,
                    intent=intent_result.intent,
                    intent_confidence=intent_result.confidence,
                    action=action,
                    action_confidence=action_confidence,
                    risk=risk.value,
                    authority_decision=authority.decision.value,
                    confirmation_required=(
                        permission.requires_confirmation
                    ),
                    message=operational_result.response,
                    verification_status=(
                        operational_result.verification_status
                    ),
                    permission_allowed=permission.allowed,
                    plan=plan,
                )

                self._record_context(text, result)
                return result

        # ---------------------------------------------------------
        # FINAL RESPONSE MESSAGE
        # ---------------------------------------------------------
        if research_result is not None:
            message = research_result.answer
        elif learning_result is not None:
            message = learning_result.answer
        elif operational_result is not None:
            message = operational_result.response
        else:
            message = reasoning_result.reasoning_response

        # ---------------------------------------------------------
        # FINAL BRAIN RESULT
        # ---------------------------------------------------------
        result = BrainResult(
            success=True,
            message=message,
            intent=intent_result.intent,
            intent_confidence=intent_result.confidence,
            action=action.value,
            action_confidence=action_confidence,
            risk=risk.value,
            permission_allowed=permission.allowed,
            confirmation_required=(
                permission.requires_confirmation
            ),
            authority_decision=authority.decision.value,
            plan_created=True,
            task_count=len(plan.tasks),
            goal_id=plan.goal.goal_id,
            verification_status=verification.status,
            metadata={
                "authority": authority.authority.value,
                "authority_reason": authority.reason,
                "permission_reason": permission.reason,
                "verification_checks_passed": (
                    verification.checks_passed
                ),
                "verification_checks_failed": (
                    verification.checks_failed
                ),
                "permission_constitution_integration": {
                    "success": (
                        permission_constitution_integration.success
                    ),
                    "allowed": (
                        permission_constitution_integration.allowed
                    ),
                    "requires_confirmation": (
                        permission_constitution_integration
                        .requires_confirmation
                    ),
                    "reason": (
                        permission_constitution_integration.reason
                    ),
                    "integration_id": (
                        permission_constitution_integration
                        .integration_id
                    ),
                },
                "verification_trust_integration": {
                    "success": (
                        verification_trust_integration.success
                    ),
                    "verification_id": (
                        verification_trust_integration
                        .verification_id
                    ),
                    "brain_id": (
                        verification_trust_integration.brain_id
                    ),
                    "trust_status": (
                        verification_trust_integration.trust_status
                    ),
                    "confidence": (
                        verification_trust_integration.confidence
                    ),
                    "summary": (
                        verification_trust_integration.summary
                    ),
                    "integration_id": (
                        verification_trust_integration
                        .integration_id
                    ),
                },
                "mother_reasoning_integration": {
                    "success": reasoning_result.success,
                    "status": (
                        reasoning_result.reasoning_status
                    ),
                    "intent": reasoning_result.intent,
                    "action": reasoning_result.action,
                    "response": (
                        reasoning_result.reasoning_response
                    ),
                },
                "mother_operational_integration": {
                    "success": (
                        operational_result.success
                        if operational_result is not None
                        else False
                    ),
                    "verification_status": (
                        operational_result.verification_status
                        if operational_result is not None
                        else "NOT_USED"
                    ),
                    "provider": (
                        operational_result.provider
                        if operational_result is not None
                        else "NOT_USED"
                    ),
                    "memory_ids": (
                        operational_result.memory_ids
                        if operational_result is not None
                        else ()
                    ),
                    "knowledge_ids": (
                        operational_result.knowledge_ids
                        if operational_result is not None
                        else ()
                    ),
                },
                "mother_research_integration": {
                    "success": (
                        research_result.success
                        if research_result is not None
                        else False
                    ),
                    "status": (
                        research_result.status
                        if research_result is not None
                        else "NOT_USED"
                    ),
                    "job_id": (
                        research_result.job_id
                        if research_result is not None
                        else None
                    ),
                    "execution_id": (
                        research_result.execution_id
                        if research_result is not None
                        else None
                    ),
                    "verification_status": (
                        research_result.verification_status
                        if research_result is not None
                        else "NOT_USED"
                    ),
                    "conflict_status": (
                        research_result.conflict_status
                        if research_result is not None
                        else "NOT_USED"
                    ),
                    "conflict_count": (
                        research_result.conflict_count
                        if research_result is not None
                        else 0
                    ),
                    "resolved_conflict_count": (
                        research_result.resolved_conflict_count
                        if research_result is not None
                        else 0
                    ),
                    "unresolved_conflict_count": (
                        research_result.unresolved_conflict_count
                        if research_result is not None
                        else 0
                    ),
                    "conflict_ids": (
                        research_result.conflict_ids
                        if research_result is not None
                        else ()
                    ),
                    "resolved_knowledge_ids": (
                        research_result.resolved_knowledge_ids
                        if research_result is not None
                        else ()
                    ),
                },
                "mother_learning_integration": {
                    "success": (
                        learning_result.success
                        if learning_result is not None
                        else False
                    ),
                    "status": (
                        learning_result.status
                        if learning_result is not None
                        else "NOT_USED"
                    ),
                    "topic": (
                        learning_result.topic
                        if learning_result is not None
                        else None
                    ),
                    "knowledge_count": (
                        learning_result.knowledge_count
                        if learning_result is not None
                        else 0
                    ),
                    "verified_knowledge_count": (
                        learning_result.verified_knowledge_count
                        if learning_result is not None
                        else 0
                    ),
                    "research_job_id": (
                        learning_result.research_job_id
                        if learning_result is not None
                        else None
                    ),
                    "verification_status": (
                        learning_result.verification_status
                        if learning_result is not None
                        else "NOT_USED"
                    ),
                },
                "mother_decision_context": {
                    "request": decision_context.request,
                    "intent": decision_context.intent,
                    "conversation_summary": (
                        decision_context.conversation_summary
                    ),
                    "memory_count": len(
                        decision_context.memory_ids
                    ),
                    "knowledge_count": len(
                        decision_context.knowledge_ids
                    ),
                    "memory_ids": (
                        decision_context.memory_ids
                    ),
                    "knowledge_ids": (
                        decision_context.knowledge_ids
                    ),
                    "retrieval_id": (
                        decision_context.retrieval_id
                    ),
                    "retrieval_summary": (
                        decision_context.retrieval_summary
                    ),
                    "research_available": (
                        decision_context.research_available
                    ),
                    "learning_available": (
                        decision_context.learning_available
                    ),
                },
            },
        )

        # ---------------------------------------------------------
        # COMPLETE
        # ---------------------------------------------------------
        self.runtime_state.complete(
            "request completed"
        )

        result.metadata["mother_runtime_state"] = (
            self.runtime_state.snapshot()
        )

        self._record_context(
            text,
            result,
        )

        return result

    def _classify_action(
        self,
        text: str,
        intent: str,
    ) -> tuple[ActionType, ActionClass]:
        normalized = text.lower().strip()

        if any(
            keyword in normalized
            for keyword in (
                "delete",
                "remove",
                "erase",
                "destroy",
                "uninstall",
            )
        ):
            return (
                ActionType.DELETE_FILE,
                ActionClass.DELETE,
            )

        if any(
            keyword in normalized
            for keyword in (
                "run command",
                "execute command",
                "execute",
                "shell",
                "terminal",
            )
        ):
            return (
                ActionType.RUN_COMMAND,
                ActionClass.EXECUTE,
            )

        if any(
            keyword in normalized
            for keyword in (
                "api key",
                "api token",
                "password",
                "secret",
                "credential",
                "access token",
            )
        ):
            return (
                ActionType.CREDENTIAL_USE,
                ActionClass.CREDENTIAL,
            )

        if any(
            keyword in normalized
            for keyword in (
                "transfer money",
                "send money",
                "make payment",
                "pay ",
                "buy ",
                "sell ",
            )
        ):
            return (
                ActionType.FINANCIAL_ACTION,
                ActionClass.FINANCIAL,
            )

        if any(
            keyword in normalized
            for keyword in (
                "system configuration",
                "change system",
                "system change",
                "install system",
                "configure system",
            )
        ):
            return (
                ActionType.SYSTEM_CHANGE,
                ActionClass.SYSTEM_CHANGE,
            )

        if any(
            keyword in normalized
            for keyword in (
                "self update",
                "self-update",
                "update yourself",
                "modify yourself",
                "rewrite yourself",
            )
        ):
            return (
                ActionType.SYSTEM_CHANGE,
                ActionClass.SELF_UPDATE,
            )

        if any(
            keyword in normalized
            for keyword in (
                "upload",
                "download",
                "connect to",
                "network access",
                "http://",
                "https://",
            )
        ):
            return (
                ActionType.NETWORK_ACCESS,
                ActionClass.NETWORK,
            )

        if any(
            keyword in normalized
            for keyword in (
                "write file",
                "save file",
                "modify file",
                "edit file",
                "update file",
                "overwrite file",
            )
        ):
            return (
                ActionType.WRITE_FILE,
                ActionClass.WRITE,
            )

        return self.INTENT_ACTION_MAP.get(
            intent,
            (
                ActionType.RESPOND,
                ActionClass.THINK,
            ),
        )

    def _action_confidence(
        self,
        text: str,
        action: ActionType,
    ) -> float:
        normalized = text.lower().strip()

        protected_keywords = {
            ActionType.DELETE_FILE: (
                "delete",
                "remove",
                "erase",
                "destroy",
                "uninstall",
            ),
            ActionType.RUN_COMMAND: (
                "run command",
                "execute command",
                "execute",
                "shell",
                "terminal",
            ),
            ActionType.CREDENTIAL_USE: (
                "api key",
                "api token",
                "password",
                "secret",
                "credential",
                "access token",
            ),
            ActionType.FINANCIAL_ACTION: (
                "transfer money",
                "send money",
                "make payment",
                "pay ",
                "buy ",
                "sell ",
            ),
            ActionType.SYSTEM_CHANGE: (
                "system configuration",
                "change system",
                "system change",
                "install system",
                "configure system",
            ),
            ActionType.NETWORK_ACCESS: (
                "upload",
                "download",
                "connect to",
                "network access",
                "http://",
                "https://",
            ),
            ActionType.WRITE_FILE: (
                "write file",
                "save file",
                "modify file",
                "edit file",
                "update file",
                "overwrite file",
            ),
        }

        keywords = protected_keywords.get(action)

        if keywords is None:
            return 0.80

        matches = sum(
            1
            for keyword in keywords
            if keyword in normalized
        )

        if matches == 0:
            return 0.50

        return min(
            0.98,
            0.80 + (matches * 0.05),
        )

    def _build_plan(
        self,
        text: str,
        intent: str,
    ):
        if intent == "search":
            steps = [
                PlanStep(
                    title="Understand research request",
                    description=text,
                    priority=TaskPriority.NORMAL,
                ),
                PlanStep(
                    title="Prepare research",
                    description=(
                        "Collect and organize relevant information."
                    ),
                    priority=TaskPriority.NORMAL,
                ),
                PlanStep(
                    title="Verify research result",
                    description=(
                        "Check evidence and consistency."
                    ),
                    priority=TaskPriority.HIGH,
                ),
            ]

        elif intent == "learn":
            steps = [
                PlanStep(
                    title="Understand learning request",
                    description=text,
                    priority=TaskPriority.NORMAL,
                ),
                PlanStep(
                    title="Acquire learning evidence",
                    description=(
                        "Collect relevant information and evidence."
                    ),
                    priority=TaskPriority.NORMAL,
                ),
                PlanStep(
                    title="Verify learned knowledge",
                    description=(
                        "Check evidence, confidence and consistency."
                    ),
                    priority=TaskPriority.HIGH,
                ),
            ]

        elif intent in {"create", "code"}:
            steps = [
                PlanStep(
                    title="Understand requirements",
                    description=text,
                    priority=TaskPriority.NORMAL,
                ),
                PlanStep(
                    title="Prepare creation plan",
                    description=(
                        "Design the requested output."
                    ),
                    priority=TaskPriority.NORMAL,
                ),
                PlanStep(
                    title="Verify proposed result",
                    description=(
                        "Check the planned result before delivery."
                    ),
                    priority=TaskPriority.HIGH,
                ),
            ]

        else:
            steps = [
                PlanStep(
                    title="Analyze request",
                    description=text,
                    priority=TaskPriority.NORMAL,
                ),
                PlanStep(
                    title="Prepare response",
                    description=(
                        "Construct a suitable response."
                    ),
                    priority=TaskPriority.NORMAL,
                ),
            ]

        return self.planner.create_plan(
            title=f"SAHIBEX: {intent}",
            description=text,
            steps=steps,
        )

    def _blocked_result(
        self,
        *,
        text: str,
        intent: str,
        intent_confidence: float,
        action: ActionType,
        action_confidence: float,
        risk: str,
        authority_decision: str,
        confirmation_required: bool,
        message: str,
        verification_status: str = "NOT_EXECUTED",
        permission_allowed: bool = False,
        plan: Any | None = None,
    ) -> BrainResult:
        success = (
            confirmation_required
            and authority_decision
            == ActionDecision.REQUIRE_CONFIRMATION.value
        )

        return BrainResult(
            success=success,
            message=message,
            intent=intent,
            intent_confidence=intent_confidence,
            action=action.value,
            action_confidence=action_confidence,
            risk=risk,
            permission_allowed=permission_allowed,
            confirmation_required=confirmation_required,
            authority_decision=authority_decision,
            plan_created=plan is not None,
            task_count=(len(plan.tasks) if plan is not None else 0),
            goal_id=(plan.goal.goal_id if plan is not None else None),
            verification_status=verification_status,
        )

    def _record_context(
        self,
        text: str,
        result: BrainResult,
    ) -> None:
        self.context.add_turn(
            user=text,
            assistant=result.message,
            intent=result.intent,
        )
        self.memory_brain.remember_interaction(
            user_text=text or "",
            assistant_text=result.message,
            intent=result.intent,
            action=result.action,
            verification_status=result.verification_status,
        )
