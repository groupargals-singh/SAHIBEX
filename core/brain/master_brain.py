from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4
import os
import math
from datetime import datetime, timezone

from security.audit.audit_logger import AuditLogger

from core.brain.context import ContextManager
from core.brain.attention import AttentionEngine, AttentionInput
from core.brain.intent import IntentEngine, IntentResult
from core.brain.semantic_intent_brain import SemanticIntentBrain
from core.brain.input_normalization import InputNormalizationEngine
from core.brain.perception_language_brain import PerceptionLanguageBrain
from core.brain.universal_language_brain import UniversalLanguageBrain
from core.brain.contextual_input_understanding import ContextualInputUnderstandingBrain
from core.brain.confidence_verification_brain import ConfidenceVerificationBrain
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
from core.brain.dynamic_tool_creation_brain import DynamicToolCandidate
from core.agent.autonomous_work_brain import AutonomousWorkBrain
from core.agent_goal import AgentGoal
from core.brain.specialist_child_manager import SpecialistChildBrainManager
from core.brain.managed_worker_runtime import ManagedWorkerRuntime, WorkerExecution
from core.brain.internal_brain_team import InternalBrainTeam
from core.brain.coding_brain import CodingBrain
from core.brain.text_development_brain import TextDevelopmentBrain
from core.brain.test_brain import TestBrain
from core.brain.library_brain import LibraryBrain
from core.brain.continuous_learning_improvement import ContinuousLearningImprovement
from core.brain.self_improvement_state_store import SelfImprovementStateStore
from security.audit.child_self_improvement_audit_store import ChildSelfImprovementAuditStore
from core.brain.security_safety_brain import SecuritySafetyBrain
from core.brain.emergency_stop import EmergencyStop
from core.brain.brain_lifecycle import BrainLifecycle
from core.brain.cognitive_neural_architecture import CognitiveNeuralArchitecture
from core.brain.three_brain_council import ThreeBrainCouncil

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

    # One source of truth for action classification and confidence scoring.
    # Keep the conservative protected-action boundary consistent across both.
    PROTECTED_ACTION_KEYWORDS = {
        ActionType.DELETE_FILE: (
            "delete", "remove", "erase", "destroy", "uninstall",
            "डिलीट", "डिलीट करो", "हटा दो", "हटाओ", "मिटा दो", "मिटाओ",
            "delete karo", "hata do", "hatao", "mita do", "mitao",
        ),
        ActionType.RUN_COMMAND: (
            "run command", "execute command", "execute", "shell", "terminal",
            "कमांड चलाओ", "कमांड चला दो", "आदेश चलाओ", "टर्मिनल पर चलाओ",
            "command chalao", "command chala do", "command chalao",
        ),
        ActionType.CREDENTIAL_USE: (
            "api key", "api token", "password", "secret", "credential", "access token",
            "पासवर्ड", "गुप्त कुंजी", "क्रेडेंशियल", "पासवर्ड दिखाओ",
        ),
        ActionType.FINANCIAL_ACTION: (
            "transfer money", "send money", "make payment", "pay ", "buy ", "sell ",
            "पैसे भेजो", "पैसे ट्रांसफर", "भुगतान करो", "पेमेंट करो", "खरीदो", "बेचो",
            "paise bhejo", "paise transfer", "bhugtan karo", "payment karo",
        ),
        ActionType.SYSTEM_CHANGE: (
            "system configuration", "change system", "system change", "install system", "configure system",
            "self update", "self-update", "update yourself", "modify yourself", "rewrite yourself",
            "सिस्टम की सेटिंग बदलो", "सिस्टम सेटिंग बदलो", "सिस्टम कॉन्फ़िगरेशन बदलो",
            "सिस्टम की सेटिंग बदल दो", "system settings badal do", "system setting badlo",
            "self update karo", "khud ko update karo",
        ),
        ActionType.NETWORK_ACCESS: (
            "upload", "download", "connect to", "network access", "http://", "https://",
            "अपलोड करो", "डाउनलोड करो", "नेटवर्क से कनेक्ट", "इंटरनेट से कनेक्ट",
            "network se connect", "internet se connect", "upload karo", "download karo",
        ),
        ActionType.WRITE_FILE: (
            "write file", "save file", "modify file", "edit file", "update file", "overwrite file",
            "फाइल लिखो", "फ़ाइल लिखो", "फाइल में बदलाव", "फ़ाइल में बदलाव",
            "फाइल बदलो", "फ़ाइल बदलो", "फाइल सेव", "फ़ाइल सेव",
            "file likh do", "file badlo", "file mein badlav", "file save karo",
        ),
    }

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
        semantic_intent_brain: SemanticIntentBrain | None = None,
        audit_logger: AuditLogger | None = None,
        tool_project_root: Path | None = None,
    ) -> None:
        self.audit_logger = audit_logger or AuditLogger(
            Path(__file__).resolve().parents[2] / "security" / "audit"
        )
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

        # Advisory cognitive focus only; this engine never grants permission
        # and never suppresses a request or changes execution authority.
        self.attention_engine = AttentionEngine()

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
        child_registry_path = os.environ.get("SAHIBEX_CHILD_REGISTRY_DB")
        child_memory_path = os.environ.get("SAHIBEX_CHILD_MEMORY_DB")
        self.specialist_child_brains = SpecialistChildBrainManager(
            identity_database_path=child_registry_path,
            memory_database_path=child_memory_path,
        )

        # SAHIBEX's own internal army/labor roles live inside the Mother
        # runtime. This registry does not create independent Child Brains;
        # handlers are reported executable only when genuinely registered.
        self.internal_brain_team = InternalBrainTeam()

        # Phase 10: controlled continuous learning and improvement.
        # Production launch scripts configure a durable append-only audit DB.
        # If configured, every proposal/test/approval/activation/rollback
        # decision is persisted and hash-chain checked before being reported.
        # Skill activation remains metadata-only; no arbitrary code executes.
        self.self_improvement_audit_store = None
        self_improvement_audit_path = os.environ.get(
            "SAHIBEX_SELF_IMPROVEMENT_AUDIT_DB"
        )
        if self_improvement_audit_path:
            self.self_improvement_audit_store = ChildSelfImprovementAuditStore(
                self_improvement_audit_path
            )
        self.self_improvement_state_store = None
        self_improvement_state_path = os.environ.get(
            "SAHIBEX_SELF_IMPROVEMENT_STATE_DB"
        )
        if self_improvement_state_path:
            self.self_improvement_state_store = SelfImprovementStateStore(
                self_improvement_state_path
            )
        self.continuous_learning = ContinuousLearningImprovement(
            audit_store=self.self_improvement_audit_store,
            state_store=self.self_improvement_state_store,
        )

        # Phase 11: unified fail-closed security/safety control plane.
        # Existing Constitution, PermissionGateway, verification,
        # audit, sandbox and emergency-stop components remain the
        # authoritative execution boundaries.
        self.emergency_stop = EmergencyStop()
        # Managed process execution is opt-in: no task ledger or worker runtime
        # is created unless the operator configures an explicit database path.
        managed_worker_db = os.environ.get("SAHIBEX_MANAGED_WORKER_DB")
        self.managed_worker_runtime = (
            ManagedWorkerRuntime(managed_worker_db)
            if managed_worker_db else None
        )
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

        # Unified language perception runs before deterministic routing.
        # Only curated high-confidence corrections are automatic; uncertain
        # dictionary matches remain suggestions and never silently rewrite.
        self.input_normalization_engine = InputNormalizationEngine()
        self.perception_language_brain = PerceptionLanguageBrain()
        self.universal_language_brain = UniversalLanguageBrain()
        self.confidence_verification_brain = ConfidenceVerificationBrain()
        self.contextual_input_understanding_brain = None
        language_provider = self.mother_operational.default_provider
        contextual_enabled = os.getenv(
            "SAHIBEX_CONTEXTUAL_INPUT_ENABLED",
            "1" if language_provider == "local" else "0",
        ).strip() == "1"
        if contextual_enabled:
            remote_language_allowed = os.getenv(
                "SAHIBEX_CONTEXTUAL_INPUT_ALLOW_REMOTE", "0"
            ).strip() == "1"
            if language_provider != "mock" and (
                language_provider != "remote" or remote_language_allowed
            ):
                self.contextual_input_understanding_brain = ContextualInputUnderstandingBrain(
                    self.mother_operational.model.gateway,
                    provider=language_provider,
                )

        # Semantic inference defaults on for the local provider, but remains
        # opt-in for remote providers. Mock output is never treated as real
        # semantic understanding; local health checks fail closed when offline.
        self.semantic_intent_brain = semantic_intent_brain
        if self.semantic_intent_brain is None and os.getenv(
            "SAHIBEX_SEMANTIC_INTENT_ENABLED",
            "1" if self.mother_operational.default_provider == "local" else "0",
        ).strip() == "1":
            provider = self.mother_operational.default_provider
            remote_allowed = os.getenv(
                "SAHIBEX_SEMANTIC_INTENT_ALLOW_REMOTE", "0"
            ).strip() == "1"
            if provider != "mock" and (provider != "remote" or remote_allowed):
                self.semantic_intent_brain = SemanticIntentBrain(
                    self.mother_operational.model.gateway,
                    provider=provider,
                )

        self.mother_reasoning = (
            mother_reasoning
            if mother_reasoning is not None
            else MotherReasoningIntegration()
        )

        self.mother_research = (
            mother_research
            if mother_research is not None
            else MotherResearchIntegration(
                storage=self.mother_operational.storage
            )
        )

        # Research/Learning, Operational retrieval, Memory and Knowledge form
        # one data plane. A silently split store can make freshly verified
        # research invisible to retrieval, so default wiring always reuses the
        # exact same storage object (including SQLite :memory: databases).
        if mother_operational is None:
            if self.mother_operational.storage is not self.mother_research.storage:
                self.mother_operational.storage = self.mother_research.storage
                # Keep every nested retrieval component on the same store.
                # Updating only the facade's storage reference leaves its
                # MemoryBrain/KnowledgeBrain instances attached to the old DB.
                memory_knowledge = self.mother_operational.memory_knowledge
                memory_knowledge.storage = self.mother_research.storage
                memory_knowledge.memory_brain.storage = self.mother_research.storage
                memory_knowledge.knowledge_brain.storage = self.mother_research.storage
        else:
            operational_path = self.mother_operational.storage.database_path
            research_path = self.mother_research.storage.database_path
            uses_private_memory_db = (
                str(operational_path) == ":memory:"
                or str(research_path) == ":memory:"
            )
            same_persistent_database = (
                not uses_private_memory_db
                and operational_path.resolve() == research_path.resolve()
            )
            if (
                self.mother_operational.storage is not self.mother_research.storage
                and not same_persistent_database
            ):
                raise ValueError(
                    "MainBrain requires mother_operational and mother_research "
                    "to share one persistent database; pass integrations backed "
                    "by the same database path or omit mother_operational so "
                    "MainBrain can wire the shared store automatically."
                )

        self.mother_learning = (
            mother_learning
            if mother_learning is not None
            else MotherLearningIntegration(
                research=self.mother_research
            )
        )
        if self.mother_learning.research is not self.mother_research:
            raise ValueError(
                "MainBrain requires mother_learning to use the same "
                "mother_research integration instance."
            )

        self.cognitive_neural_architecture = CognitiveNeuralArchitecture()
        self.three_brain_council = ThreeBrainCouncil()
        self.runtime_state = MotherBrainState()
        self.memory_brain = MemoryBrain(storage=self.mother_operational.storage)
        self.knowledge_brain = KnowledgeBrain(storage=self.mother_operational.storage)
        self.research_learning_brain = ResearchLearningBrain(
            research=self.mother_research,
            learning=self.mother_learning,
        )
        self.tool_brain = ToolBrain(
            permission_engine=self.permission,
            emergency_stop=self.emergency_stop,
            project_root=tool_project_root,
            audit_logger=self.audit_logger,
        )
        checkpoint_path = os.getenv("SAHIBEX_AUTONOMOUS_CHECKPOINT_PATH", "").strip()
        self.autonomous_work_brain = AutonomousWorkBrain(
            checkpoint_path=checkpoint_path or None
        )

        # Wire only capabilities that already have concrete, bounded runtime
        # implementations. Other role names remain visibly unwired until a
        # real implementation and regression tests exist.
        self.internal_brain_team.register_handler(
            "reading", self._internal_reading_handler
        )
        self.internal_brain_team.register_handler(
            "document_file", self._internal_document_file_handler
        )
        self.internal_brain_team.register_handler(
            "system_architecture", self._internal_system_architecture_handler
        )
        self.internal_brain_team.register_handler(
            "performance_resource", self._internal_performance_resource_handler
        )
        self.internal_brain_team.register_handler(
            "privacy_data_governance", self._internal_privacy_data_governance_handler
        )
        self.internal_brain_team.register_handler(
            "human_handoff", self._internal_human_handoff_handler
        )
        self.internal_brain_team.register_handler(
            "backup_continuity", self._internal_backup_continuity_handler
        )
        self.internal_brain_team.register_handler(
            "web_tools", self._internal_web_tools_handler
        )
        self.internal_brain_team.register_handler(
            "automation", self._internal_automation_handler
        )
        self.internal_brain_team.register_handler(
            "health_monitor", self._internal_health_monitor_handler
        )
        self.internal_brain_team.register_handler(
            "audit", self._internal_audit_handler
        )
        self.internal_brain_team.register_handler(
            "brain_creator", self._internal_brain_creator_handler
        )
        self.internal_brain_team.register_handler(
            "evaluation", self._internal_evaluation_handler
        )
        self.internal_brain_team.register_handler(
            "personal_assistant", self._internal_personal_assistant_handler
        )
        self.internal_brain_team.register_handler(
            "creative", self._internal_creative_handler
        )
        self.internal_brain_team.register_handler(
            "collaboration", self._internal_collaboration_handler
        )
        self.internal_brain_team.register_handler(
            "finance", self._internal_finance_handler
        )
        self.internal_brain_team.register_handler(
            "localization", self._internal_localization_handler
        )
        self.internal_brain_team.register_handler(
            "accessibility", self._internal_accessibility_handler
        )
        self.internal_brain_team.register_handler(
            "conversation", self._internal_conversation_handler
        )
        self.internal_brain_team.register_handler(
            "policy", self._internal_policy_handler
        )
        self.internal_brain_team.register_handler(
            "personalization", self._internal_personalization_handler
        )
        self.internal_brain_team.register_handler(
            "recovery", self._internal_recovery_handler
        )
        self.internal_brain_team.register_handler(
            "knowledge_graph", self._internal_knowledge_graph_handler
        )
        self.internal_brain_team.register_handler(
            "database", self._internal_database_handler
        )
        self.internal_brain_team.register_handler(
            "scheduling", self._internal_scheduling_handler
        )
        self.internal_brain_team.register_handler(
            "ui_ux_design", self._internal_ui_ux_design_handler
        )
        self.internal_brain_team.register_handler(
            "scientific_research", self._internal_scientific_research_handler
        )
        self.internal_brain_team.register_handler(
            "simulation", self._internal_simulation_handler
        )
        self.internal_brain_team.register_handler(
            "api_integration", self._internal_api_integration_handler
        )
        self.internal_brain_team.register_handler(
            "devops_deployment", self._internal_devops_deployment_handler
        )
        self.internal_brain_team.register_handler(
            "multimodal_coordination", self._internal_multimodal_coordination_handler
        )
        self.internal_brain_team.register_handler(
            "notification_events", self._internal_notification_events_handler
        )
        self.internal_brain_team.register_handler(
            "compliance", self._internal_compliance_handler
        )
        self.internal_brain_team.register_handler(
            "experiment_benchmark", self._internal_experiment_benchmark_handler
        )
        self.internal_brain_team.register_handler(
            "audio", self._internal_audio_handler
        )
        self.internal_brain_team.register_handler(
            "vision", self._internal_vision_handler
        )
        self.internal_brain_team.register_handler(
            "knowledge", self._internal_library_or_knowledge_handler
        )
        self.internal_brain_team.register_handler(
            "voice", self._internal_voice_handler
        )
        self.internal_brain_team.register_handler(
            "language", self._internal_language_handler
        )
        self.internal_brain_team.register_handler(
            "math", self._internal_math_handler
        )
        self.internal_brain_team.register_handler(
            "data_analysis", self._internal_data_analysis_handler
        )
        self.internal_brain_team.register_handler(
            "code_review", self._internal_code_review_handler
        )
        self.internal_brain_team.register_handler(
            "planning", self._internal_planning_handler
        )
        self.internal_brain_team.register_handler(
            "app_builder", self._internal_app_builder_handler
        )
        self.internal_brain_team.register_handler(
            "debugging", self._internal_debugging_handler
        )
        self.internal_brain_team.register_handler(
            "knowledge_maintenance", self._internal_knowledge_maintenance_handler
        )
        self.internal_brain_team.register_handler(
            "decision_analysis", self._internal_decision_analysis_handler
        )
        self.internal_brain_team.register_handler(
            "uncertainty", self._internal_uncertainty_handler
        )
        self.internal_brain_team.register_handler(
            "evidence_fact_checking", self._internal_evidence_fact_checking_handler
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
            "teaching", self._internal_teaching_handler
        )
        self.coding_brain = CodingBrain()
        self.text_development_brain = TextDevelopmentBrain()
        self.test_brain = TestBrain()
        self.library_brain = LibraryBrain()
        self.internal_brain_team.register_handler(
            "text_development", self._internal_text_development_handler
        )
        self.internal_brain_team.register_handler(
            "coding", self._internal_coding_handler
        )
        self.internal_brain_team.register_handler(
            "testing", self._internal_development_testing_handler
        )

    @staticmethod
    def _internal_automation_handler(request: str, context: dict):
        """Validate a bounded proposed workflow; never execute, schedule, or authorize it."""
        steps = context.get("steps")
        if not isinstance(steps, list) or not steps:
            return {"success": False, "status": "WORKFLOW_STEPS_REQUIRED", "validated": False, "executes_steps": False}
        if len(steps) > 30:
            return {"success": False, "status": "STEP_LIMIT_EXCEEDED", "validated": False, "executes_steps": False}
        normalized = []
        seen = set()
        for index, item in enumerate(steps):
            if not isinstance(item, dict):
                return {"success": False, "status": "STEP_FORMAT_INVALID", "step_index": index, "validated": False, "executes_steps": False}
            step_id, description = item.get("id"), item.get("description")
            depends_on = item.get("depends_on", [])
            if not isinstance(step_id, str) or not step_id.strip() or len(step_id.strip()) > 64:
                return {"success": False, "status": "STEP_ID_INVALID_OR_DUPLICATE", "step_index": index, "validated": False, "executes_steps": False}
            step_id = step_id.strip()
            if step_id in seen:
                return {"success": False, "status": "STEP_ID_INVALID_OR_DUPLICATE", "step_index": index, "validated": False, "executes_steps": False}
            if not isinstance(description, str) or not description.strip() or len(description) > 300:
                return {"success": False, "status": "STEP_DESCRIPTION_INVALID", "step_index": index, "validated": False, "executes_steps": False}
            if not isinstance(depends_on, list) or len(depends_on) > 30 or any(not isinstance(dep, str) for dep in depends_on):
                return {"success": False, "status": "DEPENDENCY_FORMAT_INVALID", "step_index": index, "validated": False, "executes_steps": False}
            seen.add(step_id)
            normalized.append({"id": step_id, "description": description.strip(), "depends_on": depends_on})
        ids = {item["id"] for item in normalized}
        for item in normalized:
            if item["id"] in item["depends_on"] or any(dep not in ids for dep in item["depends_on"]):
                return {"success": False, "status": "DEPENDENCY_REFERENCE_INVALID", "step_id": item["id"], "validated": False, "executes_steps": False}
        # Kahn validation: reject cycles without claiming to execute the workflow.
        remaining = {item["id"]: set(item["depends_on"]) for item in normalized}
        order = []
        while remaining:
            ready = sorted(key for key, deps in remaining.items() if not deps)
            if not ready:
                return {"success": False, "status": "DEPENDENCY_CYCLE_DETECTED", "validated": False, "executes_steps": False}
            for key in ready:
                order.append(key)
                remaining.pop(key)
            for deps in remaining.values():
                deps.difference_update(ready)
        return {"success": True, "status": "WORKFLOW_VALIDATED_PROPOSAL_ONLY", "request": request.strip()[:240], "step_count": len(normalized), "proposed_order": order, "steps": normalized, "validated": True, "executes_steps": False, "schedules_work": False, "grants_permissions": False, "user_approval_required_for_actions": True}

    def _internal_health_monitor_handler(self, request: str, context: dict):
        """Read current lifecycle health; do not wake, sleep, or modify the runtime."""
        try:
            status = self.brain_lifecycle.status()
            stopped = bool(self.emergency_stop.engaged)
            health_value = getattr(status.health, "value", str(status.health))
            state_value = getattr(status.state, "value", str(status.state))
            if stopped:
                overall = "CRITICAL"
            elif str(health_value).lower() in {"healthy", "health"}:
                overall = "HEALTHY"
            elif str(health_value).lower() in {"degraded"}:
                overall = "DEGRADED"
            elif str(health_value).lower() in {"critical"}:
                overall = "CRITICAL"
            else:
                overall = "UNKNOWN"
            return {"success": overall != "UNKNOWN", "status": "LIVE_READ_ONLY_HEALTH_SNAPSHOT", "health": overall, "lifecycle_state": state_value, "awake": bool(status.awake), "brain_version": str(status.brain_version), "checkpoint_sequence": int(status.checkpoint_sequence), "emergency_stop_engaged": stopped, "emergency_stop_state": str(getattr(self.emergency_stop.state, "value", self.emergency_stop.state)), "reads_lifecycle": True, "changes_runtime": False, "grants_permissions": False}
        except Exception as exc:
            return {"success": False, "status": "HEALTH_SNAPSHOT_FAILED_CLOSED", "reason_type": type(exc).__name__, "health": "UNKNOWN", "changes_runtime": False, "grants_permissions": False}

    def _internal_audit_handler(self, request: str, context: dict):
        """Return only bounded audit metadata; omit request/reason text to avoid leaking secrets."""
        limit = context.get("limit", 10)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            return {"success": False, "status": "AUDIT_LIMIT_INVALID", "events": [], "writes_audit": False}
        try:
            raw_events = self.audit_logger.read_recent(limit=limit)
            events = []
            for event in raw_events:
                if not isinstance(event, dict):
                    continue
                events.append({key: event[key] for key in ("timestamp", "intent", "intent_confidence", "action", "action_confidence", "risk", "permission", "confirmation_required", "execution_id") if key in event})
            return {"success": True, "status": "REDACTED_AUDIT_METADATA_ONLY", "event_count": len(events), "events": events, "raw_requests_included": False, "reason_text_included": False, "writes_audit": False, "audit_completeness_verified": False}
        except Exception as exc:
            return {"success": False, "status": "AUDIT_READ_FAILED_CLOSED", "reason_type": type(exc).__name__, "events": [], "writes_audit": False}

    def _internal_brain_creator_handler(self, request: str, context: dict):
        """Draft a specialist profile only; registry mutation and child birth are forbidden."""
        role_id = context.get("role_id")
        purpose = context.get("purpose")
        capabilities = context.get("capabilities")
        if not isinstance(role_id, str) or not role_id.strip() or len(role_id.strip()) > 48:
            return {"success": False, "status": "ROLE_ID_REQUIRED_OR_INVALID", "registered": False, "child_created": False}
        role_id = role_id.strip().lower()
        if not all(ch.isalnum() or ch == "_" for ch in role_id) or not role_id[0].isalpha():
            return {"success": False, "status": "ROLE_ID_FORMAT_INVALID", "registered": False, "child_created": False}
        if not isinstance(purpose, str) or not purpose.strip() or len(purpose.strip()) > 400:
            return {"success": False, "status": "PURPOSE_REQUIRED_OR_INVALID", "registered": False, "child_created": False}
        if not isinstance(capabilities, list) or not 1 <= len(capabilities) <= 10 or any(not isinstance(item, str) or not item.strip() or len(item) > 80 for item in capabilities):
            return {"success": False, "status": "CAPABILITIES_REQUIRED_OR_INVALID", "registered": False, "child_created": False}
        from core.brain.specialist_catalogue import get_specialist
        exists = get_specialist(role_id) is not None or role_id in self.internal_brain_team.ROLE_PURPOSES
        return {"success": True, "status": "SPECIALIST_PROFILE_PROPOSAL_ONLY", "proposal": {"role_id": role_id, "purpose": purpose.strip(), "capabilities": list(dict.fromkeys(item.strip() for item in capabilities)), "proposed_by_request": request.strip()[:160]}, "role_id_already_exists": exists, "requires_human_review": True, "registered": False, "creates_child_brain": False, "changes_constitution": False, "grants_permissions": False}

    @staticmethod
    def _internal_evaluation_handler(request: str, context: dict):
        """Evaluate explicit caller-supplied check records, not unseen software or test runs."""
        checks = context.get("checks")
        if not isinstance(checks, list) or not checks:
            return {"success": False, "status": "EVALUATION_CHECKS_REQUIRED", "evaluated": False, "tests_executed": False}
        if len(checks) > 50:
            return {"success": False, "status": "CHECK_LIMIT_EXCEEDED", "evaluated": False, "tests_executed": False}
        normalized = []
        for index, item in enumerate(checks):
            if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"].strip() or not isinstance(item.get("passed"), bool):
                return {"success": False, "status": "CHECK_RECORD_INVALID", "check_index": index, "evaluated": False, "tests_executed": False}
            evidence = item.get("evidence", "")
            if not isinstance(evidence, str) or len(evidence) > 1000:
                return {"success": False, "status": "CHECK_EVIDENCE_INVALID", "check_index": index, "evaluated": False, "tests_executed": False}
            normalized.append({"name": item["name"].strip()[:120], "passed": item["passed"], "evidence_provided": bool(evidence.strip())})
        passed = sum(1 for item in normalized if item["passed"])
        failed = [item["name"] for item in normalized if not item["passed"]]
        missing_evidence = [item["name"] for item in normalized if not item["evidence_provided"]]
        return {"success": not failed and not missing_evidence, "status": "EVALUATION_PASS" if not failed and not missing_evidence else "EVALUATION_INCOMPLETE_OR_FAILED", "request": request.strip()[:240], "checks_count": len(normalized), "passed_count": passed, "failed_count": len(failed), "failed_checks": failed, "checks_missing_evidence": missing_evidence, "checks": normalized, "evaluated": True, "tests_executed": False, "external_state_inspected": False, "claim_scope": "caller-supplied check records only"}

    @staticmethod
    def _internal_personal_assistant_handler(request: str, context: dict):
        """Organize supplied tasks into a proposed checklist; do not perform them."""
        tasks = context.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            return {"success": False, "status": "TASK_LIST_REQUIRED", "executes_tasks": False}
        if len(tasks) > 25:
            return {"success": False, "status": "TASK_LIMIT_EXCEEDED", "executes_tasks": False}
        normalized = []
        seen = set()
        for i, item in enumerate(tasks):
            if not isinstance(item, dict):
                return {"success": False, "status": "TASK_FORMAT_INVALID", "task_index": i, "executes_tasks": False}
            title = item.get("title")
            task_id = item.get("id", f"task-{i + 1}")
            priority = item.get("priority", "normal")
            if not isinstance(title, str) or not title.strip() or len(title) > 240:
                return {"success": False, "status": "TASK_TITLE_INVALID", "task_index": i, "executes_tasks": False}
            if not isinstance(task_id, str) or not task_id.strip() or task_id.strip() in seen:
                return {"success": False, "status": "TASK_ID_INVALID_OR_DUPLICATE", "task_index": i, "executes_tasks": False}
            if priority not in {"low", "normal", "high", "urgent"}:
                return {"success": False, "status": "TASK_PRIORITY_INVALID", "task_index": i, "executes_tasks": False}
            seen.add(task_id.strip())
            normalized.append({"id": task_id.strip(), "title": title.strip(), "priority": priority, "requires_user_approval": bool(item.get("requires_user_approval", False))})
        rank = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        normalized.sort(key=lambda item: (rank[item["priority"]], item["id"]))
        return {"success": True, "status": "PERSONAL_TASK_CHECKLIST_PROPOSED", "request": request.strip()[:200], "task_count": len(normalized), "tasks": normalized, "executes_tasks": False, "contacts_external_services": False, "creates_calendar_events": False, "user_remains_in_control": True}

    @staticmethod
    def _internal_creative_handler(request: str, context: dict):
        """Produce a structured brief and bounded idea seeds from explicit creative input."""
        topic = context.get("topic")
        if not isinstance(topic, str) or not topic.strip() or len(topic) > 500:
            return {"success": False, "status": "CREATIVE_TOPIC_REQUIRED", "generated_final_artifact": False}
        style = context.get("style", "clear and original")
        audience = context.get("audience", "unspecified audience")
        constraints = context.get("constraints", [])
        if not isinstance(style, str) or not style.strip() or len(style) > 120 or not isinstance(audience, str) or len(audience) > 120:
            return {"success": False, "status": "CREATIVE_BRIEF_FIELD_INVALID", "generated_final_artifact": False}
        if not isinstance(constraints, list) or len(constraints) > 12 or any(not isinstance(x, str) or len(x) > 160 for x in constraints):
            return {"success": False, "status": "CREATIVE_CONSTRAINTS_INVALID", "generated_final_artifact": False}
        clean_topic = topic.strip()
        return {"success": True, "status": "CREATIVE_BRIEF_AND_IDEA_SEEDS", "brief": {"topic": clean_topic, "style": style.strip(), "audience": audience.strip() or "unspecified audience", "constraints": [x.strip() for x in constraints]}, "idea_seeds": [f"Explore the central problem behind: {clean_topic}", f"Show a concrete before-and-after for: {clean_topic}", f"Challenge one common assumption about: {clean_topic}"], "generated_final_artifact": False, "requires_human_selection_and_revision": True, "executes_external_actions": False}

    @staticmethod
    def _internal_collaboration_handler(request: str, context: dict):
        """Aggregate supplied reports and expose disagreement without deciding truth."""
        reports = context.get("reports")
        if not isinstance(reports, list) or not reports:
            return {"success": False, "status": "SPECIALIST_REPORTS_REQUIRED", "conflicts_resolved": False}
        if len(reports) > 30:
            return {"success": False, "status": "REPORT_LIMIT_EXCEEDED", "conflicts_resolved": False}
        clean = []
        by_claim = {}
        for i, report in enumerate(reports):
            if not isinstance(report, dict):
                return {"success": False, "status": "REPORT_FORMAT_INVALID", "report_index": i, "conflicts_resolved": False}
            specialist = report.get("specialist")
            claim_id = report.get("claim_id")
            conclusion = report.get("conclusion")
            evidence = report.get("evidence", "")
            if any(not isinstance(v, str) or not v.strip() for v in (specialist, claim_id, conclusion)) or not isinstance(evidence, str) or len(evidence) > 1200:
                return {"success": False, "status": "REPORT_FIELD_INVALID", "report_index": i, "conflicts_resolved": False}
            row = {"specialist": specialist.strip()[:80], "claim_id": claim_id.strip()[:100], "conclusion": conclusion.strip()[:400], "evidence_provided": bool(evidence.strip())}
            clean.append(row)
            by_claim.setdefault(row["claim_id"], set()).add(row["conclusion"].casefold())
        conflicts = sorted(key for key, conclusions in by_claim.items() if len(conclusions) > 1)
        return {"success": True, "status": "REPORTS_AGGREGATED_WITH_CONFLICTS_EXPOSED" if conflicts else "REPORTS_AGGREGATED_NO_EXPLICIT_CONFLICT", "report_count": len(clean), "reports": clean, "conflicting_claim_ids": conflicts, "conflicts_resolved": False, "truth_verified": False, "requires_verification_or_human_decision": bool(conflicts), "external_actions_executed": False}

    @staticmethod
    def _internal_finance_handler(request: str, context: dict):
        """Summarize supplied cash-flow values; never move money or recommend investments."""
        income = context.get("income")
        expenses = context.get("expenses")
        if not isinstance(income, (int, float)) or isinstance(income, bool) or not math.isfinite(float(income)) or income < 0:
            return {"success": False, "status": "VALID_NONNEGATIVE_INCOME_REQUIRED", "financial_action_taken": False}
        if not isinstance(expenses, list) or len(expenses) > 100 or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(float(v)) or v < 0 for v in expenses):
            return {"success": False, "status": "VALID_EXPENSE_LIST_REQUIRED", "financial_action_taken": False}
        total_expenses = sum(float(v) for v in expenses)
        net = float(income) - total_expenses
        savings_rate = (net / float(income) * 100.0) if income else None
        return {"success": True, "status": "SUPPLIED_CASHFLOW_SUMMARY_NOT_FINANCIAL_ADVICE", "currency": str(context.get("currency", "unspecified"))[:12], "income": float(income), "expense_count": len(expenses), "total_expenses": round(total_expenses, 2), "net_cashflow": round(net, 2), "net_cashflow_status": "SURPLUS" if net > 0 else "BREAK_EVEN" if net == 0 else "DEFICIT", "net_as_percent_of_income": round(savings_rate, 2) if savings_rate is not None else None, "financial_action_taken": False, "investment_or_credit_recommendation": False, "external_data_used": False}

    @staticmethod
    def _internal_localization_handler(request: str, context: dict):
        """Check supplied translation coverage and interpolation tokens, not translation accuracy."""
        locale = context.get("locale")
        source = context.get("source_strings")
        translated = context.get("translated_strings")
        if not isinstance(locale, str) or not locale.strip() or len(locale) > 40:
            return {"success": False, "status": "TARGET_LOCALE_REQUIRED", "translation_quality_verified": False}
        if not isinstance(source, dict) or not source or len(source) > 200 or not isinstance(translated, dict):
            return {"success": False, "status": "SOURCE_AND_TRANSLATION_MAPS_REQUIRED", "translation_quality_verified": False}
        if any(not isinstance(k, str) or not k.strip() or not isinstance(v, str) for k, v in source.items()):
            return {"success": False, "status": "SOURCE_STRING_FORMAT_INVALID", "translation_quality_verified": False}
        missing = sorted(k for k in source if not isinstance(translated.get(k), str) or not translated.get(k, "").strip())
        placeholder_mismatch = []
        for key, value in source.items():
            target = translated.get(key)
            if not isinstance(target, str) or not target.strip():
                continue
            source_tokens = sorted(part.split("}", 1)[0] for part in value.split("{")[1:] if "}" in part)
            target_tokens = sorted(part.split("}", 1)[0] for part in target.split("{")[1:] if "}" in part)
            if source_tokens != target_tokens:
                placeholder_mismatch.append(key)
        return {"success": not missing and not placeholder_mismatch, "status": "LOCALIZATION_COVERAGE_CHECKED_NOT_TRANSLATION_VERIFIED" if not missing and not placeholder_mismatch else "LOCALIZATION_GAPS_FOUND", "locale": locale.strip(), "source_count": len(source), "missing_translation_keys": missing, "placeholder_mismatch_keys": placeholder_mismatch, "translation_quality_verified": False, "machine_translation_performed": False}

    @staticmethod
    def _internal_accessibility_handler(request: str, context: dict):
        """Review explicitly supplied component metadata; no live UI inspection is implied."""
        components = context.get("components")
        if not isinstance(components, list) or not components:
            return {"success": False, "status": "UI_COMPONENT_METADATA_REQUIRED", "live_ui_inspected": False}
        if len(components) > 100:
            return {"success": False, "status": "COMPONENT_LIMIT_EXCEEDED", "live_ui_inspected": False}
        findings = []
        for index, item in enumerate(components):
            if not isinstance(item, dict) or not isinstance(item.get("type"), str) or not item["type"].strip():
                return {"success": False, "status": "COMPONENT_RECORD_INVALID", "component_index": index, "live_ui_inspected": False}
            kind = item["type"].strip().lower()
            issues = []
            if kind in {"button", "input", "link", "select", "checkbox"} and not (isinstance(item.get("label"), str) and item["label"].strip()):
                issues.append("accessible_label_missing")
            if kind == "image" and not (isinstance(item.get("alt_text"), str) and item["alt_text"].strip()):
                issues.append("alt_text_missing")
            for field in ("keyboard_operable", "visible_focus", "contrast_checked"):
                if item.get(field) is not True:
                    issues.append(f"{field}_not_confirmed")
            findings.append({"component": item.get("id", f"component-{index + 1}"), "type": kind, "issues": issues, "status": "REVIEW_REQUIRED" if issues else "SUPPLIED_METADATA_CHECKS_OK"})
        issue_count = sum(len(item["issues"]) for item in findings)
        return {"success": True, "status": "ACCESSIBILITY_METADATA_REVIEW_NOT_WCAG_CERTIFICATION", "component_count": len(findings), "issue_count": issue_count, "findings": findings, "live_ui_inspected": False, "wcag_conformance_certified": False}

    @staticmethod
    def _internal_conversation_handler(request: str, context: dict):
        """Extract the latest explicit user turn from supplied bounded history."""
        messages = context.get("messages")
        if not isinstance(messages, list) or not messages:
            return {"success": False, "status": "CONVERSATION_MESSAGES_REQUIRED", "history_read": False}
        if len(messages) > 30:
            return {"success": False, "status": "MESSAGE_LIMIT_EXCEEDED", "history_read": False}
        clean = []
        for i, item in enumerate(messages):
            if not isinstance(item, dict) or item.get("role") not in {"user", "assistant", "system"} or not isinstance(item.get("content"), str) or len(item["content"]) > 4000:
                return {"success": False, "status": "MESSAGE_FORMAT_INVALID", "message_index": i, "history_read": False}
            clean.append({"role": item["role"], "content": item["content"].strip()})
        latest_user = next((item["content"] for item in reversed(clean) if item["role"] == "user" and item["content"]), None)
        return {"success": latest_user is not None, "status": "LATEST_EXPLICIT_USER_TURN_EXTRACTED" if latest_user else "NO_NONEMPTY_USER_TURN", "latest_user_request": latest_user, "message_count": len(clean), "history_read": True, "history_persisted": False, "intent_inferred": False}

    @staticmethod
    def _internal_policy_handler(request: str, context: dict):
        """Match caller-supplied policy rules; unmatched requests require review."""
        target = context.get("target_request")
        rules = context.get("rules")
        if not isinstance(target, str) or not target.strip() or len(target) > 4000 or not isinstance(rules, list) or len(rules) > 50:
            return {"success": False, "status": "TARGET_REQUEST_AND_RULES_REQUIRED", "decision": "REVIEW_REQUIRED", "grants_permission": False}
        matches = []
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict) or not isinstance(rule.get("rule_id"), str) or not isinstance(rule.get("terms"), list) or not rule["terms"] or any(not isinstance(term, str) or not term.strip() for term in rule["terms"]):
                return {"success": False, "status": "POLICY_RULE_INVALID", "rule_index": i, "decision": "REVIEW_REQUIRED", "grants_permission": False}
            outcome = rule.get("outcome", "review")
            if outcome not in {"deny", "review", "allow"}:
                return {"success": False, "status": "POLICY_OUTCOME_INVALID", "rule_index": i, "decision": "REVIEW_REQUIRED", "grants_permission": False}
            if any(term.casefold() in target.casefold() for term in rule["terms"]):
                matches.append({"rule_id": rule["rule_id"][:100], "outcome": outcome})
        if any(item["outcome"] == "deny" for item in matches):
            decision = "DENY_RECOMMENDED"
        elif any(item["outcome"] == "review" for item in matches) or not matches:
            decision = "REVIEW_REQUIRED"
        else:
            decision = "NO_DENY_MATCH_FOUND"
        return {"success": True, "status": "SUPPLIED_POLICY_RULES_EVALUATED_NOT_AUTHORIZATION", "decision": decision, "matched_rules": matches, "grants_permission": False, "executes_action": False, "unmatched_defaults_to_review": not matches}

    @staticmethod
    def _internal_personalization_handler(request: str, context: dict):
        """Validate explicit preferences for this task only; do not save profile state."""
        preferences = context.get("preferences")
        if not isinstance(preferences, dict) or not preferences or len(preferences) > 10:
            return {"success": False, "status": "TASK_PREFERENCES_REQUIRED", "persisted": False}
        allowed = {"language", "tone", "detail", "format", "accessibility"}
        clean = {}
        for key, value in preferences.items():
            if key not in allowed or not isinstance(value, str) or not value.strip() or len(value) > 120:
                return {"success": False, "status": "PREFERENCE_FIELD_INVALID", "persisted": False}
            clean[key] = value.strip()
        return {"success": True, "status": "TASK_SCOPED_PREFERENCES_NORMALIZED", "preferences": clean, "scope": "current_task_only", "persisted": False, "cross_user_sharing": False, "overrides_user_request": False}

    @staticmethod
    def _internal_recovery_handler(request: str, context: dict):
        """Assess explicit recovery prerequisites; never execute restore or rollback."""
        evidence = context.get("evidence")
        if not isinstance(evidence, dict):
            return {"success": False, "status": "RECOVERY_EVIDENCE_REQUIRED", "restore_executed": False}
        required = ("backup_verified", "checkpoint_verified", "restore_drill_passed")
        values = {key: evidence.get(key) for key in required}
        invalid = [key for key, value in values.items() if not isinstance(value, bool)]
        if invalid:
            return {"success": False, "status": "RECOVERY_EVIDENCE_INCOMPLETE", "invalid_or_missing_fields": invalid, "restore_executed": False}
        ready = all(values.values())
        return {"success": True, "status": "RECOVERY_PREREQUISITES_MET" if ready else "RECOVERY_BLOCKED_UNVERIFIED_PREREQUISITES", "prerequisites": values, "restore_ready": ready, "restore_executed": False, "rollback_executed": False, "deletes_files": False, "user_approval_required_for_restore": True}

    @staticmethod
    def _internal_knowledge_graph_handler(request: str, context: dict):
        """Validate supplied triples and flag conflicting objects for identical subject/predicate pairs."""
        triples = context.get("triples")
        if not isinstance(triples, list) or not triples:
            return {"success": False, "status": "KNOWLEDGE_TRIPLES_REQUIRED", "persisted": False}
        if len(triples) > 500:
            return {"success": False, "status": "TRIPLE_LIMIT_EXCEEDED", "persisted": False}
        clean = []
        objects_by_edge = {}
        for i, item in enumerate(triples):
            if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip() for k in ("subject", "predicate", "object")):
                return {"success": False, "status": "TRIPLE_FORMAT_INVALID", "triple_index": i, "persisted": False}
            row = {k: item[k].strip()[:240] for k in ("subject", "predicate", "object")}
            row["source"] = item.get("source", "")[:240] if isinstance(item.get("source", ""), str) else ""
            clean.append(row)
            key = (row["subject"].casefold(), row["predicate"].casefold())
            objects_by_edge.setdefault(key, set()).add(row["object"].casefold())
        conflicts = [{"subject": key[0], "predicate": key[1], "distinct_object_count": len(values)} for key, values in objects_by_edge.items() if len(values) > 1]
        return {"success": True, "status": "GRAPH_TRIPLES_VALIDATED_WITH_CONFLICTS" if conflicts else "GRAPH_TRIPLES_VALIDATED_NO_EXPLICIT_CONFLICT", "triple_count": len(clean), "triples": clean, "conflicting_edges": conflicts, "persisted": False, "truth_verified": False}

    @staticmethod
    def _internal_database_handler(request: str, context: dict):
        """Review caller-supplied schema metadata; no database connections or migrations."""
        tables = context.get("tables")
        if not isinstance(tables, list) or not tables or len(tables) > 50:
            return {"success": False, "status": "SCHEMA_TABLES_REQUIRED", "database_accessed": False}
        names = set()
        findings = []
        for i, table in enumerate(tables):
            if not isinstance(table, dict) or not isinstance(table.get("name"), str) or not table["name"].strip() or not isinstance(table.get("columns"), list) or not table["columns"] or len(table["columns"]) > 100:
                return {"success": False, "status": "SCHEMA_TABLE_INVALID", "table_index": i, "database_accessed": False}
            name = table["name"].strip()
            columns = table["columns"]
            if name.casefold() in names:
                findings.append({"table": name, "issue": "duplicate_table_name"})
            names.add(name.casefold())
            if any(not isinstance(col, str) or not col.strip() for col in columns):
                return {"success": False, "status": "SCHEMA_COLUMN_INVALID", "table": name, "database_accessed": False}
            folded = [col.strip().casefold() for col in columns]
            if len(folded) != len(set(folded)):
                findings.append({"table": name, "issue": "duplicate_column_name"})
            findings.append({"table": name, "column_count": len(columns), "issue": "structure_review_only"})
        return {"success": True, "status": "SCHEMA_METADATA_REVIEW_ONLY", "table_count": len(tables), "findings": findings, "database_accessed": False, "queries_executed": False, "migrations_executed": False}

    @staticmethod
    def _internal_scheduling_handler(request: str, context: dict):
        """Compute a proposed relative schedule from task durations and dependencies."""
        tasks = context.get("tasks")
        if not isinstance(tasks, list) or not tasks or len(tasks) > 30:
            return {"success": False, "status": "SCHEDULING_TASKS_REQUIRED_OR_LIMIT_EXCEEDED", "calendar_written": False}
        by_id = {}
        for i, task in enumerate(tasks):
            if not isinstance(task, dict) or not isinstance(task.get("id"), str) or not task["id"].strip() or task["id"].strip() in by_id:
                return {"success": False, "status": "SCHEDULE_TASK_ID_INVALID", "task_index": i, "calendar_written": False}
            duration = task.get("duration_minutes")
            deps = task.get("depends_on", [])
            if not isinstance(duration, int) or isinstance(duration, bool) or not 1 <= duration <= 1440 or not isinstance(deps, list) or len(deps) > 30 or any(not isinstance(dep, str) for dep in deps):
                return {"success": False, "status": "SCHEDULE_TASK_FIELDS_INVALID", "task_index": i, "calendar_written": False}
            by_id[task["id"].strip()] = {"duration_minutes": duration, "depends_on": deps}
        for key, task in by_id.items():
            if any(dep not in by_id or dep == key for dep in task["depends_on"]):
                return {"success": False, "status": "SCHEDULE_DEPENDENCY_INVALID", "task_id": key, "calendar_written": False}
        remaining = set(by_id)
        finish = {}
        schedule = []
        while remaining:
            ready = sorted(key for key in remaining if all(dep in finish for dep in by_id[key]["depends_on"]))
            if not ready:
                return {"success": False, "status": "SCHEDULE_DEPENDENCY_CYCLE", "calendar_written": False}
            for key in ready:
                start = max((finish[dep] for dep in by_id[key]["depends_on"]), default=0)
                end = start + by_id[key]["duration_minutes"]
                finish[key] = end
                schedule.append({"id": key, "start_minute": start, "end_minute": end, "duration_minutes": by_id[key]["duration_minutes"]})
                remaining.remove(key)
        return {"success": True, "status": "RELATIVE_SCHEDULE_PROPOSED", "tasks": schedule, "total_duration_minutes": max(finish.values(), default=0), "calendar_written": False, "notifications_sent": False, "executes_tasks": False}

    @staticmethod
    def _internal_ui_ux_design_handler(request: str, context: dict):
        """Review supplied interface requirements without claiming visual inspection."""
        screens = context.get("screens")
        if not isinstance(screens, list) or not screens or len(screens) > 40:
            return {"success": False, "status": "SCREEN_REQUIREMENTS_REQUIRED_OR_LIMIT_EXCEEDED", "live_ui_inspected": False}
        findings = []
        for i, screen in enumerate(screens):
            if not isinstance(screen, dict) or not isinstance(screen.get("name"), str) or not screen["name"].strip():
                return {"success": False, "status": "SCREEN_RECORD_INVALID", "screen_index": i, "live_ui_inspected": False}
            missing = []
            for field in ("primary_action", "empty_state", "error_state", "loading_state"):
                if not isinstance(screen.get(field), str) or not screen[field].strip():
                    missing.append(field)
            findings.append({"screen": screen["name"].strip()[:120], "missing_states_or_actions": missing, "status": "GAPS_FOUND" if missing else "REQUIREMENTS_COMPLETE_FOR_CHECKED_FIELDS"})
        gap_count = sum(len(item["missing_states_or_actions"]) for item in findings)
        return {"success": True, "status": "UI_UX_REQUIREMENTS_REVIEW_NOT_USABILITY_TEST", "screen_count": len(findings), "gap_count": gap_count, "findings": findings, "live_ui_inspected": False, "usability_test_executed": False}

    @staticmethod
    def _internal_scientific_research_handler(request: str, context: dict):
        """Structure a research proposal from supplied inputs, never fabricate results or citations."""
        hypothesis = context.get("hypothesis")
        variables = context.get("variables")
        method = context.get("method")
        if not isinstance(hypothesis, str) or not hypothesis.strip() or len(hypothesis) > 1000 or not isinstance(variables, list) or not variables or len(variables) > 20 or any(not isinstance(v, str) or not v.strip() for v in variables) or not isinstance(method, str) or not method.strip() or len(method) > 500:
            return {"success": False, "status": "HYPOTHESIS_VARIABLES_AND_METHOD_REQUIRED", "findings_generated": False}
        outcomes = context.get("outcomes", [])
        if not isinstance(outcomes, list) or len(outcomes) > 20 or any(not isinstance(v, str) or not v.strip() for v in outcomes):
            return {"success": False, "status": "OUTCOME_LIST_INVALID", "findings_generated": False}
        return {"success": True, "status": "RESEARCH_PLAN_STRUCTURED_NOT_VALIDATED", "hypothesis": hypothesis.strip(), "variables": [v.strip()[:160] for v in variables], "method": method.strip(), "planned_outcomes": [v.strip()[:160] for v in outcomes], "recommended_checks": ["define operational measures", "identify confounders", "predefine analysis and stopping criteria", "document limitations and replication steps"], "findings_generated": False, "citations_fabricated": False, "ethics_or_safety_review_completed": False}

    @staticmethod
    def _internal_simulation_handler(request: str, context: dict):
        """Evaluate deterministic y = baseline * multiplier + offset scenarios only."""
        baseline = context.get("baseline")
        scenarios = context.get("scenarios")
        if not isinstance(baseline, (int, float)) or isinstance(baseline, bool) or not math.isfinite(float(baseline)) or not isinstance(scenarios, list) or not scenarios or len(scenarios) > 50:
            return {"success": False, "status": "FINITE_BASELINE_AND_SCENARIOS_REQUIRED", "real_world_actions": False}
        results = []
        for i, scenario in enumerate(scenarios):
            if not isinstance(scenario, dict) or not isinstance(scenario.get("name"), str) or not scenario["name"].strip():
                return {"success": False, "status": "SCENARIO_RECORD_INVALID", "scenario_index": i, "real_world_actions": False}
            multiplier, offset = scenario.get("multiplier", 1.0), scenario.get("offset", 0.0)
            if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(float(v)) for v in (multiplier, offset)):
                return {"success": False, "status": "SCENARIO_PARAMETER_INVALID", "scenario_index": i, "real_world_actions": False}
            value = float(baseline) * float(multiplier) + float(offset)
            if not math.isfinite(value):
                return {"success": False, "status": "SCENARIO_RESULT_NONFINITE", "scenario_index": i, "real_world_actions": False}
            results.append({"name": scenario["name"].strip()[:120], "multiplier": float(multiplier), "offset": float(offset), "result": value})
        return {"success": True, "status": "DETERMINISTIC_WHAT_IF_RESULTS", "equation": "result = baseline * multiplier + offset", "baseline": float(baseline), "results": results, "real_world_actions": False, "predictive_accuracy_claimed": False, "assumptions_supplied_by_caller": True}

    @staticmethod
    def _internal_api_integration_handler(request: str, context: dict):
        """Validate API proposal metadata only; never access network or credentials."""
        endpoint = context.get("endpoint")
        method = context.get("method")
        if not isinstance(endpoint, str) or not endpoint.strip() or len(endpoint) > 1000 or method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            return {"success": False, "status": "API_ENDPOINT_AND_METHOD_REQUIRED", "network_called": False}
        auth_mode = context.get("auth_mode", "not_specified")
        if not isinstance(auth_mode, str) or len(auth_mode) > 80:
            return {"success": False, "status": "API_AUTH_MODE_INVALID", "network_called": False}
        return {"success": True, "status": "API_INTEGRATION_PROPOSAL_ONLY", "endpoint": endpoint.strip(), "method": method, "auth_mode": auth_mode, "request_schema_supplied": isinstance(context.get("request_schema"), dict), "response_schema_supplied": isinstance(context.get("response_schema"), dict), "network_called": False, "credentials_read": False, "request_sent": False, "permission_granted": False, "requires_security_and_permission_review": True}

    @staticmethod
    def _internal_devops_deployment_handler(request: str, context: dict):
        """Review explicit release prerequisites; no build, deploy or rollback execution."""
        checks = context.get("checks")
        if not isinstance(checks, dict):
            return {"success": False, "status": "DEPLOYMENT_CHECKS_REQUIRED", "deployment_executed": False}
        required = ("tests_passed", "artifact_verified", "approval_granted", "rollback_plan_ready")
        invalid = [key for key in required if not isinstance(checks.get(key), bool)]
        if invalid:
            return {"success": False, "status": "DEPLOYMENT_CHECKS_INCOMPLETE", "missing_or_invalid": invalid, "deployment_executed": False}
        ready = all(checks[key] for key in required)
        return {"success": True, "status": "RELEASE_PREREQUISITES_MET" if ready else "RELEASE_BLOCKED", "checks": {key: checks[key] for key in required}, "deployment_ready": ready, "deployment_executed": False, "rollback_executed": False, "system_changed": False}

    @staticmethod
    def _internal_multimodal_coordination_handler(request: str, context: dict):
        """Normalize caller-supplied observations without asserting semantic verification."""
        observations = context.get("observations")
        if not isinstance(observations, list) or not observations or len(observations) > 60:
            return {"success": False, "status": "MULTIMODAL_OBSERVATIONS_REQUIRED", "observations_verified": False}
        clean = []
        for i, item in enumerate(observations):
            if not isinstance(item, dict) or item.get("modality") not in {"text", "image", "audio"} or not isinstance(item.get("content"), str) or not item["content"].strip() or len(item["content"]) > 3000:
                return {"success": False, "status": "OBSERVATION_FORMAT_INVALID", "observation_index": i, "observations_verified": False}
            source = item.get("source", "")
            if not isinstance(source, str) or len(source) > 240:
                return {"success": False, "status": "OBSERVATION_SOURCE_INVALID", "observation_index": i, "observations_verified": False}
            clean.append({"modality": item["modality"], "content": item["content"].strip(), "source": source, "trusted": False})
        return {"success": True, "status": "MULTIMODAL_OBSERVATIONS_NORMALIZED_UNTRUSTED", "observation_count": len(clean), "modalities_present": sorted({item["modality"] for item in clean}), "observations": clean, "observations_verified": False, "cross_modal_consistency_verified": False}

    @staticmethod
    def _internal_notification_events_handler(request: str, context: dict):
        """Validate event drafts only; do not deliver, schedule, or contact services."""
        events = context.get("events")
        if not isinstance(events, list) or not events or len(events) > 50:
            return {"success": False, "status": "NOTIFICATION_EVENTS_REQUIRED", "notifications_sent": False}
        clean = []
        for i, event in enumerate(events):
            if not isinstance(event, dict) or not isinstance(event.get("title"), str) or not event["title"].strip() or len(event["title"]) > 160:
                return {"success": False, "status": "EVENT_TITLE_INVALID", "event_index": i, "notifications_sent": False}
            when = event.get("when", "")
            if not isinstance(when, str) or len(when) > 100:
                return {"success": False, "status": "EVENT_TIME_INVALID", "event_index": i, "notifications_sent": False}
            clean.append({"title": event["title"].strip(), "when": when, "time_validated": False})
        return {"success": True, "status": "NOTIFICATION_EVENT_DRAFTS_VALIDATED", "event_count": len(clean), "events": clean, "notifications_sent": False, "events_scheduled": False, "delivery_verified": False}

    @staticmethod
    def _internal_compliance_handler(request: str, context: dict):
        """Map supplied requirement evidence without claiming legal or regulatory certification."""
        requirements = context.get("requirements")
        if not isinstance(requirements, list) or not requirements or len(requirements) > 100:
            return {"success": False, "status": "COMPLIANCE_REQUIREMENTS_REQUIRED", "certified": False}
        results = []
        for i, item in enumerate(requirements):
            if not isinstance(item, dict) or not isinstance(item.get("requirement"), str) or not item["requirement"].strip():
                return {"success": False, "status": "REQUIREMENT_RECORD_INVALID", "requirement_index": i, "certified": False}
            evidence = item.get("evidence")
            status = "UNVERIFIED" if evidence is None or evidence == "" else "EVIDENCE_SUPPLIED_REQUIRES_REVIEW" if isinstance(evidence, str) else "EVIDENCE_FORMAT_INVALID"
            results.append({"requirement": item["requirement"].strip()[:240], "status": status, "evidence_present": isinstance(evidence, str) and bool(evidence.strip())})
        return {"success": True, "status": "COMPLIANCE_EVIDENCE_MAPPED_NOT_CERTIFIED", "requirement_count": len(results), "results": results, "certified": False, "legal_advice": False}

    @staticmethod
    def _internal_experiment_benchmark_handler(request: str, context: dict):
        """Compare supplied finite measurements; no benchmark is run by this handler."""
        measurements = context.get("measurements")
        if not isinstance(measurements, list) or not measurements or len(measurements) > 100:
            return {"success": False, "status": "BENCHMARK_MEASUREMENTS_REQUIRED", "experiments_executed": False}
        clean = []
        for i, item in enumerate(measurements):
            if not isinstance(item, dict) or any(not isinstance(item.get(key), str) or not item[key].strip() for key in ("system", "metric")):
                return {"success": False, "status": "BENCHMARK_RECORD_INVALID", "measurement_index": i, "experiments_executed": False}
            value = item.get("value")
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
                return {"success": False, "status": "BENCHMARK_VALUE_INVALID", "measurement_index": i, "experiments_executed": False}
            clean.append({"system": item["system"].strip()[:100], "metric": item["metric"].strip()[:100], "value": float(value), "unit": str(item.get("unit", "unspecified"))[:40], "evidence": str(item.get("evidence", ""))[:300]})
        groups = {}
        for item in clean:
            groups.setdefault(item["metric"], []).append(item)
        summaries = [{"metric": metric, "systems": sorted(group, key=lambda item: item["value"]), "spread": max(item["value"] for item in group) - min(item["value"] for item in group)} for metric, group in sorted(groups.items())]
        return {"success": True, "status": "SUPPLIED_BENCHMARKS_COMPARED_NOT_REPRODUCED", "measurement_count": len(clean), "metric_summaries": summaries, "experiments_executed": False, "reproducibility_verified": False, "best_system_claimed": False}

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

    @staticmethod
    def _internal_teaching_handler(request: str, context: dict):
        """Create a bounded lesson outline; does not browse or claim fact-checking."""
        topic = context.get("topic", request)
        if not isinstance(topic, str) or not topic.strip():
            return {
                "success": False,
                "status": "TOPIC_REQUIRED",
                "factual_verification": False,
                "external_research_performed": False,
            }
        topic = topic.strip()[:240]
        language = context.get("language", "auto")
        if not isinstance(language, str) or language.lower() not in {"auto", "en", "english", "hi", "hindi"}:
            language = "auto"
        level = context.get("level", "beginner")
        if not isinstance(level, str) or level.lower() not in {"beginner", "intermediate", "advanced"}:
            level = "beginner"
        return {
            "success": True,
            "status": "LESSON_OUTLINE_ONLY",
            "topic": topic,
            "language_requested": language.lower(),
            "level": level.lower(),
            "lesson": [
                {"step": 1, "title": "Core idea", "instruction": f"Explain the central idea of {topic} in plain language."},
                {"step": 2, "title": "Break it down", "instruction": "Introduce the key parts one at a time and define unfamiliar terms."},
                {"step": 3, "title": "Worked example", "instruction": f"Give one concrete, clearly labelled example of {topic}."},
                {"step": 4, "title": "Check understanding", "instruction": "Ask one short question and wait for the learner's answer."},
            ],
            "factual_verification": False,
            "external_research_performed": False,
            "executes_tools": False,
            "writes_files": False,
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
        decision_context = context.get("decision_context", {})
        if not isinstance(decision_context, dict):
            decision_context = {}
        result = self.mother_reasoning.analyze_approved_request(
            user_input=request,
            intent=intent,
            action=action,
            decision_context=decision_context,
        )
        quality = assess_answer(request, result.reasoning_response)
        return {
            "success": result.success,
            "response": result.reasoning_response,
            "status": "STRUCTURALLY_VALID" if quality.acceptable else "QUALITY_REJECTED",
            "quality_reasons": quality.reasons,
            "factual_verification": False,
            "decision_context": result.context_summary,
            "reasoning_assessment": result.reasoning_assessment,
            "_reasoning_result": result,
        }

    def _internal_development_testing_handler(self, request: str, context: dict):
        """Validate queued candidates statically; preserve legacy test-report analysis."""
        candidate = context.get("candidate")
        if candidate is None:
            return self._internal_testing_handler(request, context)
        if not isinstance(candidate, dict):
            return {"success": False, "status": "CANDIDATE_REQUIRED", "promotion_allowed": False, "executes_code": False}
        return self.test_brain.validate_candidate(candidate)

    def _internal_library_or_knowledge_handler(self, request: str, context: dict):
        """Expose local library catalogue through the existing knowledge role."""
        operation = context.get("library_operation")
        if operation is None:
            return self._internal_knowledge_handler(request, context)
        if operation == "index":
            return self.library_brain.index_local_file(
                context.get("path", ""), title=context.get("title", ""),
                category=context.get("category", "general"),
                source=context.get("source", "local_user_library"),
                license_status=context.get("license_status", "UNKNOWN"),
            )
        if operation == "list":
            return self.library_brain.list_entries(category=context.get("category"))
        return {"success": False, "status": "LIBRARY_OPERATION_NOT_ALLOWED", "network_used": False}

    def _internal_text_development_handler(self, request: str, context: dict):
        """Queue candidate artifacts for review; never execute or promote them."""
        result = self.text_development_brain.propose(request, context)
        if not result.get("success"):
            return result
        result["mother_review"] = {
            "status": "REVIEW_REQUIRED",
            "candidate_static_reviewed": False,
            "security_reviewed": False,
            "tests_executed": False,
            "regression_executed": False,
            "promotion_allowed": False,
        }
        if result.get("artifact_type") == "python" and isinstance(context.get("content"), str):
            review = self.coding_brain.review_python(context["content"])
            result["mother_review"]["static_code_review"] = {
                "status": review.status,
                "success": review.success,
                "findings": [finding.__dict__ for finding in review.findings],
                "executes_code": False,
            }
            result["mother_review"]["candidate_static_reviewed"] = True
            result["mother_review"]["status"] = (
                "STATIC_REVIEW_NEEDS_FOLLOWUP" if review.status != "STATIC_CHECK_PASSED"
                else "STATIC_REVIEW_PASSED_TESTS_STILL_REQUIRED"
            )
        return result

    def _internal_coding_handler(self, request: str, context: dict):
        """Review supplied Python source or draft code; never writes or executes it."""
        if "source_code" in context:
            review = self.coding_brain.review_context(context)
            review["request"] = request
            review["role"] = "internal_coding_brain"
            return review
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
        decision_context = context.get("decision_context", {})
        if not isinstance(decision_context, dict):
            decision_context = {}
        result = self._build_plan(request.strip(), intent)
        # Carry read-only context provenance into the plan record. The
        # planner still creates tasks only; this metadata grants no authority.
        result.metadata["decision_context"] = decision_context
        result.metadata["context_memory_ids"] = tuple(
            decision_context.get("memory_ids", ())
        )
        result.metadata["context_knowledge_ids"] = tuple(
            decision_context.get("knowledge_ids", ())
        )
        result.metadata["context_working_memory_ids"] = tuple(
            decision_context.get("working_memory_ids", ())
        )
        result.metadata["context_retrieval_id"] = decision_context.get(
            "retrieval_id"
        )
        result.metadata["context_aware"] = True
        return {
            "success": result.success,
            "decision_context": decision_context,
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

    @staticmethod
    def _internal_document_file_handler(request: str, context: dict):
        """Summarize supplied document text only; never opens or modifies a path."""
        source = context.get("document_text")
        if not isinstance(source, str) or not source.strip():
            return {
                "success": False,
                "status": "DOCUMENT_TEXT_REQUIRED",
                "reason": "Provide document_text explicitly; filesystem access is not part of this handler.",
                "reads_files": False,
                "writes_files": False,
                "deletes_files": False,
                "executes_content": False,
                "factual_verification": False,
            }
        max_chars = context.get("max_chars", 12000)
        if not isinstance(max_chars, int) or isinstance(max_chars, bool):
            max_chars = 12000
        max_chars = min(max(max_chars, 1), 12000)
        text = source.strip()
        excerpt = text[:max_chars]
        lines = [line.strip() for line in excerpt.splitlines() if line.strip()]
        # Extract only source-grounded lines; do not invent a generated summary.
        max_points = context.get("max_points", 8)
        if not isinstance(max_points, int) or isinstance(max_points, bool):
            max_points = 8
        max_points = min(max(max_points, 1), 8)
        points = [line[:500] for line in lines[:max_points]]
        return {
            "success": True,
            "status": "SOURCE_GROUNDED_EXTRACTION_NOT_FACT_VERIFIED",
            "request": request.strip()[:240],
            "character_count": len(text),
            "processed_character_count": len(excerpt),
            "line_count": len(lines),
            "extracted_points": points,
            "truncated": len(text) > len(excerpt),
            "reads_files": False,
            "writes_files": False,
            "deletes_files": False,
            "executes_content": False,
            "factual_verification": False,
        }

    @staticmethod
    def _internal_system_architecture_handler(request: str, context: dict):
        """Review explicitly supplied architecture text; never inspect filesystem."""
        source = context.get("architecture_text")
        if not isinstance(source, str) or not source.strip():
            return {"success": False, "status": "ARCHITECTURE_TEXT_REQUIRED", "reason": "Supply architecture_text explicitly; repository files are not inspected.", "reads_files": False, "writes_files": False, "executes_code": False, "repository_completeness_verified": False}
        max_chars = context.get("max_chars", 12000)
        if not isinstance(max_chars, int) or isinstance(max_chars, bool):
            max_chars = 12000
        max_chars = min(max(max_chars, 1), 12000)
        text = source.strip()
        excerpt = text[:max_chars]
        lines = [line.strip()[:500] for line in excerpt.splitlines() if line.strip()]
        modules = [line for line in lines if any(token in line.lower() for token in ("module", "component", "brain", "service", "package"))][:12]
        dependencies = [line for line in lines if any(token in line.lower() for token in ("depends", "dependency", "calls", "routes to", "->", "→", "imports"))][:12]
        risks = []
        if not modules:
            risks.append("No explicit module/component lines recognized; provide a clearer architecture description.")
        if not dependencies:
            risks.append("No explicit dependency or data-flow lines recognized; dependency coverage is unknown.")
        if len(text) > len(excerpt):
            risks.append("Input was truncated; the review may omit later details.")
        return {"success": True, "status": "BOUNDED_ARCHITECTURE_TEXT_REVIEW_NOT_REPOSITORY_VERIFIED", "request": request.strip()[:240], "input_character_count": len(text), "processed_character_count": len(excerpt), "modules_or_components": modules, "dependency_or_flow_lines": dependencies, "review_warnings": risks, "truncated": len(text) > len(excerpt), "reads_files": False, "writes_files": False, "executes_code": False, "repository_completeness_verified": False, "factual_verification": False}

    @staticmethod
    def _internal_performance_resource_handler(request: str, context: dict):
        """Assess supplied numeric metrics only; does not probe or change the device."""
        metrics = context.get("metrics")
        if not isinstance(metrics, dict) or not metrics:
            return {
                "success": False,
                "status": "RESOURCE_METRICS_REQUIRED",
                "reason": "Supply a metrics dictionary; this handler does not inspect live device state.",
                "reads_system_state": False,
                "changes_runtime": False,
            }
        thresholds = {"ram_used_percent": 85.0, "cpu_percent": 90.0, "gpu_used_percent": 90.0}
        assessed = {}
        warnings = []
        for key, value in metrics.items():
            if key not in thresholds:
                continue
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                warnings.append(f"{key}: ignored because metric is not numeric")
                continue
            if not 0 <= float(value) <= 100:
                warnings.append(f"{key}: ignored because percentage is outside 0..100")
                continue
            limit = thresholds[key]
            assessed[key] = {"value_percent": float(value), "warning_threshold_percent": limit, "status": "HIGH" if value >= limit else "WITHIN_THRESHOLD"}
            if value >= limit:
                warnings.append(f"{key} is at or above the conservative {limit:g}% warning threshold")
        if not assessed:
            return {"success": False, "status": "NO_VALID_RESOURCE_METRICS", "assessed_metrics": {}, "warnings": warnings, "reads_system_state": False, "changes_runtime": False}
        return {
            "success": True,
            "status": "SUPPLIED_METRICS_ASSESSED_NOT_LIVE_MONITORING",
            "request": request.strip()[:240],
            "assessed_metrics": assessed,
            "warnings": warnings,
            "recommendation": "Consider deferring nonessential work when a supplied metric is HIGH; do not kill or unload models automatically.",
            "reads_system_state": False,
            "changes_runtime": False,
            "executes_commands": False,
        }

    @staticmethod
    def _internal_evidence_fact_checking_handler(request: str, context: dict):
        """Compare caller-supplied claims/evidence; never invent sources or assert live verification."""
        claims = context.get("claims")
        evidence = context.get("evidence")
        if not isinstance(claims, (list, tuple)) or not claims:
            return {"success": False, "status": "CLAIMS_REQUIRED", "claim_reviews": [], "factual_verification": False, "external_research_performed": False}
        if not isinstance(evidence, (list, tuple)):
            return {"success": False, "status": "EVIDENCE_LIST_REQUIRED", "claim_reviews": [], "factual_verification": False, "external_research_performed": False}
        if len(claims) > 20 or len(evidence) > 40:
            return {"success": False, "status": "INPUT_LIMIT_EXCEEDED", "claim_reviews": [], "factual_verification": False, "external_research_performed": False}
        clean_claims = []
        for claim in claims:
            if not isinstance(claim, str) or not claim.strip():
                return {"success": False, "status": "CLAIM_FORMAT_INVALID", "claim_reviews": [], "factual_verification": False}
            clean_claims.append(claim.strip()[:500])
        clean_evidence = []
        for item in evidence:
            if not isinstance(item, dict):
                return {"success": False, "status": "EVIDENCE_FORMAT_INVALID", "claim_reviews": [], "factual_verification": False}
            text = item.get("text")
            source = item.get("source")
            supports = item.get("supports_claims", [])
            contradicts = item.get("contradicts_claims", [])
            if not isinstance(text, str) or not text.strip() or not isinstance(source, str) or not source.strip():
                return {"success": False, "status": "EVIDENCE_PROVENANCE_REQUIRED", "claim_reviews": [], "factual_verification": False}
            if not isinstance(supports, (list, tuple)) or not isinstance(contradicts, (list, tuple)):
                return {"success": False, "status": "EVIDENCE_MAPPING_INVALID", "claim_reviews": [], "factual_verification": False}
            if any(not isinstance(i, int) or isinstance(i, bool) or i < 0 or i >= len(clean_claims) for i in (*supports, *contradicts)):
                return {"success": False, "status": "EVIDENCE_CLAIM_INDEX_INVALID", "claim_reviews": [], "factual_verification": False}
            clean_evidence.append({"text": text.strip()[:1000], "source": source.strip()[:300], "supports_claims": list(dict.fromkeys(supports)), "contradicts_claims": list(dict.fromkeys(contradicts))})
        reviews = []
        for index, claim in enumerate(clean_claims):
            supporting = [e for e in clean_evidence if index in e["supports_claims"]]
            contradicting = [e for e in clean_evidence if index in e["contradicts_claims"]]
            if supporting and contradicting:
                status = "CONFLICTING_SUPPLIED_EVIDENCE"
            elif contradicting:
                status = "CONTRADICTED_BY_SUPPLIED_EVIDENCE"
            elif supporting:
                status = "SUPPORTED_BY_SUPPLIED_EVIDENCE_NOT_INDEPENDENTLY_VERIFIED"
            else:
                status = "INSUFFICIENT_MAPPED_EVIDENCE"
            reviews.append({"claim_index": index, "claim": claim, "status": status, "supporting_sources": [e["source"] for e in supporting], "contradicting_sources": [e["source"] for e in contradicting], "uncertainty": "Mappings and source quality were supplied by the caller and have not been independently checked."})
        return {"success": True, "status": "SUPPLIED_EVIDENCE_REVIEW_NOT_INDEPENDENTLY_VERIFIED", "claim_reviews": reviews, "claims_reviewed": len(reviews), "evidence_items_reviewed": len(clean_evidence), "factual_verification": False, "external_research_performed": False, "source_authenticity_checked": False, "writes_files": False, "executes_tools": False}

    @staticmethod
    def _internal_human_handoff_handler(request: str, context: dict):
        """Build a bounded handoff from caller-supplied facts; never executes actions."""
        summary = context.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            return {"success": False, "status": "HANDOFF_SUMMARY_REQUIRED", "reason": "Provide a concise summary of completed work and current state.", "handoff_ready": False, "actions_executed": False, "approval_requested": False}
        def clean_list(key, limit=8):
            value = context.get(key, [])
            if not isinstance(value, (list, tuple)):
                return None
            cleaned = []
            for item in value[:limit]:
                if not isinstance(item, str) or not item.strip():
                    return None
                cleaned.append(item.strip()[:300])
            return list(dict.fromkeys(cleaned))
        blockers = clean_list("blockers")
        decisions = clean_list("decisions_needed")
        completed = clean_list("completed_items")
        if blockers is None or decisions is None or completed is None:
            return {"success": False, "status": "HANDOFF_LISTS_INVALID", "handoff_ready": False, "actions_executed": False, "reason": "blockers, decisions_needed and completed_items must be lists of non-empty strings."}
        approval_needed = context.get("approval_needed", False)
        if not isinstance(approval_needed, bool):
            return {"success": False, "status": "APPROVAL_FLAG_INVALID", "handoff_ready": False, "actions_executed": False}
        return {"success": True, "status": "HUMAN_HANDOFF_PREPARED_NOT_SENT", "handoff_ready": True, "summary": summary.strip()[:2000], "completed_items": completed, "blockers": blockers, "decisions_needed": decisions, "approval_needed": approval_needed, "approval_granted": False, "actions_executed": False, "message_sent": False, "external_contacted": False, "note": "Prepared only from supplied context; no notification, external contact, approval, or action execution occurred."}

    @staticmethod
    def _internal_backup_continuity_handler(request: str, context: dict):
        """Assess supplied backup evidence only; never reads, writes, or restores files."""
        backup = context.get("backup")
        restore_test = context.get("restore_test")
        if not isinstance(backup, dict):
            return {"success": False, "status": "BACKUP_EVIDENCE_REQUIRED", "backup_validated": False, "restore_test_verified": False, "files_read": False, "files_written": False, "restore_executed": False}
        required = ("location_label", "created_at", "content_manifest", "integrity_check")
        missing = [key for key in required if key not in backup or backup[key] is None or backup[key] == ""]
        if missing:
            return {"success": False, "status": "BACKUP_METADATA_INCOMPLETE", "missing_fields": missing, "backup_validated": False, "restore_test_verified": False, "files_read": False, "files_written": False, "restore_executed": False}
        if not isinstance(backup["location_label"], str) or not isinstance(backup["created_at"], str) or not isinstance(backup["content_manifest"], (list, tuple)) or not isinstance(backup["integrity_check"], dict):
            return {"success": False, "status": "BACKUP_METADATA_INVALID", "backup_validated": False, "restore_test_verified": False, "files_read": False, "files_written": False, "restore_executed": False}
        integrity = backup["integrity_check"]
        integrity_passed = integrity.get("passed") if isinstance(integrity, dict) else None
        if not isinstance(integrity_passed, bool):
            return {"success": False, "status": "INTEGRITY_RESULT_INVALID", "backup_validated": False, "restore_test_verified": False, "files_read": False, "files_written": False, "restore_executed": False}
        if not integrity_passed:
            return {"success": True, "status": "BACKUP_INTEGRITY_FAILED", "backup_validated": False, "restore_test_verified": False, "warnings": ["Supplied integrity result did not pass."], "files_read": False, "files_written": False, "restore_executed": False}
        if not isinstance(restore_test, dict):
            return {"success": True, "status": "BACKUP_METADATA_REPORTED_RESTORE_TEST_MISSING", "backup_validated": False, "restore_test_verified": False, "warnings": ["Integrity success is caller-supplied metadata, not an independently executed check."], "files_read": False, "files_written": False, "restore_executed": False}
        restore_passed = restore_test.get("passed")
        if not isinstance(restore_passed, bool):
            return {"success": False, "status": "RESTORE_TEST_RESULT_INVALID", "backup_validated": False, "restore_test_verified": False, "files_read": False, "files_written": False, "restore_executed": False}
        return {"success": True, "status": "SUPPLIED_BACKUP_AND_RESTORE_EVIDENCE_REVIEWED_NOT_INDEPENDENTLY_VERIFIED", "backup_validated": False, "restore_test_verified": False, "reported_integrity_passed": integrity_passed, "reported_restore_test_passed": restore_passed, "manifest_item_count": min(len(backup["content_manifest"]), 100), "location_label": backup["location_label"][:200], "created_at": backup["created_at"][:100], "warnings": ["All checks are based on caller-supplied metadata; no actual backup file was inspected and no restore was performed."], "files_read": False, "files_written": False, "restore_executed": False}

    @staticmethod
    def _internal_uncertainty_handler(request: str, context: dict):
        """Assess supplied claim/evidence metadata only; never invent confidence scores."""
        claims = context.get("claims")
        if not isinstance(claims, (list, tuple)) or not claims:
            return {"success": False, "status": "CLAIMS_REQUIRED", "assessments": [], "claims_modified": False}
        if len(claims) > 50:
            return {"success": False, "status": "INPUT_LIMIT_EXCEEDED", "assessments": [], "claims_modified": False}
        assessments = []
        required_text = ("claim_id", "claim")
        required_counts = ("evidence_count", "conflict_count", "independent_source_count")
        for item in claims:
            if not isinstance(item, dict) or any(not isinstance(item.get(key), str) or not item[key].strip() for key in required_text):
                return {"success": False, "status": "CLAIM_METADATA_INVALID", "assessments": [], "claims_modified": False}
            if any(type(item.get(key)) is not int or item[key] < 0 or item[key] > 1000 for key in required_counts):
                return {"success": False, "status": "EVIDENCE_COUNTS_INVALID", "assessments": [], "claims_modified": False}
            evidence_count = item["evidence_count"]
            conflict_count = item["conflict_count"]
            source_count = item["independent_source_count"]
            gaps = []
            if evidence_count == 0:
                gaps.append("NO_EVIDENCE_REPORTED")
            if source_count == 0:
                gaps.append("NO_INDEPENDENT_SOURCE_REPORTED")
            if conflict_count > 0:
                gaps.append("UNRESOLVED_CONFLICT_REPORTED")
            if evidence_count > 0 and source_count == 0:
                gaps.append("INDEPENDENCE_NOT_ESTABLISHED")
            assessments.append({
                "claim_id": item["claim_id"].strip()[:120],
                "status": "UNCERTAINTY_FLAGS_PRESENT" if gaps else "NO_METADATA_GAP_FLAGGED",
                "uncertainty_flags": list(dict.fromkeys(gaps)),
                "reported_evidence_count": evidence_count,
                "reported_conflict_count": conflict_count,
                "reported_independent_source_count": source_count,
                "factual_truth_verified": False,
            })
        return {"success": True, "status": "SUPPLIED_CLAIM_METADATA_ASSESSED_NOT_FACT_VERIFIED", "assessments": assessments, "claims_assessed": len(assessments), "confidence_score_generated": False, "claims_modified": False, "external_research_performed": False}

    def _internal_web_tools_handler(self, request: str, context: dict):
        """Discover registered tool candidates only; never execute or authorize a tool."""
        if context.get("action") == "propose_dynamic_tool":
            return self._internal_dynamic_tool_creation_handler(request, context)
        query = context.get("query", request)
        limit = context.get("max_results", 10)
        if not isinstance(query, str) or not query.strip() or len(query) > 500:
            return {"success": False, "status": "TOOL_DISCOVERY_QUERY_INVALID", "candidates": [], "tools_executed": False}
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10:
            return {"success": False, "status": "TOOL_DISCOVERY_LIMIT_INVALID", "candidates": [], "tools_executed": False}
        try:
            found = self.tool_brain.discover(query.strip(), max_results=limit)
        except (ValueError, TypeError, RuntimeError) as exc:
            return {"success": False, "status": "TOOL_DISCOVERY_FAILED", "reason": str(exc)[:200], "candidates": [], "tools_executed": False}
        candidates = []
        for candidate in found[:limit]:
            candidates.append({
                "name": str(candidate.name)[:120],
                "description": str(getattr(candidate, "description", ""))[:300],
                "read_only": bool(getattr(candidate, "read_only", False)),
            })
        return {
            "success": True,
            "status": "REGISTERED_TOOLS_DISCOVERED_NOT_EXECUTED",
            "query": query.strip(),
            "candidates": candidates,
            "returned_count": len(candidates),
            "tools_executed": False,
            "permissions_granted": False,
            "protected_actions_authorized": False,
        }

    def _internal_dynamic_tool_creation_handler(self, request: str, context: dict):
        """Create a reviewed proposal only; this handler never approves or activates."""
        try:
            candidate = self.propose_dynamic_tool(request, context=context)
        except (ValueError, TypeError, KeyError) as exc:
            return {
                "success": False,
                "status": "DYNAMIC_TOOL_PROPOSAL_REJECTED",
                "reason": str(exc)[:300],
                "tool_activated": False,
                "approval_required": True,
            }
        return self._dynamic_tool_candidate_summary(candidate)

    @staticmethod
    def _dynamic_tool_candidate_summary(candidate: DynamicToolCandidate) -> dict:
        return {
            "success": candidate.status in {"STAGED", "ACTIVE", "ROLLED_BACK"},
            "status": candidate.status,
            "candidate_id": candidate.candidate_id,
            "name": candidate.spec.name,
            "description": candidate.spec.description,
            "operations": [
                {"operation": step.operation, "arguments": dict(step.arguments)}
                for step in candidate.spec.steps
            ],
            "sha256": candidate.sha256,
            "findings": list(candidate.findings),
            "approval_required": True,
            "tool_activated": candidate.status == "ACTIVE",
            "next_action": "Review the exact proposal, then call approve_dynamic_tool_candidate with explicit user approval.",
        }

    def propose_dynamic_tool(self, request: str, *, context: dict | None = None) -> DynamicToolCandidate:
        """Mother Brain proposal entry point. It can stage but cannot activate."""
        return self.tool_brain.dynamic_tool_creation.propose_from_request(
            request, context=context
        )

    def approve_dynamic_tool_candidate(self, candidate_id: str, *, user_approved: bool = False) -> dict:
        """Explicit user-controlled activation boundary; no LLM may set approval."""
        candidate = self.tool_brain.dynamic_tool_creation.approve(
            candidate_id, user_approved=user_approved
        )
        return self._dynamic_tool_candidate_summary(candidate)

    def rollback_dynamic_tool_candidate(self, candidate_id: str, *, user_approved: bool = False) -> dict:
        candidate = self.tool_brain.dynamic_tool_creation.rollback(
            candidate_id, user_approved=user_approved
        )
        return self._dynamic_tool_candidate_summary(candidate)

    def verify_dynamic_tool_candidate(self, candidate_id: str) -> dict:
        """Static candidate verification; never executes the proposed tool."""
        return self.tool_brain.dynamic_tool_creation.verify_candidate(candidate_id)

    def dynamic_tool_creation_status(self) -> dict:
        """Read-only lifecycle and capability diagnostics for the tool builder."""
        return self.tool_brain.dynamic_tool_creation.lifecycle_status()

    def design_dynamic_tool(self, request: str, *, context: dict | None = None) -> dict:
        """Create a staged design report; activation still requires separate approval."""
        return self.tool_brain.dynamic_tool_creation.design_report(request, context=context)

    @staticmethod
    def _internal_audio_handler(request: str, context: dict):
        """Transcribe only an explicit local WAV inside the configured private audio capture directory."""
        import os
        from pathlib import Path
        capture_dir = os.getenv("SAHIBEX_AUDIO_CAPTURE_DIR", "").strip()
        audio_path = context.get("audio_path")
        if not capture_dir:
            return {"success": False, "status": "AUDIO_ASR_NOT_CONFIGURED", "transcript": None, "network_upload_performed": False}
        if not isinstance(audio_path, str) or not audio_path.strip() or len(audio_path) > 2048:
            return {"success": False, "status": "AUDIO_PATH_INVALID", "transcript": None, "network_upload_performed": False}
        from core.brain.speech_recognition import LocalWhisperCppRecognizer, SpeechRecognitionError
        try:
            root = Path(capture_dir).expanduser().resolve(strict=True)
            candidate = Path(audio_path).expanduser()
            if candidate.is_symlink():
                raise ValueError("symbolic-link audio files are not accepted")
            resolved = candidate.resolve(strict=True)
            if resolved.parent != root or not resolved.is_file():
                raise ValueError("audio must be a regular file directly inside the configured private capture directory")
            recognizer = LocalWhisperCppRecognizer()
            result = recognizer.transcribe(resolved)
        except SpeechRecognitionError as exc:
            return {"success": False, "status": "AUDIO_TRANSCRIPTION_REJECTED", "error_code": exc.code, "reason": str(exc)[:200], "transcript": None, "network_upload_performed": False}
        except (OSError, ValueError, RuntimeError) as exc:
            return {"success": False, "status": "AUDIO_INPUT_REJECTED", "reason": str(exc)[:200], "transcript": None, "network_upload_performed": False}
        return {
            "success": True,
            "status": "LOCAL_AUDIO_TRANSCRIBED_UNVERIFIED",
            "transcript": result.transcript[:8192],
            "engine": result.engine,
            "mode": result.mode,
            "language": result.language,
            "duration_seconds": result.duration_seconds,
            "transcript_verified_against_human": False,
            "network_upload_performed": False,
            "microphone_capture_performed": False,
        }

    @staticmethod
    def _internal_vision_handler(request: str, context: dict):
        """Perform local OCR only on an explicitly supplied image in the private capture directory."""
        import os
        from pathlib import Path
        capture_dir = os.getenv("SAHIBEX_OCR_CAPTURE_DIR", "").strip()
        image_path = context.get("image_path")
        if not capture_dir:
            return {"success": False, "status": "VISION_OCR_NOT_CONFIGURED", "text": None, "image_interpretation_verified": False}
        try:
            from core.brain.ocr_runtime import OCRRuntime
            runtime = OCRRuntime(
                capture_dir,
                tesseract_cmd=os.getenv("SAHIBEX_TESSERACT_EXECUTABLE", "tesseract"),
                timeout_seconds=20.0,
            )
        except (OSError, ValueError) as exc:
            return {"success": False, "status": "VISION_OCR_BACKEND_UNAVAILABLE", "reason": str(exc)[:200], "text": None, "image_interpretation_verified": False}
        if image_path is None:
            return {
                "success": True,
                "status": "VISION_OCR_READY_IMAGE_REQUIRED",
                "ocr_backend": "tesseract",
                "installed_languages": list(runtime.installed_languages()),
                "image_interpretation_verified": False,
                "camera_capture_performed": False,
                "network_upload_performed": False,
            }
        if not isinstance(image_path, str) or not image_path.strip() or len(image_path) > 2048:
            return {"success": False, "status": "VISION_IMAGE_PATH_INVALID", "text": None, "image_interpretation_verified": False}
        languages = context.get("languages", "eng")
        if not isinstance(languages, str) or len(languages) > 80:
            return {"success": False, "status": "VISION_LANGUAGE_SETTING_INVALID", "text": None, "image_interpretation_verified": False}
        try:
            observation = runtime.extract(Path(image_path), languages=languages)
        except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
            return {"success": False, "status": "VISION_OCR_REJECTED", "reason": str(exc)[:200], "text": None, "image_interpretation_verified": False}
        return {
            "success": True,
            "status": "VISION_OCR_TEXT_EXTRACTED_UNTRUSTED",
            "text": observation.text[:16000],
            "source_sha256": observation.sha256,
            "source_filename": observation.filename,
            "languages": observation.languages,
            "confidence": observation.confidence,
            "trust_notice": observation.trust_notice,
            "image_interpretation_verified": False,
            "camera_capture_performed": False,
            "network_upload_performed": False,
        }

    def _internal_knowledge_handler(self, request: str, context: dict):
        """Retrieve only through the existing persistent, trust-filtering Knowledge Brain."""
        query = context.get("query", request)
        verified_only = context.get("verified_only", True)
        min_confidence = context.get("min_confidence", 0.0)
        if not isinstance(query, str) or not query.strip() or len(query) > 1000:
            return {"success": False, "status": "KNOWLEDGE_QUERY_INVALID", "items": []}
        if not isinstance(verified_only, bool):
            return {"success": False, "status": "VERIFIED_ONLY_FLAG_INVALID", "items": []}
        if isinstance(min_confidence, bool) or not isinstance(min_confidence, (int, float)) or not 0 <= min_confidence <= 1:
            return {"success": False, "status": "MIN_CONFIDENCE_INVALID", "items": []}
        try:
            result = self.knowledge_brain.retrieve(query.strip(), verified_only=verified_only, min_confidence=float(min_confidence))
        except (ValueError, TypeError):
            return {"success": False, "status": "KNOWLEDGE_RETRIEVAL_REJECTED", "items": []}
        items = []
        for item in result.knowledge[:20]:
            items.append({
                "knowledge_id": item.knowledge_id,
                "statement": item.statement,
                "confidence": item.confidence,
                "verified_flag": item.verified,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "last_verified_at": item.last_verified_at.isoformat() if item.last_verified_at else None,
                "evidence_count": len(item.evidence),
                "finding_count": len(item.findings),
            })
        return {
            "success": True,
            "status": "TRUST_FILTERED_KNOWLEDGE_RETRIEVAL",
            "query": result.query,
            "verified_only": verified_only,
            "min_confidence": float(min_confidence),
            "items": items,
            "returned_count": len(items),
            "provenance_details_included": False,
            "permission_granted": False,
            "actions_executed": False,
        }

    @staticmethod
    def _internal_voice_handler(request: str, context: dict):
        """Inspect configured local voice components only; do not record/play audio."""
        import os
        import shutil
        from pathlib import Path
        from core.brain.speech_recognition import LocalWhisperCppRecognizer
        asr = LocalWhisperCppRecognizer()
        asr_ready = asr.is_ready()
        tts_executable = os.getenv("SAHIBEX_PIPER_EXECUTABLE", "piper")
        tts_resolved = shutil.which(tts_executable) if not os.path.isabs(tts_executable) else tts_executable
        if not tts_resolved or not Path(tts_resolved).is_file():
            tts_engine_ready = False
        else:
            tts_engine_ready = True
        models = {
            "hi": os.getenv("SAHIBEX_PIPER_HI_MODEL", ""),
            "en": os.getenv("SAHIBEX_PIPER_EN_MODEL", ""),
        }
        model_ready = {lang: bool(path and Path(path).expanduser().is_file()) for lang, path in models.items()}
        tts_ready = tts_engine_ready and any(model_ready.values())
        if asr_ready and tts_ready:
            status = "LOCAL_VOICE_COMPONENTS_CONFIGURED_ROUND_TRIP_UNVERIFIED"
        elif not asr_ready and not tts_ready:
            status = "LOCAL_ASR_AND_TTS_NOT_READY"
        elif not asr_ready:
            status = "LOCAL_ASR_NOT_READY"
        else:
            status = "LOCAL_TTS_NOT_READY"
        return {
            "success": True,
            "status": status,
            "local_asr_ready": asr_ready,
            "local_asr_engine_path": str(asr.executable),
            "local_asr_model_path_configured": bool(asr.model_path.is_file()),
            "local_tts_engine_ready": tts_engine_ready,
            "local_tts_model_ready": model_ready,
            "live_microphone_test_performed": False,
            "speaker_playback_test_performed": False,
            "end_to_end_round_trip_verified": False,
            "network_audio_upload_performed": False,
        }

    @staticmethod
    def _internal_language_handler(request: str, context: dict):
        """Identify likely language/script from supplied text; no translation is implied."""
        from core.brain.universal_language_brain import UniversalLanguageBrain
        sample = context.get("text", request)
        if not isinstance(sample, str) or not sample.strip() or len(sample) > 10000:
            return {"success": False, "status": "LANGUAGE_TEXT_INVALID", "assessment": None, "translation_performed": False}
        try:
            assessment = UniversalLanguageBrain().detect(sample)
        except (TypeError, ValueError):
            return {"success": False, "status": "LANGUAGE_DETECTION_FAILED", "assessment": None, "translation_performed": False}
        if assessment.language_code in {"und", "und-Latn"}:
            status = "LANGUAGE_UNDETERMINED_OR_LOW_CONFIDENCE"
        else:
            status = "LANGUAGE_ASSESSED_HEURISTICALLY"
        return {
            "success": True,
            "status": status,
            "assessment": {
                "language_code": assessment.language_code,
                "language_name": assessment.language_name,
                "script": assessment.script,
                "confidence": assessment.confidence,
                "mixed": assessment.mixed,
            },
            "translation_performed": False,
            "fluent_generation_verified": False,
        }

    @staticmethod
    def _internal_math_handler(request: str, context: dict):
        """Use the project's restricted arithmetic resolver; never eval user input."""
        from core.brain.math_resolver import resolve_math_question
        expression = context.get("expression", request)
        if not isinstance(expression, str) or not expression.strip() or len(expression) > 300:
            return {"success": False, "status": "ARITHMETIC_INPUT_INVALID", "answer": None, "dynamic_evaluation": False}
        try:
            response = resolve_math_question(expression)
        except (ArithmeticError, ValueError, TypeError):
            response = None
        if response is None:
            return {"success": False, "status": "UNSUPPORTED_OR_OUT_OF_BOUNDS_EXPRESSION", "answer": None, "expression": expression[:300], "dynamic_evaluation": False}
        return {
            "success": True,
            "status": "SAFE_ARITHMETIC_RESOLVED",
            "answer": response.answer,
            "expression": response.expression,
            "dynamic_evaluation": False,
            "external_actions": False,
        }

    @staticmethod
    def _internal_data_analysis_handler(request: str, context: dict):
        """Compute descriptive numeric summaries from supplied rows only."""
        rows = context.get("rows")
        fields = context.get("numeric_fields")
        safe = {"external_data_access": False, "rows_modified": False, "causal_claims_made": False}
        if not isinstance(rows, (list, tuple)) or not rows:
            return {"success": False, "status": "DATA_ROWS_REQUIRED", "summaries": {}, **safe}
        if len(rows) > 500:
            return {"success": False, "status": "INPUT_LIMIT_EXCEEDED", "summaries": {}, **safe}
        if not isinstance(fields, (list, tuple)) or not 1 <= len(fields) <= 20 or any(not isinstance(f, str) or not f.strip() for f in fields):
            return {"success": False, "status": "NUMERIC_FIELDS_REQUIRED_OR_INVALID", "summaries": {}, **safe}
        if any(not isinstance(row, dict) for row in rows):
            return {"success": False, "status": "DATA_ROW_INVALID", "summaries": {}, **safe}
        names = [f.strip() for f in fields]
        if len(names) != len(set(names)):
            return {"success": False, "status": "NUMERIC_FIELDS_DUPLICATED", "summaries": {}, **safe}
        summaries = {}
        for name in names:
            values = []
            missing_count = 0
            invalid_count = 0
            for row in rows:
                value = row.get(name)
                if value is None or value == "":
                    missing_count += 1
                    continue
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    invalid_count += 1
                    continue
                values.append(float(value))
            if values:
                summaries[name] = {
                    "count": len(values),
                    "mean": round(sum(values) / len(values), 6),
                    "minimum": min(values),
                    "maximum": max(values),
                    "missing_count": missing_count,
                    "invalid_count": invalid_count,
                    "status": "DESCRIPTIVE_STATISTICS_ONLY",
                }
            else:
                summaries[name] = {"count": 0, "mean": None, "minimum": None, "maximum": None, "missing_count": missing_count, "invalid_count": invalid_count, "status": "NO_VALID_NUMERIC_VALUES"}
        return {
            "success": True,
            "status": "SUPPLIED_DATA_DESCRIPTIVE_SUMMARY_ONLY",
            "row_count": len(rows),
            "summaries": summaries,
            "statistical_significance_tested": False,
            "causality_inferred": False,
            **safe,
        }

    @staticmethod
    def _internal_code_review_handler(request: str, context: dict):
        """Scan supplied diff text for selected risk patterns; not a complete security review."""
        diff_text = context.get("diff_text")
        safe = {"executes_code": False, "modifies_code": False, "repository_read": False, "security_review_complete": False}
        if not isinstance(diff_text, str) or not diff_text.strip():
            return {"success": False, "status": "DIFF_TEXT_REQUIRED", "findings": [], **safe}
        if len(diff_text) > 20000:
            return {"success": False, "status": "INPUT_LIMIT_EXCEEDED", "findings": [], **safe}
        patterns = (
            ("DYNAMIC_EVAL", "eval(", "Dynamic evaluation can execute input as code; inspect trust boundary."),
            ("DYNAMIC_EXEC", "exec(", "Dynamic execution can run constructed code; inspect authorization and input sources."),
            ("SHELL_TRUE", "shell=true", "Shell-mediated process execution can expand injection risk."),
            ("TLS_VERIFY_DISABLED", "verify=false", "TLS certificate verification appears disabled."),
            ("INSECURE_PICKLE_LOAD", "pickle.loads", "Deserializing untrusted pickle data can execute code."),
            ("BROAD_EXCEPTION_SWALLOW", "except exception: pass", "An exception may be silently swallowed; verify failure visibility."),
            ("WORLD_WRITABLE_PERMISSION", "chmod 777", "World-writable permissions may expose or alter files."),
        )
        findings = []
        for line_number, line in enumerate(diff_text.splitlines()[:500], start=1):
            normalized = line.casefold().replace(" ", "")
            for code, token, note in patterns:
                needle = token.casefold().replace(" ", "")
                if needle in normalized:
                    findings.append({"finding_id": code, "line": line_number, "excerpt": line.strip()[:240], "note": note, "status": "REVIEW_REQUIRED_NOT_CONFIRMED_VULNERABILITY"})
        return {
            "success": True,
            "status": "SUPPLIED_DIFF_HEURISTIC_SCAN_ONLY",
            "findings": findings[:100],
            "lines_scanned": min(len(diff_text.splitlines()), 500),
            "truncated": len(diff_text.splitlines()) > 500,
            "pattern_set_is_exhaustive": False,
            "false_positives_possible": True,
            **safe,
        }

    @staticmethod
    def _internal_planning_handler(request: str, context: dict):
        """Validate a supplied dependency graph; never schedules or executes tasks."""
        tasks = context.get("tasks")
        safe = {"tasks_executed": False, "schedule_created": False, "permissions_granted": False}
        if not isinstance(tasks, (list, tuple)) or not tasks:
            return {"success": False, "status": "TASKS_REQUIRED", "proposed_order": [], **safe}
        if len(tasks) > 30:
            return {"success": False, "status": "INPUT_LIMIT_EXCEEDED", "proposed_order": [], **safe}
        cleaned = []
        by_id = {}
        for item in tasks:
            if not isinstance(item, dict):
                return {"success": False, "status": "TASK_SPEC_INVALID", "proposed_order": [], **safe}
            task_id, description = item.get("task_id"), item.get("description")
            deps = item.get("depends_on", [])
            if (not isinstance(task_id, str) or not task_id.strip() or len(task_id) > 100
                    or task_id.strip() in by_id or not isinstance(description, str)
                    or not description.strip() or len(description) > 1000):
                return {"success": False, "status": "TASK_SPEC_INVALID", "proposed_order": [], **safe}
            if not isinstance(deps, (list, tuple)) or len(deps) > 30 or any(not isinstance(dep, str) or not dep.strip() for dep in deps):
                return {"success": False, "status": "DEPENDENCIES_INVALID", "proposed_order": [], **safe}
            normalized_deps = [dep.strip() for dep in deps]
            if len(normalized_deps) != len(set(normalized_deps)) or task_id.strip() in normalized_deps:
                return {"success": False, "status": "DEPENDENCIES_INVALID", "proposed_order": [], **safe}
            row = {"task_id": task_id.strip(), "description": description.strip(), "depends_on": normalized_deps}
            by_id[row["task_id"]] = row
            cleaned.append(row)
        for row in cleaned:
            if any(dep not in by_id for dep in row["depends_on"]):
                return {"success": False, "status": "UNKNOWN_DEPENDENCY", "proposed_order": [], "task_id": row["task_id"], **safe}
        indegree = {row["task_id"]: len(row["depends_on"]) for row in cleaned}
        dependents = {row["task_id"]: [] for row in cleaned}
        for row in cleaned:
            for dep in row["depends_on"]:
                dependents[dep].append(row["task_id"])
        ready = [row["task_id"] for row in cleaned if indegree[row["task_id"]] == 0]
        order = []
        while ready:
            current = ready.pop(0)
            order.append(current)
            for child in dependents[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
        if len(order) != len(cleaned):
            cycle_candidates = [row["task_id"] for row in cleaned if indegree[row["task_id"]] > 0]
            return {"success": False, "status": "DEPENDENCY_CYCLE_DETECTED", "proposed_order": [], "cycle_candidates": cycle_candidates, **safe}
        return {
            "success": True,
            "status": "DEPENDENCY_GRAPH_VALIDATED_PROPOSED_ORDER_ONLY",
            "proposed_order": order,
            "task_count": len(cleaned),
            "dependency_count": sum(len(row["depends_on"]) for row in cleaned),
            "validated_tasks": cleaned,
            "execution_performed": False,
            **safe,
        }

    @staticmethod
    def _internal_app_builder_handler(request: str, context: dict):
        """Draft a proposed app outline from supplied requirements; perform no build/deploy."""
        spec = context.get("app_spec")
        no_side_effects = {
            "writes_files": False,
            "generates_executable_code": False,
            "builds_app": False,
            "deploys_app": False,
            "requirements_independently_verified": False,
        }
        if not isinstance(spec, dict):
            return {"success": False, "status": "APP_SPEC_REQUIRED", **no_side_effects}
        name, goal, platform, features = (spec.get("app_name"), spec.get("goal"), spec.get("platform"), spec.get("features"))
        if any(not isinstance(v, str) or not v.strip() or len(v) > 200 for v in (name, goal, platform)):
            return {"success": False, "status": "APP_SPEC_FIELDS_INVALID", **no_side_effects}
        if not isinstance(features, (list, tuple)) or not 1 <= len(features) <= 20:
            return {"success": False, "status": "FEATURES_REQUIRED_OR_LIMIT_EXCEEDED", **no_side_effects}
        clean_features = []
        seen = set()
        for feature in features:
            if not isinstance(feature, str) or not feature.strip() or len(feature) > 200:
                return {"success": False, "status": "FEATURES_INVALID", **no_side_effects}
            label = feature.strip()
            if label.casefold() not in seen:
                seen.add(label.casefold())
                clean_features.append(label)
        constraints = spec.get("constraints", [])
        if not isinstance(constraints, (list, tuple)) or len(constraints) > 20 or any(not isinstance(c, str) or not c.strip() or len(c) > 300 for c in constraints):
            return {"success": False, "status": "CONSTRAINTS_INVALID", **no_side_effects}
        proposed_screens = [{
            "screen_name": feature[:80],
            "source_feature": feature,
            "suggested_regions": ["navigation or title", "feature-specific content", "loading, empty and error states"],
            "status": "DRAFT_REQUIRES_USER_REVIEW",
        } for feature in clean_features]
        gaps = []
        if not isinstance(spec.get("target_users"), str) or not spec.get("target_users", "").strip():
            gaps.append("TARGET_USERS_NOT_SPECIFIED")
        if not isinstance(spec.get("acceptance_criteria"), (list, tuple)) or not spec.get("acceptance_criteria"):
            gaps.append("ACCEPTANCE_CRITERIA_NOT_SPECIFIED")
        return {
            "success": True,
            "status": "APP_STRUCTURE_DRAFTED_NOT_BUILT",
            "app_name": name.strip(),
            "goal": goal.strip(),
            "target_platform": platform.strip(),
            "supplied_features": clean_features,
            "proposed_layers": ["presentation", "application logic", "data access"],
            "proposed_screens": proposed_screens,
            "constraints": [c.strip() for c in constraints],
            "requirements_gaps": gaps,
            "needs_user_review": True,
            "screen_count": len(proposed_screens),
            **no_side_effects,
        }

    @staticmethod
    def _internal_debugging_handler(request: str, context: dict):
        """Triage only supplied failure reports; never executes or edits code."""
        failures = context.get("failures")
        safety = {
            "executes_code": False,
            "reads_filesystem": False,
            "writes_filesystem": False,
            "changes_runtime": False,
            "root_cause_confirmed": False,
        }
        if not isinstance(failures, (list, tuple)) or not failures:
            return {"success": False, "status": "FAILURE_REPORTS_REQUIRED", "triage": [], **safety}
        if len(failures) > 30:
            return {"success": False, "status": "INPUT_LIMIT_EXCEEDED", "triage": [], **safety}

        triage = []
        seen_ids = set()
        for item in failures:
            if not isinstance(item, dict):
                return {"success": False, "status": "FAILURE_REPORT_INVALID", "triage": [], **safety}
            issue_id = item.get("issue_id")
            symptom = item.get("symptom")
            steps = item.get("reproduction_steps")
            expected = item.get("expected")
            observed = item.get("observed")
            if (not isinstance(issue_id, str) or not issue_id.strip() or len(issue_id) > 120
                    or issue_id.strip() in seen_ids
                    or not isinstance(symptom, str) or not symptom.strip() or len(symptom) > 2000):
                return {"success": False, "status": "FAILURE_REPORT_INVALID", "triage": [], **safety}
            if not isinstance(steps, (list, tuple)) or len(steps) > 10:
                return {"success": False, "status": "REPRODUCTION_STEPS_INVALID", "triage": [], **safety}
            if any(not isinstance(step, str) or not step.strip() or len(step) > 500 for step in steps):
                return {"success": False, "status": "REPRODUCTION_STEPS_INVALID", "triage": [], **safety}
            for value in (expected, observed):
                if value is not None and (not isinstance(value, str) or len(value) > 2000):
                    return {"success": False, "status": "EXPECTED_OBSERVED_INVALID", "triage": [], **safety}
            error_excerpt = item.get("error_excerpt", "")
            if not isinstance(error_excerpt, str) or len(error_excerpt) > 4000:
                return {"success": False, "status": "ERROR_EXCERPT_INVALID", "triage": [], **safety}

            gaps = []
            if not steps:
                gaps.append("REPRODUCTION_STEPS_MISSING")
            if not isinstance(expected, str) or not expected.strip():
                gaps.append("EXPECTED_BEHAVIOR_MISSING")
            if not isinstance(observed, str) or not observed.strip():
                gaps.append("OBSERVED_BEHAVIOR_MISSING")
            if not error_excerpt.strip():
                gaps.append("ERROR_OR_LOG_EXCERPT_NOT_SUPPLIED")
            triage.append({
                "issue_id": issue_id.strip(),
                "status": "EVIDENCE_INCOMPLETE" if gaps else "REPRODUCTION_REPORT_READY_FOR_INVESTIGATION",
                "symptom": symptom.strip()[:500],
                "reproduction_steps": [step.strip()[:500] for step in steps],
                "diagnostic_gaps": gaps,
                "suggested_next_steps": [
                    "Reproduce in a safe test environment before changing code",
                    "Capture the exact failing test or command and complete error output",
                    "Compare expected and observed behavior, then isolate one variable at a time",
                ],
                "root_cause": None,
            })
            seen_ids.add(issue_id.strip())
        return {
            "success": True,
            "status": "SUPPLIED_FAILURE_REPORTS_TRIAGED_NOT_EXECUTED",
            "triage": triage,
            "failures_reviewed": len(triage),
            "root_causes_invented": False,
            **safety,
        }

    @staticmethod
    def _internal_knowledge_maintenance_handler(request: str, context: dict):
        """Review supplied knowledge metadata only; never edit, delete, or promote records."""
        records = context.get("records")
        if not isinstance(records, (list, tuple)) or not records:
            return {"success": False, "status": "KNOWLEDGE_RECORDS_REQUIRED", "reviews": [], "records_modified": False, "records_deleted": False}
        if len(records) > 100:
            return {"success": False, "status": "INPUT_LIMIT_EXCEEDED", "reviews": [], "records_modified": False, "records_deleted": False}
        cleaned = []
        required = ("record_id", "content", "updated_at")
        for item in records:
            if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip() for k in required):
                return {"success": False, "status": "KNOWLEDGE_RECORD_METADATA_INVALID", "reviews": [], "records_modified": False, "records_deleted": False}
            cleaned.append({"record_id": item["record_id"].strip()[:120], "content": item["content"].strip()[:2000], "updated_at": item["updated_at"].strip()[:100], "source": item.get("source", "")[:200] if isinstance(item.get("source", ""), str) else ""})
        reviews = []
        seen_content = {}
        for i, item in enumerate(cleaned):
            duplicate_of = seen_content.get(item["content"].casefold())
            if duplicate_of is None:
                seen_content[item["content"].casefold()] = item["record_id"]
            reviews.append({"record_id": item["record_id"], "status": "POSSIBLE_DUPLICATE" if duplicate_of is not None else "REVIEW_REQUIRED", "possible_duplicate_of": duplicate_of, "updated_at": item["updated_at"], "note": "Age/staleness cannot be judged without a supplied policy or reference time; content similarity is exact case-insensitive match only."})
        return {"success": True, "status": "SUPPLIED_KNOWLEDGE_METADATA_REVIEW_ONLY", "reviews": reviews, "records_reviewed": len(reviews), "staleness_verified": False, "semantic_duplicates_checked": False, "conflicts_resolved": False, "records_modified": False, "records_deleted": False, "knowledge_promoted": False, "filesystem_or_database_access": False}

    @staticmethod
    def _internal_decision_analysis_handler(request: str, context: dict):
        """Rank only caller-scored options against explicit weighted criteria."""
        options = context.get("options")
        criteria = context.get("criteria")
        no_side_effects = {
            "reads_external_data": False,
            "executes_tools": False,
            "changes_state": False,
            "factual_verification": False,
        }
        if not isinstance(options, (list, tuple)) or not isinstance(criteria, (list, tuple)):
            return {"success": False, "status": "OPTIONS_AND_CRITERIA_REQUIRED", **no_side_effects}
        if not 2 <= len(options) <= 10 or not 1 <= len(criteria) <= 10:
            return {"success": False, "status": "INPUT_LIMIT_EXCEEDED", **no_side_effects}
        clean_criteria = []
        seen_criteria = set()
        for item in criteria:
            if not isinstance(item, dict):
                return {"success": False, "status": "CRITERIA_INVALID", **no_side_effects}
            cid, weight = item.get("criterion_id"), item.get("weight")
            if not isinstance(cid, str) or not cid.strip() or cid.strip() in seen_criteria:
                return {"success": False, "status": "CRITERIA_INVALID", **no_side_effects}
            if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not 0 < weight <= 100:
                return {"success": False, "status": "CRITERIA_WEIGHT_INVALID", **no_side_effects}
            seen_criteria.add(cid.strip())
            clean_criteria.append({"criterion_id": cid.strip(), "weight": float(weight)})
        clean_options = []
        seen_options = set()
        for item in options:
            if not isinstance(item, dict):
                return {"success": False, "status": "OPTIONS_INVALID", **no_side_effects}
            oid, scores = item.get("option_id"), item.get("scores")
            if not isinstance(oid, str) or not oid.strip() or oid.strip() in seen_options:
                return {"success": False, "status": "OPTIONS_INVALID", **no_side_effects}
            if not isinstance(scores, dict) or set(scores) != seen_criteria:
                return {"success": False, "status": "OPTION_SCORES_MUST_MATCH_CRITERIA", **no_side_effects}
            clean_scores = {}
            for cid in seen_criteria:
                score = scores.get(cid)
                if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 10:
                    return {"success": False, "status": "OPTION_SCORE_INVALID", **no_side_effects}
                clean_scores[cid] = float(score)
            seen_options.add(oid.strip())
            clean_options.append({"option_id": oid.strip(), "scores": clean_scores})
        weight_total = sum(c["weight"] for c in clean_criteria)
        ranked = []
        for option in clean_options:
            weighted = sum(option["scores"][c["criterion_id"]] * c["weight"] for c in clean_criteria) / weight_total
            ranked.append({"option_id": option["option_id"], "weighted_score": round(weighted, 4), "scores": option["scores"]})
        ranked.sort(key=lambda row: (-row["weighted_score"], row["option_id"]))
        top_score = ranked[0]["weighted_score"]
        tied = [row["option_id"] for row in ranked if row["weighted_score"] == top_score]
        return {
            "success": True,
            "status": "SUPPLIED_OPTION_SCORES_COMPARED_NOT_REAL_WORLD_VERIFIED",
            "ranking": ranked,
            "top_ranked_options": tied,
            "tie_for_first": len(tied) > 1,
            "criteria_used": clean_criteria,
            "option_count": len(ranked),
            "scores_invented": False,
            "recommendation_is_conditional_on_supplied_scores": True,
            **no_side_effects,
        }

    @staticmethod
    def _internal_privacy_data_governance_handler(request: str, context: dict):
        """Evaluate explicitly supplied scope metadata; never fetches or exposes data."""
        principal = context.get("principal_id")
        owner = context.get("resource_owner_id")
        if not isinstance(principal, str) or not principal.strip() or not isinstance(owner, str) or not owner.strip():
            return {"success": False, "status": "IDENTITY_SCOPE_REQUIRED", "reason": "Supply explicit principal_id and resource_owner_id; missing identity fails closed.", "access_allowed": False, "data_read": False, "data_exposed": False}
        if principal != owner:
            return {"success": True, "status": "DENIED_OWNER_MISMATCH", "access_allowed": False, "reason": "Principal does not match resource owner.", "data_read": False, "data_exposed": False, "cross_user_access": False}
        principal_child = context.get("principal_child_id")
        resource_child = context.get("resource_child_id")
        if (principal_child is None) != (resource_child is None):
            return {"success": False, "status": "CHILD_SCOPE_INCOMPLETE", "access_allowed": False, "reason": "Both child scope identifiers must be supplied together.", "data_read": False, "data_exposed": False}
        if principal_child is not None and (not isinstance(principal_child, str) or not principal_child.strip() or not isinstance(resource_child, str) or not resource_child.strip()):
            return {"success": False, "status": "CHILD_SCOPE_INVALID", "access_allowed": False, "data_read": False, "data_exposed": False}
        if principal_child is not None and principal_child != resource_child:
            return {"success": True, "status": "DENIED_CHILD_SCOPE_MISMATCH", "access_allowed": False, "reason": "Child-brain scope does not match; cross-child access is denied.", "data_read": False, "data_exposed": False, "cross_child_access": False}
        requested = context.get("requested_fields")
        allowed = context.get("allowed_fields")
        if not isinstance(requested, (list, tuple)) or not isinstance(allowed, (list, tuple)):
            return {"success": False, "status": "FIELD_SCOPE_REQUIRED", "access_allowed": False, "reason": "Explicit requested_fields and allowed_fields are required.", "data_read": False, "data_exposed": False}
        if any(not isinstance(field, str) or not field.strip() for field in (*requested, *allowed)):
            return {"success": False, "status": "FIELD_SCOPE_INVALID", "access_allowed": False, "data_read": False, "data_exposed": False}
        allowed_set = set(allowed)
        permitted = list(dict.fromkeys(field for field in requested if field in allowed_set))
        denied = list(dict.fromkeys(field for field in requested if field not in allowed_set))
        return {"success": not denied, "status": "MINIMUM_SCOPE_ALLOWED" if not denied else "DENIED_EXCESS_FIELDS", "access_allowed": not denied, "principal_matches_owner": True, "child_scope_checked": principal_child is not None, "permitted_fields": permitted, "denied_fields": denied, "data_read": False, "data_exposed": False, "writes_files": False, "grants_permissions": False, "note": "Metadata-only policy assessment; this does not enforce downstream storage or connector authorization."}

    def _internal_research_handler(self, request: str, context: dict):
        """Delegate to Mother Research; its own provider permission gates remain authoritative."""
        confirmation = context.get("confirmation", False)
        if not isinstance(confirmation, bool):
            return {
                "success": False,
                "operation": "research",
                "verified": False,
                "persisted": False,
                "error": "confirmation must be an explicit boolean",
            }
        result = self.research_learning_brain.research_topic(
            request,
            confirmation=confirmation,
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
        confirmation = context.get("confirmation", False)
        if not isinstance(confirmation, bool):
            return {
                "success": False,
                "operation": "learn",
                "verified": False,
                "persisted": False,
                "error": "confirmation must be an explicit boolean",
            }
        result = self.research_learning_brain.learn_topic(
            request,
            confirmation=confirmation,
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

    def run_managed_worker(
        self,
        task_id: str,
        handler: Callable[..., Any],
        *,
        args=(),
        kwargs=None,
        timeout_seconds: float = 10.0,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> WorkerExecution:
        """Run an explicitly approved, bounded handler in an isolated process.

        This opt-in path is separate from legacy in-process child dispatch.
        It fails closed when approval, runtime configuration, or safety latch
        is missing; it never retries work automatically.
        """
        if mother_approved is not True or human_approved is not True:
            raise PermissionError("managed worker requires explicit Mother and human approval")
        if self.emergency_stop.engaged:
            raise PermissionError("managed worker blocked by Emergency Stop")
        runtime = self.managed_worker_runtime
        if runtime is None:
            raise RuntimeError(
                "managed worker runtime is disabled; configure SAHIBEX_MANAGED_WORKER_DB"
            )
        submitted = runtime.submit(
            task_id,
            handler,
            args=args,
            kwargs=kwargs,
            timeout_seconds=timeout_seconds,
            max_retries=0,
        )
        if submitted.status != "running":
            return submitted
        return runtime.wait(task_id)

    def dispatch_worker_team(
        self,
        operation,
        subject: str,
        *,
        army_child_id: str,
        labour_child_id: str,
        verify_results: Callable[[Any, Any], bool],
        mother_approved: bool = False,
        human_approved: bool = False,
    ):
        """Dispatch real registered child handlers; workers receive no authority."""
        from core.brain.research_learning_command import DepartmentOperation

        if not isinstance(operation, DepartmentOperation):
            raise TypeError("operation must be DepartmentOperation")
        if not (mother_approved and human_approved):
            raise PermissionError("worker-team dispatch requires Mother and human approval")
        if not army_child_id or not labour_child_id or army_child_id == labour_child_id:
            raise ValueError("distinct registered Army and Labour child IDs are required")
        manager = self.specialist_child_brains

        def child_worker(child_id: str, role: str):
            def run(task: str):
                request = f"{role} subtask: {task}"
                metadata = {
                    "department_operation": operation.value,
                    "worker_role": role,
                }
                # Preserve the child manager's full lifecycle/capability
                # validation and dispatcher load accounting. Only the handler
                # invocation is moved into the managed process boundary.
                if self.managed_worker_runtime is not None:
                    def execute_managed(handler, normalized_request, handler_metadata):
                        execution = self.run_managed_worker(
                            f"child-{child_id}-{uuid4()}",
                            handler,
                            args=(normalized_request, handler_metadata),
                            timeout_seconds=30.0,
                            mother_approved=mother_approved,
                            human_approved=human_approved,
                        )
                        if execution.status != "completed":
                            raise RuntimeError(
                                execution.error or f"managed worker {execution.status}"
                            )
                        return execution.result

                    dispatched = manager.dispatch(
                        child_id,
                        request,
                        metadata=metadata,
                        mother_approved=True,
                        handler_executor=execute_managed,
                    )
                    return dispatched.result if dispatched.success else None

                dispatched = manager.dispatch(
                    child_id,
                    request,
                    metadata=metadata,
                    mother_approved=True,
                )
                return dispatched.result if dispatched.success else None
            return run

        return self.research_learning_brain.commander.dispatch_workers(
            operation,
            subject,
            army_worker=child_worker(army_child_id, "Army analysis"),
            labour_worker=child_worker(labour_child_id, "Labour evidence"),
            verify_results=verify_results,
        )

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

    def _prepare_user_input(self, text: str) -> tuple[str, dict[str, Any]]:
        """Normalize and understand text without granting authority or guessing silently."""
        normalized = self.input_normalization_engine.normalize(
            modality="text",
            content=text,
            source_id="user-text",
            timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=1.0,
            metadata={"channel": "master_brain"},
        )
        original = normalized.content
        try:
            perception = self.perception_language_brain.assess(original)
        except (TypeError, ValueError):
            language = self.universal_language_brain.detect(original)
            return original, {
                "status": "PERCEPTION_SKIPPED_INPUT_LIMIT_OR_INVALID",
                "input_id": normalized.input_id,
                "input_confidence": normalized.confidence,
                "input_confidence_basis": "text_payload_integrity_only; ASR confidence unavailable",
                "original_text": original,
                "normalized_text": original,
                "language_code": language.language_code,
                "language_name": language.language_name,
                "script": language.script,
                "language_confidence": language.confidence,
                "mixed_language": language.mixed,
                "corrections": [],
                "suggestions_not_applied": [],
                "known_terms": [],
                "contextual_repair_status": "SKIPPED_INPUT_VALIDATION",
                "contextual_repair_confidence": None,
                "permission_granted": False,
                "action_executed": False,
                "raw_input_preserved": True,
            }
        candidate = perception.normalized_text
        correction_rows = [
            {
                "original": item.original,
                "corrected": item.corrected,
                "reason": item.reason,
                "confidence": item.confidence,
            }
            for item in perception.corrections
        ]
        suggestion_rows = [
            {
                "original": item.original,
                "suggested": item.corrected,
                "reason": item.reason,
                "confidence": item.confidence,
            }
            for item in perception.suggestions
        ]
        contextual_status = "DISABLED_BY_DEFAULT"
        contextual_confidence = None

        # Model-based repair is an optional second opinion. It is never used
        # with the mock provider and its own numeric/negation/similarity guards
        # must pass before a candidate can enter the main request pipeline.
        contextual = self.contextual_input_understanding_brain
        if contextual is not None and (
            perception.suggestions or len(perception.corrections) >= 2
        ):
            contextual_result = contextual.understand(candidate)
            contextual_status = contextual_result.status
            contextual_confidence = contextual_result.confidence
            if contextual_result.changed:
                safe_candidate = contextual_result.corrected_text
                if (
                    ContextualInputUnderstandingBrain._numbers(original)
                    == ContextualInputUnderstandingBrain._numbers(safe_candidate)
                    and ContextualInputUnderstandingBrain._negations(original)
                    == ContextualInputUnderstandingBrain._negations(safe_candidate)
                ):
                    repaired = self.perception_language_brain.assess(
                        safe_candidate,
                        language_code=contextual_result.language_code,
                    )
                    candidate = repaired.normalized_text
                    correction_rows.extend(
                        {
                            "original": item.original,
                            "corrected": item.corrected,
                            "reason": "contextual_model_" + item.reason,
                            "confidence": item.confidence,
                        }
                        for item in repaired.corrections
                    )
                    if safe_candidate != original:
                        correction_rows.append({
                            "original": original,
                            "corrected": safe_candidate,
                            "reason": "contextual_model_repair",
                            "confidence": contextual_result.confidence,
                        })
                else:
                    contextual_status = "REJECTED_INDEPENDENT_SAFETY_CHECK"
        elif contextual is not None:
            contextual_status = "SKIPPED_NO_AMBIGUOUS_SPELLING"

        # Last independent guard: even curated normalization may not alter
        # numbers or explicit negation. Keep the exact original if it does.
        if (
            ContextualInputUnderstandingBrain._numbers(original)
            != ContextualInputUnderstandingBrain._numbers(candidate)
            or ContextualInputUnderstandingBrain._negations(original)
            != ContextualInputUnderstandingBrain._negations(candidate)
        ):
            candidate = original
            correction_rows = []
            status = "REJECTED_SAFETY_MISMATCH"
        elif candidate != original:
            status = "CURATED_OR_VERIFIED_REPAIR_APPLIED"
        else:
            status = "NO_SAFE_CORRECTION_NEEDED"

        language = self.universal_language_brain.detect(candidate)
        trace: dict[str, Any] = {
            "status": status,
            "input_id": normalized.input_id,
            "input_confidence": normalized.confidence,
            "input_confidence_basis": "text_payload_integrity_only; ASR confidence unavailable",
            "original_text": original,
            "normalized_text": candidate,
            "language_code": language.language_code,
            "language_name": language.language_name,
            "script": language.script,
            "language_confidence": language.confidence,
            "mixed_language": language.mixed,
            "corrections": correction_rows,
            "suggestions_not_applied": suggestion_rows,
            "known_terms": list(perception.known_terms),
            "contextual_repair_status": contextual_status,
            "contextual_repair_confidence": contextual_confidence,
            "permission_granted": False,
            "action_executed": False,
            "raw_input_preserved": True,
        }
        return candidate, trace

    def process(
        self,
        text: str,
        *,
        user_confirmation: bool = False,
    ) -> BrainResult:
        self.runtime_state = MotherBrainState()
        raw_text = text if isinstance(text, str) else ""
        input_trace: dict[str, Any] | None = None

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

            self._record_context(raw_text, result, input_understanding=input_trace)
            return result

        # ---------------------------------------------------------
        # RECEIVE REQUEST
        # ---------------------------------------------------------
        self.runtime_state.begin(text)
        text, input_trace = self._prepare_user_input(text)

        # Resolve only context-grounded references. If a word has multiple
        # common meanings or a demonstrative has no prior referent, ask before
        # entering a resolver, planner, model, or tool path.
        recent_turns = self.context.recent(3)
        context_parts: list[str] = []
        seen_context_users: set[str] = set()

        def append_context_turn(user_value: str, assistant_value: str) -> None:
            user_value = str(user_value or "").strip()[:2000]
            assistant_value = str(assistant_value or "").strip()[:2000]
            if not user_value or user_value.casefold() in seen_context_users:
                return
            seen_context_users.add(user_value.casefold())
            # A prior clarification question lists alternatives; it is not
            # evidence that the user selected one of those meanings.
            assistant_is_clarification = (
                assistant_value.rstrip().endswith(("?", "؟"))
                or "do you mean" in assistant_value.casefold()
                or "which file" in assistant_value.casefold()
                or "किस चीज़" in assistant_value
                or "किस फ़ाइल" in assistant_value
                or "किस विषय" in assistant_value
            )
            context_parts.append(
                user_value if assistant_is_clarification
                else user_value + " " + assistant_value
            )

        for turn in reversed(recent_turns):
            append_context_turn(turn.user, turn.assistant)

        # ContextManager is intentionally in-memory. Recover a small, newest-first
        # conversation window from persistent MemoryBrain after process restart.
        try:
            persisted_turns = self.memory_brain.retrieve_recent_conversations(limit=5)
        except Exception:
            persisted_turns = []
        for memory in persisted_turns:
            content = str(getattr(memory, "content", ""))
            if "\nSAHIBEX: " in content:
                user_part, assistant_part = content.split("\nSAHIBEX: ", 1)
                user_part = user_part.removeprefix("User: ")
                append_context_turn(user_part, assistant_part)
            else:
                append_context_turn(content, "")

        prior_context = " ".join(context_parts)[-4000:]
        ambiguous, ambiguity_question, ambiguity_reasons = (
            self.confidence_verification_brain.detect_ambiguity(
                text,
                context_text=prior_context,
                language_code=str(input_trace.get("language_code", "und")),
            )
        )
        if ambiguous:
            language_confidence = float(
                input_trace.get("language_confidence", 0.0)
            )
            confidence_decision = self.confidence_verification_brain.assess(
                input_id=str(input_trace.get("input_id", "master-input")),
                text=text,
                intent_confidence=0.30,
                language_confidence=language_confidence,
                input_confidence=float(input_trace.get("input_confidence", 1.0)),
                ambiguity_question=ambiguity_question,
                ambiguity_reasons=ambiguity_reasons,
                missing_information=True,
            )
            self.runtime_state.transition(MotherRuntimeState.UNDERSTANDING)
            self.runtime_state.set_request_context(
                intent="general_request", action="respond", risk="low"
            )
            self.runtime_state.set_authority(
                permission_allowed=False, confirmation_required=False
            )
            self.runtime_state.block("Clarification required before proceeding.")
            result = self._blocked_result(
                text=text,
                intent="general_request",
                intent_confidence=0.30,
                action=ActionType.RESPOND,
                action_confidence=0.30,
                risk="low",
                authority_decision=ActionDecision.DENY.value,
                confirmation_required=False,
                message=confidence_decision.clarification_question,
                verification_status="CLARIFICATION_REQUIRED",
                permission_allowed=False,
                metadata={
                    "confidence_verification": confidence_decision.to_dict(),
                    "ambiguity_detection": {
                        "status": "AMBIGUOUS",
                        "reasons": list(ambiguity_reasons),
                        "prior_context_used": bool(prior_context),
                    },
                    "action_executed": False,
                    "grants_authority": False,
                },
            )
            result.metadata["mother_runtime_state"] = self.runtime_state.snapshot()
            self._record_context(raw_text, result, input_understanding=input_trace)
            return result

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
            self._record_context(raw_text, result, input_understanding=input_trace)
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
                "CURATED_KNOWLEDGE"
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
                verification_status="CURATED_KNOWLEDGE",
                metadata={
                    "response_source": "curated_local_knowledge",
                    "fact_id": local_fact.fact_id,
                    "factual_verification": "CURATED_NOT_INDEPENDENTLY_VERIFIED",
                },
            )
            self.runtime_state.complete("curated local fact answered")
            result.metadata["mother_runtime_state"] = (
                self.runtime_state.snapshot()
            )
            self._record_context(raw_text, result, input_understanding=input_trace)
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
            self._record_context(raw_text, result, input_understanding=input_trace)
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
            self._record_context(raw_text, result, input_understanding=input_trace)
            return result

        # ---------------------------------------------------------
        # INTENT + OPTIONAL MULTILINGUAL SEMANTIC FALLBACK
        # ---------------------------------------------------------
        contextual_intent_detector = getattr(self.intent_engine, "detect_with_context", None)
        intent_result = (
            contextual_intent_detector(text, context_text=prior_context)
            if callable(contextual_intent_detector)
            else self.intent_engine.detect(text)
        )
        semantic_result = None
        if (
            self.semantic_intent_brain is not None
            and (
                intent_result.intent == "general_request"
                or intent_result.confidence < SemanticIntentBrain.MIN_CONFIDENCE
            )
        ):
            semantic_result = self.semantic_intent_brain.classify(
                text,
                expected_language_code=str(input_trace.get("language_code", "und")),
            )
            if semantic_result is not None and semantic_result.needs_clarification:
                clarification_action = semantic_result.action
                clarification_risk = self.permission.RISK_MAP[clarification_action]
                result = self._blocked_result(
                    text=text,
                    intent=semantic_result.intent,
                    intent_confidence=semantic_result.confidence,
                    action=clarification_action,
                    action_confidence=semantic_result.confidence,
                    risk=clarification_risk.value,
                    authority_decision=ActionDecision.DENY.value,
                    confirmation_required=False,
                    message=semantic_result.clarification_question,
                    verification_status="CLARIFICATION_REQUIRED",
                    permission_allowed=False,
                    metadata={
                        "semantic_intent": {
                            "status": "CLARIFICATION_REQUIRED",
                            "language_code": semantic_result.language_code,
                            "confidence": semantic_result.confidence,
                            "needs_clarification": True,
                            "clarification_question": semantic_result.clarification_question,
                            "provider": semantic_result.provider,
                            "model": semantic_result.model,
                            "grants_authority": False,
                            "executes_action": False,
                        }
                    },
                )
                self._record_denial_audit(
                    request=text,
                    intent=semantic_result.intent,
                    intent_confidence=semantic_result.confidence,
                    action=clarification_action,
                    action_confidence=semantic_result.confidence,
                    risk=clarification_risk.value,
                    confirmation_required=False,
                    reason="Semantic classifier requested clarification; no action executed.",
                )
                self._record_context(raw_text, result, input_understanding=input_trace)
                return result
            if semantic_result is not None and semantic_result.accepted:
                intent_result = IntentResult(
                    intent=semantic_result.intent,
                    confidence=semantic_result.confidence,
                    entities={"language_code": semantic_result.language_code},
                )

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
        action_input = text if raw_text == text else raw_text + "\n" + text
        action, constitution_action = self._classify_action(
            action_input,
            intent_result.intent,
        )
        # Semantic classification may refine an otherwise non-protected route,
        # but can never downgrade a deterministic protected-action finding.
        if (
            semantic_result is not None
            and semantic_result.accepted
            and action not in set(self.PROTECTED_ACTION_KEYWORDS)
            and semantic_result.action is not ActionType.RESPOND
        ):
            action = semantic_result.action
            constitution_action = self._action_class_for_semantic(action)

        action_confidence = self._action_confidence(
            action_input,
            action,
        )
        if (
            semantic_result is not None
            and semantic_result.accepted
            and action is semantic_result.action
        ):
            action_confidence = max(action_confidence, semantic_result.confidence)

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

            self._record_denial_audit(
                request=text, intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                action=action, action_confidence=action_confidence,
                risk=risk.value, confirmation_required=False,
                reason=authority.reason,
            )
            self._record_context(raw_text, result, input_understanding=input_trace)
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

            self._record_denial_audit(
                request=text, intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                action=action, action_confidence=action_confidence,
                risk=risk.value, confirmation_required=True,
                reason="Protected action requires explicit user confirmation.",
            )
            self._record_context(raw_text, result, input_understanding=input_trace)
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

            self._record_denial_audit(
                request=text, intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                action=action, action_confidence=action_confidence,
                risk=risk.value,
                confirmation_required=permission.requires_confirmation,
                reason=permission.reason,
            )
            self._record_context(raw_text, result, input_understanding=input_trace)
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

            self._record_denial_audit(
                request=text, intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                action=action, action_confidence=action_confidence,
                risk=risk.value,
                confirmation_required=permission.requires_confirmation,
                reason="Request failed safety verification.",
            )
            self._record_context(raw_text, result, input_understanding=input_trace)
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

        active_working_entries = self.memory_brain.working_memory.entries()[:5]
        working_memory_ids = tuple(
            entry.memory.memory_id for entry in active_working_entries
        )
        working_memory_items = tuple(
            {
                "memory_id": entry.memory.memory_id,
                "content": str(entry.memory.content)[:300],
                "memory_type": str(entry.memory.memory_type),
                "confidence": float(entry.memory.confidence),
                "verification_status": str(
                    entry.memory.metadata.get("verification_status", "UNVERIFIED")
                    if isinstance(entry.memory.metadata, dict)
                    else "UNVERIFIED"
                ),
                "source": "bounded_working_memory",
                "is_verified_evidence": False,
            }
            for entry in active_working_entries
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
            working_memory_ids=working_memory_ids,
            working_memory_items=working_memory_items,
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
            {
                "intent": intent_result.intent,
                "action": action.value,
                "decision_context": decision_context.summary(),
            },
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
            self._record_context(raw_text, result, input_understanding=input_trace)
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

            self._record_context(raw_text, result, input_understanding=input_trace)
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
            {
                "intent": intent_result.intent,
                "decision_context": decision_context.summary(),
            },
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
            self._record_context(raw_text, result, input_understanding=input_trace)
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
                self._record_context(raw_text, result, input_understanding=input_trace)
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
                self._record_context(raw_text, result, input_understanding=input_trace)
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
            research_payload = (
                research_dispatch.result
                if research_dispatch.accepted
                and isinstance(research_dispatch.result, dict)
                else {}
            )
            research_result = research_payload.get("result")
            research_handler_verified = (
                research_payload.get("success") is True
                and research_payload.get("verified") is True
                and research_payload.get("persisted") is True
            )

            if (
                research_result is None
                or not research_handler_verified
                or not research_result.success
                or research_result.verification_status != "VERIFIED"
            ):
                is_hindi_request = any("\u0900" <= char <= "\u097f" for char in text)
                if research_result is None:
                    research_error = (
                        "यह रिसर्च अभी पूरी नहीं हो सकी, इसलिए मैं सत्यापित जवाब नहीं दे सकता। मैंने बिना प्रमाण के निष्कर्ष नहीं बनाया। कृपया दोबारा कोशिश करें।"
                        if is_hindi_request
                        else (research_dispatch.reason or "Research execution failed.")
                    )
                else:
                    # Never surface an arbitrary inner answer after its final
                    # verification gate failed. Render a fresh, localized,
                    # evidence-neutral fallback instead of trusting that text.
                    research_error = (
                        "इस सवाल का भरोसेमंद जवाब देने के लिए पर्याप्त प्रमाण सत्यापित नहीं हो सके। मैंने बिना प्रमाण के निष्कर्ष नहीं बनाया।"
                        if is_hindi_request
                        else "I couldn't verify this research answer from sufficient evidence. No unsupported conclusion was generated."
                    )
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
                                research_handler_verified
                                and research_result is not None
                                and research_result.success
                                and research_result.verification_status == "VERIFIED"
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
                            "diagnostics": (
                                research_result.diagnostics
                                if research_result is not None
                                else {}
                            ),
                        },
                    },
                )

                self._record_context(raw_text, result, input_understanding=input_trace)
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
            learning_payload = (
                learning_dispatch.result
                if learning_dispatch.accepted
                and isinstance(learning_dispatch.result, dict)
                else {}
            )
            learning_result = learning_payload.get("result")
            learning_handler_verified = (
                learning_payload.get("success") is True
                and learning_payload.get("verified") is True
                and learning_payload.get("persisted") is True
            )

            if (
                learning_result is None
                or not learning_handler_verified
                or not learning_result.success
                or learning_result.verification_status != "VERIFIED"
                or learning_result.verified_knowledge_count <= 0
            ):
                learning_error = (
                    learning_dispatch.reason
                    if learning_result is None
                    else "I couldn't verify this learning result or persist verified knowledge."
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
                    metadata={
                        "internal_brain_dispatch": dict(internal_role_trace),
                        "mother_learning_integration": {
                            "success": (
                                learning_handler_verified
                                and learning_result is not None
                                and learning_result.success
                                and learning_result.verification_status == "VERIFIED"
                                and learning_result.verified_knowledge_count > 0
                            ),
                            "status": (
                                learning_result.status
                                if learning_result is not None
                                else "NOT_EXECUTED"
                            ),
                            "research_job_id": (
                                learning_result.research_job_id
                                if learning_result is not None
                                else None
                            ),
                            "research_execution_id": (
                                learning_result.research_execution_id
                                if learning_result is not None
                                else None
                            ),
                            "verification_status": (
                                learning_result.verification_status
                                if learning_result is not None
                                else "NOT_EXECUTED"
                            ),
                            "error": (
                                learning_result.error
                                if learning_result is not None
                                else learning_error
                            ),
                        },
                    },
                )

                self._record_context(raw_text, result, input_understanding=input_trace)
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
                    self._record_context(raw_text, result, input_understanding=input_trace)
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
                            "quality_reasons": getattr(operational_result, "quality_reasons", ()),
                            "diagnostics": getattr(operational_result, "diagnostics", {}),
                            "factual_verification": getattr(operational_result, "diagnostics", {}).get("factual_verification", False),
                        },
                    },
                )

                self._record_context(raw_text, result, input_understanding=input_trace)
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
                research_result.verification_status
                if research_result is not None
                else learning_result.verification_status
                if learning_result is not None
                else operational_result.verification_status
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
                    "context_reused": bool(
                        reasoning_result.reasoning_assessment
                        and reasoning_result.reasoning_assessment.reusable_context.get(
                            "working_memory_items"
                        )
                    ),
                    "needs_verification": bool(
                        reasoning_result.reasoning_assessment.needs_verification
                    ) if reasoning_result.reasoning_assessment else True,
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
                    "quality_reasons": (
                        getattr(operational_result, "quality_reasons", ())
                        if operational_result is not None
                        else ()
                    ),
                    "diagnostics": (
                        getattr(operational_result, "diagnostics", {})
                        if operational_result is not None
                        else {}
                    ),
                    "factual_verification": (
                        getattr(operational_result, "diagnostics", {}).get("factual_verification", False)
                        if operational_result is not None
                        else False
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
                    "audit_recorded": (
                        tool_result.audit_recorded
                        if tool_result is not None
                        else False
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
                    # Preserve the evidence/traceability diagnostics from the
                    # actual research pipeline at the public MainBrain boundary.
                    # Without this field, downstream callers see VERIFIED but
                    # cannot inspect the source/evidence chain that supports it.
                    "diagnostics": (
                        research_result.diagnostics
                        if research_result is not None
                        else {}
                    ),
                    "prompt_injection_status": (
                        research_result.prompt_injection_status
                        if research_result is not None
                        else "NOT_USED"
                    ),
                    "prompt_injection_safe_to_follow": (
                        research_result.prompt_injection_safe_to_follow
                        if research_result is not None
                        else False
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
                "cognitive_flow_trace": {
                    "context_built": True,
                    "working_memory_available": bool(working_memory_ids),
                    "working_memory_items_passed": (
                        len(decision_context.working_memory_items)
                    ),
                    "context_passed_to_reasoning": True,
                    "context_passed_to_planning": True,
                    "reasoning_context_received": bool(
                        reasoning_dispatch.result.get("decision_context")
                    ) if isinstance(reasoning_dispatch.result, dict) else False,
                    "reasoning_context_reused": bool(
                        getattr(
                            reasoning_dispatch.result.get("reasoning_assessment"),
                            "reusable_context",
                            {},
                        ).get("working_memory_items")
                    ) if isinstance(reasoning_dispatch.result, dict) else False,
                    "reasoning_assessment_needs_verification": bool(
                        getattr(
                            reasoning_dispatch.result.get("reasoning_assessment"),
                            "needs_verification",
                            True,
                        )
                    ) if isinstance(reasoning_dispatch.result, dict) else True,
                    "planning_context_received": bool(
                        orchestration_dispatch.result.get("decision_context")
                    ) if isinstance(orchestration_dispatch.result, dict) else False,
                    "plan_context_aware": bool(
                        plan.metadata.get("context_aware")
                    ),
                    "planning_context_reference_count": (
                        len(plan.metadata.get("context_memory_ids", ()))
                        + len(plan.metadata.get("context_knowledge_ids", ()))
                        + len(plan.metadata.get("context_working_memory_ids", ()))
                    ),
                    "execution_authority_changed": False,
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
            input_understanding=input_trace,
        )

        return result

    @staticmethod
    def _action_class_for_semantic(action: ActionType) -> ActionClass:
        """Map a semantic label into the existing independent constitution gate."""
        mapping = {
            ActionType.RESPOND: ActionClass.THINK,
            ActionType.RESEARCH: ActionClass.RESEARCH,
            ActionType.CREATE: ActionClass.THINK,
            ActionType.READ_FILE: ActionClass.READ,
            ActionType.WRITE_FILE: ActionClass.WRITE,
            ActionType.DELETE_FILE: ActionClass.DELETE,
            ActionType.RUN_COMMAND: ActionClass.EXECUTE,
            ActionType.NETWORK_ACCESS: ActionClass.NETWORK,
            ActionType.CREDENTIAL_USE: ActionClass.CREDENTIAL,
            ActionType.SYSTEM_CHANGE: ActionClass.SYSTEM_CHANGE,
            ActionType.FINANCIAL_ACTION: ActionClass.FINANCIAL,
        }
        return mapping[action]

    def _classify_action(
        self,
        text: str,
        intent: str,
    ) -> tuple[ActionType, ActionClass]:
        normalized = text.lower().strip()

        if any(
            keyword in normalized
            for keyword in self.PROTECTED_ACTION_KEYWORDS[ActionType.DELETE_FILE]
        ):
            return (
                ActionType.DELETE_FILE,
                ActionClass.DELETE,
            )

        if any(
            keyword in normalized
            for keyword in self.PROTECTED_ACTION_KEYWORDS[ActionType.RUN_COMMAND]
        ):
            return (
                ActionType.RUN_COMMAND,
                ActionClass.EXECUTE,
            )

        if any(
            keyword in normalized
            for keyword in self.PROTECTED_ACTION_KEYWORDS[ActionType.CREDENTIAL_USE]
        ):
            return (
                ActionType.CREDENTIAL_USE,
                ActionClass.CREDENTIAL,
            )

        if any(
            keyword in normalized
            for keyword in self.PROTECTED_ACTION_KEYWORDS[ActionType.FINANCIAL_ACTION]
        ):
            return (
                ActionType.FINANCIAL_ACTION,
                ActionClass.FINANCIAL,
            )

        if any(
            keyword in normalized
            for keyword in (
                *self.PROTECTED_ACTION_KEYWORDS[ActionType.SYSTEM_CHANGE][:5],
                "सिस्टम की सेटिंग बदलो",
                "सिस्टम सेटिंग बदलो",
                "सिस्टम कॉन्फ़िगरेशन बदलो",
                "सिस्टम की सेटिंग बदल दो",
                "system settings badal do",
                "system setting badlo",
            )
        ):
            return (
                ActionType.SYSTEM_CHANGE,
                ActionClass.SYSTEM_CHANGE,
            )

        if any(
            keyword in normalized
            for keyword in self.PROTECTED_ACTION_KEYWORDS[ActionType.SYSTEM_CHANGE][5:]
        ):
            return (
                ActionType.SYSTEM_CHANGE,
                ActionClass.SELF_UPDATE,
            )

        if any(
            keyword in normalized
            for keyword in self.PROTECTED_ACTION_KEYWORDS[ActionType.NETWORK_ACCESS]
        ):
            return (
                ActionType.NETWORK_ACCESS,
                ActionClass.NETWORK,
            )

        if any(
            keyword in normalized
            for keyword in self.PROTECTED_ACTION_KEYWORDS[ActionType.WRITE_FILE]
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

        protected_keywords = self.PROTECTED_ACTION_KEYWORDS

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

    def _record_denial_audit(
        self,
        *,
        request: str,
        intent: str,
        intent_confidence: float,
        action: ActionType,
        action_confidence: float,
        risk: str,
        confirmation_required: bool,
        reason: str,
    ) -> bool:
        """Persist a denial decision without granting or changing authority."""
        try:
            self.audit_logger.record(
                request=request[:1000],
                intent=intent or "unknown",
                intent_confidence=float(intent_confidence),
                action=action.value,
                action_confidence=float(action_confidence),
                risk=risk or "unknown",
                permission_allowed=False,
                confirmation_required=bool(confirmation_required),
                reason=(reason or "Request blocked by security policy.")[:1000],
            )
            return True
        except (OSError, TypeError, ValueError):
            # Logging failure must never convert a denial into execution.
            return False

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

    @staticmethod
    def _bounded_cognitive_score(value: Any, default: float = 0.0) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return default
        return max(0.0, min(1.0, float(value)))

    def _attention_trace(
        self,
        text: str,
        result: BrainResult,
    ) -> dict[str, Any]:
        # Scores are transparent routing heuristics, not calibrated
        # probabilities, factual confidence, permission or execution gates.
        intent_confidence = self._bounded_cognitive_score(
            result.intent_confidence, 0.0
        )
        risk_scores = {
            "low": 0.0,
            "medium": 0.5,
            "high": 0.8,
            "critical": 1.0,
        }
        risk_score = risk_scores.get(str(result.risk).lower(), 0.0)
        normalized = " ".join((text or "").casefold().split())
        urgency_terms = (
            "urgent", "emergency", "asap", "immediately", "critical",
            "तुरंत", "अभी", "आपातकाल", "जरूरी", "जल्दी",
            "urgent hai", "abhi karo", "turant",
        )
        urgency = 1.0 if any(term in normalized for term in urgency_terms) else 0.0
        recent_intents = self.context.summary().get("recent_intents", [])
        if isinstance(recent_intents, list) and recent_intents:
            goal_relevance = sum(
                1 for item in recent_intents if item == result.intent
            ) / len(recent_intents)
        else:
            goal_relevance = 0.5
        priority = max(intent_confidence, urgency, risk_score)
        attention_input = AttentionInput(
            content=(text or "empty request")[:4096],
            relevance=intent_confidence,
            urgency=urgency,
            risk=risk_score,
            goal_relevance=self._bounded_cognitive_score(goal_relevance, 0.5),
            priority=self._bounded_cognitive_score(priority, 0.0),
        )
        assessment = self.attention_engine.evaluate(attention_input)
        return {
            "version": self.attention_engine.VERSION,
            "decision": assessment.decision.value,
            "attention_score": assessment.attention_score,
            "input_id": assessment.input_id,
            "reason": assessment.reason,
            "signals": {
                "relevance_from_intent_confidence": intent_confidence,
                "urgency_keyword_heuristic": urgency,
                "risk_from_action_risk_class": risk_score,
                "goal_relevance_from_recent_intent_overlap": goal_relevance,
                "priority_heuristic": priority,
            },
            "advisory_only": True,
            "permission_granted": False,
            "action_executed": False,
            "execution_gated_by_attention": False,
            "confidence_is_calibrated_probability": False,
        }

    def _record_context(
        self,
        text: str,
        result: BrainResult,
        input_understanding: dict[str, Any] | None = None,
    ) -> None:
        # A common post-decision cognitive trace covers normal and fast paths.
        # It is observability/routing advice only: authority remains governed
        # by Constitution, PermissionGateway, and the existing safety brain.
        if isinstance(input_understanding, dict):
            result.metadata.setdefault(
                "input_understanding", dict(input_understanding)
            )

        # Confidence about request interpretation is kept separate from
        # factual truth. The verifier only labels a fact evidence-verified
        # when an upstream component explicitly supplies that evidence status.
        if "confidence_verification" not in result.metadata:
            trace = input_understanding if isinstance(input_understanding, dict) else {}
            semantic = result.metadata.get("semantic_intent", {})
            if not isinstance(semantic, dict):
                semantic = {}
            semantic_confidence = semantic.get("confidence")
            if isinstance(semantic_confidence, bool) or not isinstance(semantic_confidence, (int, float)):
                semantic_confidence = None
            factual_status = self.confidence_verification_brain.factual_status_for_response(
                result.verification_status, result.metadata
            )
            ambiguity = result.metadata.get("ambiguity_detection", {})
            if not isinstance(ambiguity, dict):
                ambiguity = {}
            confidence_decision = self.confidence_verification_brain.assess(
                input_id=str(trace.get("input_id", "master-input")),
                text=text or "",
                intent_confidence=float(result.intent_confidence),
                language_confidence=float(trace.get("language_confidence", 0.0)),
                input_confidence=float(trace.get("input_confidence", 1.0)),
                semantic_confidence=semantic_confidence,
                semantic_needs_clarification=bool(
                    semantic.get("needs_clarification", False)
                ),
                semantic_question=str(
                    semantic.get("clarification_question", "")
                ),
                ambiguity_question=str(
                    result.metadata.get("clarification_question", "")
                ),
                ambiguity_reasons=tuple(ambiguity.get("reasons", ())),
                factual_claim_status=factual_status,
            )
            result.metadata["confidence_verification"] = confidence_decision.to_dict()

        result.metadata.setdefault(
            "factual_verification_assessment",
            {
                "status": result.metadata["confidence_verification"]["factual_claim_status"],
                "verified": result.metadata["confidence_verification"]["factual_claim_status"] == "EVIDENCE_VERIFIED",
                "note": "Routing/permission verification is not proof of factual truth.",
            },
        )
        result.metadata.setdefault(
            "cognitive_attention",
            self._attention_trace(text, result),
        )
        try:
            assessment = self.cognitive_neural_architecture.assess(
                request=text or "",
                intent=result.intent,
                action=result.action,
                risk=result.risk,
                verification_status=result.verification_status,
                confirmation_required=result.confirmation_required,
            )
            result.metadata.setdefault(
                "cognitive_neural_architecture", assessment.to_dict()
            )
            try:
                council = self.three_brain_council.deliberate(
                    request=text or "",
                    answer=result.message or "",
                    intent=result.intent,
                    risk=result.risk,
                    verification_status=result.verification_status,
                )
                result.metadata["three_brain_council"] = council.to_dict()
            except Exception as exc:
                # The advisory council is non-authoritative and must never
                # interrupt a safe answer if a reviewer has an unexpected bug.
                result.metadata["three_brain_council"] = {
                    "version": ThreeBrainCouncil.VERSION,
                    "status": "review_unavailable",
                    "authority_changed": False,
                    "error_type": type(exc).__name__,
                }
        except (TypeError, ValueError):
            # Diagnostics must never turn a safe response into a failure.
            result.metadata.setdefault(
                "cognitive_neural_architecture",
                {"version": CognitiveNeuralArchitecture.VERSION,
                 "status": "assessment_unavailable", "authority_changed": False},
            )

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
        # Report the real bounded working-memory state after the interaction
        # has been activated. This is a read-only snapshot, not a promotion.
        try:
            working_memory = self.memory_brain.working_memory
            active_entries = working_memory.entries()
            result.metadata.setdefault(
                "working_memory",
                {
                    "capacity": working_memory.capacity,
                    "active_count": working_memory.count(),
                    "bounded": True,
                    "long_term_storage": False,
                    "top_active_memory_ids": [
                        entry.memory.memory_id for entry in active_entries[:5]
                    ],
                    "snapshot_after_interaction_activation": True,
                    "promotes_to_long_term": False,
                    "grants_permission": False,
                    "executes_actions": False,
                },
            )
        except (AttributeError, TypeError, ValueError):
            result.metadata.setdefault(
                "working_memory",
                {
                    "status": "snapshot_unavailable",
                    "grants_permission": False,
                    "executes_actions": False,
                },
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
