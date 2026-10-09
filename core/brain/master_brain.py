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
from core.brain.factual_resolver import resolve_local_fact
from core.brain.math_resolver import resolve_math_question
from core.brain.text_task_resolver import resolve_text_task
from core.brain.conversation_resolver import resolve_local_conversation
from core.brain.answer_quality import assess_answer
from core.brain.prompt_injection_guard import PromptInjectionGuard
from core.brain.mother_reasoning_integration import (
    MotherReasoningIntegration,
)
from core.brain.mother_research_integration import (
    MotherResearchIntegration,
)
from core.research.standing_research_consent import StandingResearchConsent
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
from core.brain.internal_brain_team import InternalBrainTeam
from core.brain.continuous_learning_improvement import ContinuousLearningImprovement
from core.brain.security_safety_brain import SecuritySafetyBrain
from core.brain.emergency_stop import EmergencyStop
from core.brain.brain_lifecycle import BrainLifecycle

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
        # User explicitly requested routine public internet learning without
        # per-query prompts. This consent is deliberately scoped to search /
        # learn and the RESEARCH action; it is not general network approval.
        self.standing_research_consent = StandingResearchConsent()
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

        # SAHIBEX's own internal army/labor roles live inside the Mother
        # runtime. This registry does not create independent Child Brains;
        # handlers are reported executable only when genuinely registered.
        self.internal_brain_team = InternalBrainTeam()

        # Phase 10: controlled continuous learning and improvement.
        # Experience is collected from real BrainResult outcomes; skill
        # activation remains gated and cannot modify Constitution or
        # self-authorize protected updates.
        self.continuous_learning = ContinuousLearningImprovement()

        # Phase 11: unified fail-closed security/safety control plane.
        # Existing Constitution, PermissionGateway, verification,
        # audit, sandbox and emergency-stop components remain the
        # authoritative execution boundaries.
        self.emergency_stop = EmergencyStop()
        self.security_safety = SecuritySafetyBrain()
        self.security_safety.bind_runtime(
            constitution=self.constitution,
            permission_gateway=self.permission_gateway,
            emergency_stop=self.emergency_stop,
        )

        # Phase 12: lifecycle control plane. Identity remains the
        # existing immutable Root Identity; lifecycle never grants
        # authority or executes protected actions.
        self.brain_lifecycle = BrainLifecycle(
            root_identity=self.root_identity,
        )

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

        # Wire only capabilities that already have concrete, bounded runtime
        # implementations. Other role names remain visibly unwired until a
        # real implementation and regression tests exist.
        self.internal_brain_team.register_handler(
            "reading", self._internal_reading_handler
        )
        self.internal_brain_team.register_handler(
            "research", self._internal_research_handler
        )
        self.internal_brain_team.register_handler(
            "learning", self._internal_learning_handler
        )
        self.internal_brain_team.register_handler(
            "memory", self._internal_memory_handler
        )
        self.internal_brain_team.register_handler(
            "verification", self._internal_verification_handler
        )
        self.internal_brain_team.register_handler(
            "security", self._internal_security_handler
        )
        self.internal_brain_team.register_handler(
            "orchestration", self._internal_orchestration_handler
        )
        self.internal_brain_team.register_handler(
            "reasoning", self._internal_reasoning_handler
        )
        self.internal_brain_team.register_handler(
            "coding", self._internal_coding_handler
        )
        self.internal_brain_team.register_handler(
            "testing", self._internal_testing_handler
        )

    @staticmethod
    def _internal_testing_handler(request: str, context: dict):
        """Analyze a supplied test report; test execution stays with authorized Tool Brain."""
        reports = context.get("test_results")
        exit_code = context.get("exit_code")
        if not isinstance(reports, list) or not reports or len(reports) > 500:
            return {
                "success": False,
                "status": "TEST_RESULTS_REQUIRED",
                "executes_tests": False,
                "execution_verified": False,
            }
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            return {
                "success": False,
                "status": "VALID_EXIT_CODE_REQUIRED",
                "executes_tests": False,
                "execution_verified": False,
            }
        normalized = []
        for item in reports:
            if not isinstance(item, dict):
                return {"success": False, "status": "INVALID_TEST_REPORT", "executes_tests": False, "execution_verified": False}
            name = item.get("name")
            passed = item.get("passed")
            if not isinstance(name, str) or not name.strip() or not isinstance(passed, bool):
                return {"success": False, "status": "INVALID_TEST_REPORT", "executes_tests": False, "execution_verified": False}
            normalized.append({"name": name.strip(), "passed": passed})
        passed_count = sum(1 for item in normalized if item["passed"])
        failed_count = len(normalized) - passed_count
        consistent = (failed_count == 0 and exit_code == 0) or (failed_count > 0 and exit_code != 0)
        if not consistent:
            status = "INCONSISTENT_REPORT"
        elif failed_count:
            status = "TEST_FAILURES_REPORTED"
        else:
            status = "ALL_REPORTED_TESTS_PASSED"
        return {
            "success": consistent,
            "status": status,
            "reported_count": len(normalized),
            "passed_count": passed_count,
            "failed_count": failed_count,
            "failed_tests": [item["name"] for item in normalized if not item["passed"]],
            "exit_code": exit_code,
            "executes_tests": False,
            "execution_verified": False,
            "report_origin": str(context.get("report_origin", "unspecified")),
        }

    def _internal_reasoning_handler(self, request: str, context: dict):
        """Use the existing Mother reasoning adapter, then quality-check its response."""
        intent = context.get("intent", "explain")
        action = context.get("action", "respond")
        allowed_intents = {"search", "learn", "create", "code", "explain", "general_request", "system_status"}
        allowed_actions = {item.value for item in ActionType}
        if intent not in allowed_intents:
            intent = "general_request"
        if action not in allowed_actions:
            action = "respond"
        result = self.mother_reasoning.analyze_approved_request(
            user_input=request,
            intent=intent,
            action=action,
        )
        quality = assess_answer(request, result.reasoning_response)
        return {
            "success": result.success,
            "response": result.reasoning_response,
            "status": "STRUCTURALLY_VALID" if quality.acceptable else "QUALITY_REJECTED",
            "quality_reasons": quality.reasons,
            "factual_verification": False,
            "_reasoning_result": result,
        }

    def _internal_coding_handler(self, request: str, context: dict):
        """Generate a code draft through Mother Operational; never writes or executes it."""
        result = self.mother_operational.process_approved_request(
            objective=request,
            intent="code",
        )
        return {
            "success": result.success,
            "status": result.verification_status,
            "code_draft": result.response,
            "provider": result.provider,
            "memory_ids": result.memory_ids,
            "knowledge_ids": result.knowledge_ids,
            "writes_files": False,
            "executes_code": False,
            "factual_verification": False,
            "_operational_result": result,
        }

    def _internal_orchestration_handler(self, request: str, context: dict):
        """Create an execution-neutral task plan; never runs its tasks."""
        requested_intent = context.get("intent", "general_request")
        allowed_intents = {"search", "learn", "create", "code", "explain", "general_request"}
        intent = requested_intent if requested_intent in allowed_intents else "general_request"
        result = self._build_plan(request.strip(), intent)
        return {
            "success": result.success,
            "status": "PLAN_CREATED_NOT_EXECUTED" if result.success else "PLAN_FAILED",
            "intent": intent,
            "goal_id": getattr(result.goal, "goal_id", None),
            "task_count": len(result.tasks),
            "task_ids": [task.task_id for task in result.tasks],
            "message": result.message,
            "execution_started": False,
            "_plan_result": result,
        }

    @staticmethod
    def _internal_security_handler(request: str, context: dict):
        """Inspect untrusted text for injection indicators; never grants authority."""
        content = context.get("content", request)
        if not isinstance(content, str):
            return {
                "success": False,
                "status": "TEXT_REQUIRED",
                "safe_to_follow": False,
                "grants_authority": False,
            }
        assessment = PromptInjectionGuard().inspect(
            content,
            source=str(context.get("source", "untrusted")),
        )
        return {
            "success": True,
            "status": assessment.status.value,
            "safe_to_follow": assessment.safe_to_follow,
            "matched_rules": assessment.matched_rules,
            "grants_authority": False,
            "executes_content": False,
        }

    @staticmethod
    def _internal_verification_handler(request: str, context: dict):
        """Run conservative answer-quality checks; this is not a fact-check."""
        question = context.get("question", request)
        answer = context.get("answer")
        if not isinstance(question, str) or not isinstance(answer, str):
            return {
                "success": False,
                "status": "QUESTION_AND_ANSWER_REQUIRED",
                "factual_verification": False,
            }
        assessment = assess_answer(question, answer)
        return {
            "success": True,
            "status": "QUALITY_ACCEPTED" if assessment.acceptable else "QUALITY_REJECTED",
            "acceptable": assessment.acceptable,
            "score": assessment.score,
            "reasons": assessment.reasons,
            "factual_verification": False,
        }

    @staticmethod
    def _internal_reading_handler(request: str, context: dict):
        """Extract supplied text only; never opens a path or executes content."""
        source_text = context.get("source_text")
        if not isinstance(source_text, str) or not source_text.strip():
            return {
                "success": False,
                "status": "SOURCE_TEXT_REQUIRED",
                "reason": "Reading Brain only processes text explicitly supplied in context.",
            }
        text = source_text.strip()
        max_chars = context.get("max_chars", 12000)
        if not isinstance(max_chars, int) or isinstance(max_chars, bool):
            max_chars = 12000
        max_chars = min(max(max_chars, 1), 12000)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return {
            "success": True,
            "status": "EXTRACTED_NOT_FACT_VERIFIED",
            "request": request.strip(),
            "character_count": len(text),
            "line_count": len(lines),
            "excerpt": text[:max_chars],
            "truncated": len(text) > max_chars,
        }

    def _internal_research_handler(self, request: str, context: dict):
        """Delegate to Mother Research; its own provider permission gates remain authoritative."""
        result = self.research_learning_brain.research_topic(
            request,
            confirmation=bool(context.get("confirmation", False)),
        )
        return {
            "success": result.success,
            "operation": result.operation,
            "verified": result.verified,
            "persisted": result.persisted,
            "result": result.result,
            "error": result.error,
        }

    def _internal_learning_handler(self, request: str, context: dict):
        """Delegate learning to the existing evidence and knowledge pipeline."""
        result = self.research_learning_brain.learn_topic(
            request,
            confirmation=bool(context.get("confirmation", False)),
        )
        return {
            "success": result.success,
            "operation": result.operation,
            "verified": result.verified,
            "persisted": result.persisted,
            "result": result.result,
            "error": result.error,
        }

    def _internal_memory_handler(self, request: str, context: dict):
        """Read-only retrieval from existing memory; never writes or deletes."""
        matches = self.memory_brain.retrieve(request)
        return {
            "success": True,
            "status": "MEMORY_RETRIEVAL_ONLY",
            "count": len(matches),
            "matches": matches,
        }

    def dispatch_internal_brain(
        self,
        role_id: str,
        request: str,
        context: dict | None = None,
        *,
        authorization_passed: bool = False,
        verification_passed: bool = False,
    ):
        """Explicit internal-role entry point; callers must supply upstream gate results."""
        return self.internal_brain_team.dispatch(
            role_id,
            request,
            context,
            authorization_passed=authorization_passed,
            verification_passed=verification_passed,
        )

    def start_lifecycle(self):
        return self.brain_lifecycle.startup()

    def lifecycle_status(self):
        return self.brain_lifecycle.status()

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

        # SAFE ARITHMETIC: deterministic and independent of language-model quality.
        math_response = resolve_math_question(text)
        if math_response is not None:
            self.runtime_state.transition(MotherRuntimeState.UNDERSTANDING)
            self.runtime_state.set_request_context(
                intent="general_request", action="respond", risk="low"
            )
            self.runtime_state.set_authority(
                permission_allowed=True, confirmation_required=False
            )
            self.runtime_state.set_verification("DETERMINISTIC_ARITHMETIC")
            result = BrainResult(
                success=True,
                message=math_response.answer,
                intent="general_request",
                intent_confidence=1.0,
                action="respond",
                action_confidence=1.0,
                risk="low",
                permission_allowed=True,
                confirmation_required=False,
                authority_decision=ActionDecision.ALLOW.value,
                plan_created=False,
                task_count=0,
                goal_id=None,
                verification_status="DETERMINISTIC_ARITHMETIC",
                metadata={
                    "response_source": "safe_arithmetic_resolver",
                    "expression": math_response.expression,
                },
            )
            self.runtime_state.complete("safe arithmetic resolved")
            result.metadata["mother_runtime_state"] = self.runtime_state.snapshot()
            self._record_context(text, result)
            return result

        # FAST, CURATED FACT: resolve only exact supported questions.
        # Compound questions must go through normal reasoning; never answer
        # a substring while silently omitting the rest of the request.
        local_fact = resolve_local_fact(text)
        if local_fact is not None:
            # Fast-path answers must still participate in the same runtime
            # lifecycle telemetry as the full reasoning path.
            self.runtime_state.transition(
                MotherRuntimeState.UNDERSTANDING
            )
            self.runtime_state.set_request_context(
                intent="explain",
                action="respond",
                risk="low",
            )
            self.runtime_state.set_authority(
                permission_allowed=True,
                confirmation_required=False,
            )
            self.runtime_state.set_verification(
                "STRUCTURALLY_VALID"
            )
            result = BrainResult(
                success=True,
                message=local_fact.answer,
                intent="explain",
                intent_confidence=1.0,
                action="respond",
                action_confidence=1.0,
                risk="low",
                permission_allowed=True,
                confirmation_required=False,
                authority_decision=ActionDecision.ALLOW.value,
                plan_created=False,
                task_count=0,
                goal_id=None,
                verification_status="STRUCTURALLY_VALID",
                metadata={
                    "response_source": "curated_local_knowledge",
                    "fact_id": local_fact.fact_id,
                },
            )
            self.runtime_state.complete("curated local fact answered")
            result.metadata["mother_runtime_state"] = (
                self.runtime_state.snapshot()
            )
            self._record_context(text, result)
            return result

        # BASIC TEXT CONVERSATION: deterministic greetings, capability, and
        # status replies do not depend on small-model generation quality.
        local_conversation = resolve_local_conversation(text)
        if local_conversation is not None:
            self.runtime_state.transition(MotherRuntimeState.UNDERSTANDING)
            self.runtime_state.set_request_context(
                intent=local_conversation.intent,
                action="respond",
                risk="low",
            )
            self.runtime_state.set_authority(
                permission_allowed=True,
                confirmation_required=False,
            )
            self.runtime_state.set_verification("STRUCTURALLY_VALID")
            result = BrainResult(
                success=True,
                message=local_conversation.answer,
                intent=local_conversation.intent,
                intent_confidence=1.0,
                action="respond",
                action_confidence=1.0,
                risk="low",
                permission_allowed=True,
                confirmation_required=False,
                authority_decision=ActionDecision.ALLOW.value,
                plan_created=False,
                task_count=0,
                goal_id=None,
                verification_status="STRUCTURALLY_VALID",
                metadata={
                    "response_source": "deterministic_text_conversation",
                    "response_id": local_conversation.response_id,
                },
            )
            self.runtime_state.complete("basic text conversation answered")
            result.metadata["mother_runtime_state"] = self.runtime_state.snapshot()
            self._record_context(text, result)
            return result

        # SAFE, EXACT TEXT TASKS: deterministic answers for validated common
        # questions/examples avoid known weak small-model generations.
        text_task = resolve_text_task(text)
        if text_task is not None:
            self.runtime_state.transition(MotherRuntimeState.UNDERSTANDING)
            self.runtime_state.set_request_context(intent="explain", action="respond", risk="low")
            self.runtime_state.set_authority(permission_allowed=True, confirmation_required=False)
            self.runtime_state.set_verification("DETERMINISTIC_TEXT_TASK")
            result = BrainResult(
                success=True, message=text_task.answer, intent="explain",
                intent_confidence=1.0, action="respond", action_confidence=1.0,
                risk="low", permission_allowed=True, confirmation_required=False,
                authority_decision=ActionDecision.ALLOW.value, plan_created=False,
                task_count=0, goal_id=None,
                verification_status="DETERMINISTIC_TEXT_TASK",
                metadata={"response_source": "deterministic_text_task", "task_id": text_task.task_id},
            )
            self.runtime_state.complete("deterministic text task answered")
            result.metadata["mother_runtime_state"] = self.runtime_state.snapshot()
            self._record_context(text, result)
            return result

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

        standing_research_allowed = self.standing_research_consent.allows(
            intent=intent_result.intent,
            action=action.value,
            request=text,
        )
        effective_confirmation = bool(user_confirmation or standing_research_allowed)

        authority = self.human_approval.check(
            constitution_action,
            user_confirmation=effective_confirmation,
        )

        permission = self.permission_gateway.check(
            action,
            confirmation=effective_confirmation,
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

        reasoning_dispatch = self.dispatch_internal_brain(
            "reasoning",
            text,
            {"intent": intent_result.intent, "action": action.value},
            authorization_passed=permission.allowed,
            verification_passed=verification.verified,
        )
        reasoning_result = (
            reasoning_dispatch.result.get("_reasoning_result")
            if reasoning_dispatch.accepted and isinstance(reasoning_dispatch.result, dict)
            else None
        )

        if reasoning_result is None:
            self.runtime_state.fail("Internal Reasoning Brain dispatch failed closed.")
            result = self._blocked_result(
                text=text,
                intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                action=action,
                action_confidence=action_confidence,
                risk=risk.value,
                authority_decision=authority.decision.value,
                confirmation_required=permission.requires_confirmation,
                message="Internal Reasoning Brain dispatch failed closed.",
                verification_status="NOT_EXECUTED",
                permission_allowed=permission.allowed,
            )
            self._record_context(text, result)
            return result

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
        orchestration_dispatch = self.dispatch_internal_brain(
            "orchestration",
            text,
            {"intent": intent_result.intent},
            authorization_passed=permission.allowed,
            verification_passed=verification.verified,
        )
        plan = (
            orchestration_dispatch.result.get("_plan_result")
            if orchestration_dispatch.accepted and isinstance(orchestration_dispatch.result, dict)
            else None
        )
        if plan is None:
            self.runtime_state.fail("Internal Orchestration Brain dispatch failed closed.")
            result = self._blocked_result(
                text=text,
                intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                action=action,
                action_confidence=action_confidence,
                risk=risk.value,
                authority_decision=authority.decision.value,
                confirmation_required=permission.requires_confirmation,
                message="Internal Orchestration Brain dispatch failed closed.",
                verification_status="NOT_EXECUTED",
                permission_allowed=permission.allowed,
            )
            self._record_context(text, result)
            return result

        internal_role_trace = {
            "reasoning": "DISPATCHED",
            "orchestration": "DISPATCHED",
        }

        # ---------------------------------------------------------
        # MOTHER RESEARCH / LEARNING / OPERATIONAL RUNTIME
        # ---------------------------------------------------------
        self.runtime_state.transition(
            MotherRuntimeState.EXECUTING
        )

        operational_result = None
        research_result = None
        learning_result = None
        tool_result = None

        # ---------------------------------------------------------
        # PROTECTED TOOL RUNTIME
        # ---------------------------------------------------------
        # Once the existing Constitution + Permission + Human Approval
        # gates have explicitly allowed a protected action, execution is
        # delegated to Tool Brain. Tool Brain never self-authorizes.
        if action in {
            ActionType.WRITE_FILE,
            ActionType.DELETE_FILE,
            ActionType.RUN_COMMAND,
        }:
            self.runtime_state.set_operation("tool_brain_protected")
            tool_result = self.tool_brain.execute(
                text,
                user_confirmation=user_confirmation,
            )

            if not tool_result.success:
                self.runtime_state.fail(
                    tool_result.error
                    or tool_result.reason
                    or "Protected tool execution failed."
                )

                result = self._blocked_result(
                    text=text,
                    intent=intent_result.intent,
                    intent_confidence=intent_result.confidence,
                    action=action,
                    action_confidence=action_confidence,
                    risk=risk.value,
                    authority_decision=authority.decision.value,
                    confirmation_required=tool_result.requires_confirmation,
                    message=(
                        tool_result.error
                        or tool_result.reason
                        or "Protected tool execution failed."
                    ),
                    verification_status="NOT_EXECUTED",
                    permission_allowed=tool_result.allowed,
                    plan=plan,
                )
                self._record_context(text, result)
                return result

        # ---------------------------------------------------------
        # READ-ONLY TOOL RUNTIME
        # ---------------------------------------------------------
        # Read-only tool requests are executed through Tool Brain,
        # rather than being answered by the language model as if the
        # file had been inspected. Tool Brain remains the authority
        # boundary for discovery, permission, safe execution, result
        # verification, and recovery.
        if (
            intent_result.intent == "file_operation"
            and action == ActionType.READ_FILE
        ):
            self.runtime_state.set_operation("tool_brain")
            tool_result = self.tool_brain.execute(
                text,
                user_confirmation=user_confirmation,
            )

            if not tool_result.success:
                self.runtime_state.fail(
                    tool_result.error
                    or tool_result.reason
                    or "Tool execution failed."
                )

                result = self._blocked_result(
                    text=text,
                    intent=intent_result.intent,
                    intent_confidence=intent_result.confidence,
                    action=action,
                    action_confidence=action_confidence,
                    risk=risk.value,
                    authority_decision=authority.decision.value,
                    confirmation_required=tool_result.requires_confirmation,
                    message=(
                        tool_result.error
                        or tool_result.reason
                        or "Tool execution failed."
                    ),
                    verification_status="NOT_EXECUTED",
                    permission_allowed=tool_result.allowed,
                    plan=plan,
                )
                self._record_context(text, result)
                return result

        # ---------------------------------------------------------
        # RESEARCH
        # ---------------------------------------------------------
        elif intent_result.intent == "search":
            self.runtime_state.set_operation(
                "mother_research"
            )

            research_dispatch = self.dispatch_internal_brain(
                "research",
                text,
                {"confirmation": effective_confirmation},
                authorization_passed=permission.allowed,
                verification_passed=verification.verified,
            )
            internal_role_trace["research"] = "DISPATCHED" if research_dispatch.accepted else "BLOCKED"
            research_result = (
                research_dispatch.result.get("result")
                if research_dispatch.accepted and isinstance(research_dispatch.result, dict)
                else None
            )

            if research_result is None or not research_result.success:
                research_error = (
                    research_result.answer
                    if research_result is not None and research_result.answer
                    else research_result.error
                    if research_result is not None
                    else research_dispatch.reason
                ) or "Research execution failed."
                self.runtime_state.fail(research_error)

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
                    message=research_error,
                    verification_status=(
                        research_result.verification_status
                        if research_result is not None
                        else "NOT_EXECUTED"
                    ),
                    permission_allowed=permission.allowed,
                    plan=plan,
                    metadata={
                        "internal_brain_dispatch": dict(internal_role_trace),
                        "mother_research_integration": {
                            "success": (
                                research_result.success
                                if research_result is not None
                                else False
                            ),
                            "status": (
                                research_result.status
                                if research_result is not None
                                else "NOT_EXECUTED"
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
                                else "NOT_EXECUTED"
                            ),
                            "error": (
                                research_result.error
                                if research_result is not None
                                else research_error
                            ),
                        },
                    },
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

            learning_dispatch = self.dispatch_internal_brain(
                "learning",
                text,
                {"confirmation": effective_confirmation},
                authorization_passed=permission.allowed,
                verification_passed=verification.verified,
            )
            internal_role_trace["learning"] = "DISPATCHED" if learning_dispatch.accepted else "BLOCKED"
            learning_result = (
                learning_dispatch.result.get("result")
                if learning_dispatch.accepted and isinstance(learning_dispatch.result, dict)
                else None
            )

            if learning_result is None or not learning_result.success:
                learning_error = (
                    learning_result.error
                    if learning_result is not None
                    else learning_dispatch.reason
                ) or "Learning execution failed."
                self.runtime_state.fail(learning_error)

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
                    message=learning_error,
                    verification_status=(
                        learning_result.verification_status
                        if learning_result is not None
                        else "NOT_EXECUTED"
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

            if intent_result.intent == "code":
                coding_dispatch = self.dispatch_internal_brain(
                    "coding",
                    text,
                    {},
                    authorization_passed=permission.allowed,
                    verification_passed=verification.verified,
                )
                internal_role_trace["coding"] = "DISPATCHED" if coding_dispatch.accepted else "BLOCKED"
                operational_result = (
                    coding_dispatch.result.get("_operational_result")
                    if coding_dispatch.accepted and isinstance(coding_dispatch.result, dict)
                    else None
                )
                if operational_result is None:
                    self.runtime_state.fail("Internal Coding Brain dispatch failed closed.")
                    result = self._blocked_result(
                        text=text,
                        intent=intent_result.intent,
                        intent_confidence=intent_result.confidence,
                        action=action,
                        action_confidence=action_confidence,
                        risk=risk.value,
                        authority_decision=authority.decision.value,
                        confirmation_required=permission.requires_confirmation,
                        message="Internal Coding Brain dispatch failed closed.",
                        verification_status="NOT_EXECUTED",
                        permission_allowed=permission.allowed,
                        plan=plan,
                    )
                    self._record_context(text, result)
                    return result
            else:
                operational_result = (
                    self.mother_operational.process_approved_request(
                        objective=text,
                        intent=intent_result.intent,
                        provider=self.mother_operational.default_provider,
                    )
                )

            if not operational_result.success:
                failure_message = (
                    operational_result.response
                    or "Mother Brain operational processing failed."
                )
                self.runtime_state.fail(failure_message)

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
                    message=failure_message,
                    verification_status=(
                        operational_result.verification_status
                    ),
                    permission_allowed=permission.allowed,
                    plan=plan,
                    metadata={
                        "failure_stage": "mother_operational",
                        "mother_decision_context": decision_context.summary(),
                        "mother_operational_integration": {
                            "success": operational_result.success,
                            "verification_status": operational_result.verification_status,
                            "provider": operational_result.provider,
                            "memory_ids": operational_result.memory_ids,
                            "knowledge_ids": operational_result.knowledge_ids,
                        },
                    },
                )

                self._record_context(text, result)
                return result

        # ---------------------------------------------------------
        # FINAL RESPONSE MESSAGE
        # ---------------------------------------------------------
        if tool_result is not None:
            tool_payload = tool_result.result
            if isinstance(tool_payload, dict) and "content" in tool_payload:
                message = str(tool_payload["content"])
            else:
                message = str(tool_payload)
        elif research_result is not None:
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
            # Preserve the operational response's factual-verification boundary.
            verification_status=(
                operational_result.verification_status
                if operational_result is not None
                else verification.status
            ),
            metadata={
                "internal_brain_dispatch": dict(internal_role_trace),
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
                "tool_brain_integration": {
                    "success": (
                        tool_result.success
                        if tool_result is not None
                        else False
                    ),
                    "tool": (
                        tool_result.tool
                        if tool_result is not None
                        else None
                    ),
                    "allowed": (
                        tool_result.allowed
                        if tool_result is not None
                        else False
                    ),
                    "recovery_status": (
                        tool_result.recovery_status
                        if tool_result is not None
                        else "NOT_USED"
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
        metadata: dict[str, Any] | None = None,
    ) -> BrainResult:
        # A blocked protected action is not a successful execution.
        # confirmation_required is status metadata, not success.
        success = False

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
            metadata=dict(metadata or {}),
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

        # Phase 10 experience collection is deliberately observational.
        # A failed/blocked result becomes a learning signal; it never
        # grants permission or triggers an automatic protected update.
        try:
            learning_outcome = result.message or ""
            if learning_outcome.startswith(
                "MOCK MODEL RESPONSE: Received request:"
            ):
                learning_outcome = (
                    "[MOCK_RESPONSE_ECHO_SUPPRESSED]"
                )
            learning_outcome = learning_outcome[:16384]

            self.continuous_learning.record_experience(
                task=text or "empty request",
                context=f"intent={result.intent}; risk={result.risk}",
                action_taken=result.action,
                outcome=learning_outcome,
                lesson=(
                    "Successful verified interaction."
                    if result.success
                    else "Review failed/blocked interaction before proposing improvement."
                ),
                success=result.success,
                confidence=(
                    1.0
                    if result.verification_status == "VERIFIED"
                    else 0.6
                ),
                importance=0.7,
                tags=[result.intent, result.action, result.verification_status],
                provenance={
                    "goal_id": result.goal_id,
                    "authority_decision": result.authority_decision,
                },
            )
        except (TypeError, ValueError):
            # Learning telemetry must never break the primary Brain result.
            pass
