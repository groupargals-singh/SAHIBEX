"""SAHIBEX-owned internal specialist roles (not independent Child Brains).

These role definitions are part of the Mother Brain runtime and do not
instantiate separate identities, independent constitutions, or child births.
The registry is deliberately descriptive: a role is marked executable only
when a real handler is registered by the runtime. It never grants permission.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from time import perf_counter

from core.diagnostics.flow_tracker import record_dispatch


@dataclass(frozen=True)
class InternalBrainRole:
    role_id: str
    purpose: str
    capabilities: tuple[str, ...]
    handler_registered: bool


@dataclass(frozen=True)
class InternalBrainDispatch:
    accepted: bool
    role_id: str
    request: str
    result: Any = None
    reason: str = ""


InternalHandler = Callable[[str, dict[str, Any]], Any]


class InternalBrainTeam:
    """In-process role registry for SAHIBEX's own army/labor specialists."""

    ROLE_PURPOSES = {
        "reading": ("Read and extract source material", ("read", "extract")),
        "document_file": ("Summarize and extract explicitly supplied document text without filesystem access", ("summarize_supplied_text", "extract_points")),
        "system_architecture": ("Review an explicitly supplied architecture description without claiming full repository inspection", ("architecture_review", "dependency_risk_scan")),
        "performance_resource": ("Assess explicitly supplied resource metrics against conservative thresholds", ("resource_assessment", "capacity_warnings")),
        "privacy_data_governance": ("Check supplied access metadata and minimum-necessary field scope", ("scope_check", "data_minimization")),
        "human_handoff": ("Prepare a transparent handoff summary and identify unresolved decisions", ("handoff_summary", "blockers", "approval_needed")),
        "backup_continuity": ("Assess explicitly supplied backup and recovery evidence without modifying files", ("backup_evidence_review", "recovery_readiness", "restore_test_status")),
        "web_tools": ("Discover registered tools through Tool Brain without executing them or granting permissions", ("registered_tool_discovery", "read_only_capability_summary", "permission_boundary")),
        "automation": ("Validate a proposed workflow as bounded steps without executing or scheduling it", ("workflow_validation", "step_bounds", "approval_boundary")),
        "health_monitor": ("Read lifecycle health and emergency-stop state without changing runtime state", ("lifecycle_health", "safety_latch_status", "read_only_diagnostics")),
        "audit": ("Summarize recent audit metadata while redacting request bodies and sensitive details", ("audit_metadata_review", "bounded_recent_events", "redacted_output")),
        "brain_creator": ("Draft a proposed specialist profile for human review without registering or birthing it", ("profile_draft", "capability_bounds", "human_review_required")),
        "evaluation": ("Evaluate caller-supplied checks and evidence without inventing test results", ("criteria_evaluation", "evidence_presence", "limitations_report")),
        "personal_assistant": ("Structure user-supplied tasks into a proposed checklist without performing external actions", ("task_breakdown", "missing_details", "approval_boundary")),
        "creative": ("Turn explicit creative requirements into a bounded creative brief and idea seeds", ("creative_brief", "idea_seeds", "constraint_tracking")),
        "collaboration": ("Compare supplied specialist reports and surface conflicts without silently choosing a winner", ("report_normalization", "conflict_detection", "provenance_preservation")),
        "finance": ("Summarize caller-supplied income and expense figures without investment advice or transactions", ("cashflow_summary", "input_validation", "financial_safety_boundary")),
        "localization": ("Check supplied localized strings for completeness without claiming translation quality", ("locale_validation", "missing_translation_detection", "placeholder_consistency")),
        "accessibility": ("Review supplied UI component metadata against basic accessibility checks", ("label_and_alt_checks", "keyboard_access_review", "contrast_and_focus_flags")),
        "conversation": ("Extract bounded conversation context and the latest explicit user request", ("turn_validation", "latest_request_extraction", "context_limits")),
        "policy": ("Evaluate supplied policy rules against a request without granting authority", ("rule_matching", "review_required_default", "permission_boundary")),
        "personalization": ("Normalize explicit task-scoped preferences without persistent profile writes", ("preference_validation", "task_scope", "no_persistent_write")),
        "recovery": ("Assess supplied recovery evidence and prerequisites without restoring or rolling back", ("checkpoint_review", "restore_prerequisites", "fail_closed")),
        "knowledge_graph": ("Validate supplied entity-relation triples and surface inconsistent edges without persistence", ("triple_validation", "relationship_conflicts", "provenance_fields")),
        "database": ("Review supplied schema metadata for basic naming and structural consistency without database access", ("schema_validation", "duplicate_detection", "no_migration_execution")),
        "scheduling": ("Build a proposed dependency-aware relative schedule without calendar writes", ("duration_validation", "dependency_order", "proposal_only")),
        "ui_ux_design": ("Review supplied interface requirements and flows for clarity and missing states", ("screen_flow_review", "empty_error_states", "usability_gaps")),
        "scientific_research": ("Structure a supplied hypothesis into a transparent research plan without inventing findings", ("hypothesis_structure", "variable_mapping", "methodology_gaps")),
        "simulation": ("Compute bounded deterministic what-if scenarios from explicit caller-supplied equations", ("scenario_validation", "deterministic_projection", "assumption_disclosure")),
        "api_integration": ("Validate an API integration proposal without network calls or credential handling", ("endpoint_contract_review", "method_validation", "no_network_execution")),
        "devops_deployment": ("Review deployment prerequisites and rollback plans without building or deploying", ("release_checklist", "rollback_review", "approval_boundary")),
        "multimodal_coordination": ("Normalize supplied text, image and audio observations while preserving source provenance", ("observation_normalization", "source_provenance", "untrusted_input_boundary")),
        "notification_events": ("Validate proposed notification event metadata without sending or scheduling messages", ("event_validation", "payload_bounds", "no_delivery")),
        "compliance": ("Review caller-supplied requirements and evidence without claiming legal certification", ("evidence_mapping", "gap_reporting", "no_certification")),
        "experiment_benchmark": ("Compare supplied benchmark measurements without executing experiments or inventing metrics", ("metric_validation", "comparative_summary", "reproducibility_limits")),
        "audio": ("Transcribe consent-provided bounded PCM WAV through the local offline recognizer", ("local_offline_asr", "audio_path_validation", "transcript_provenance")),
        "vision": ("Extract bounded text from a consent-provided image through the local OCR runtime with provenance", ("local_ocr", "image_path_validation", "source_hash_provenance")),
        "knowledge": ("Retrieve persisted knowledge with verification, conflict and freshness filters", ("scoped_retrieval", "verified_only_filter", "provenance_summary")),
        "voice": ("Report readiness of configured local speech input/output components without claiming a live microphone-to-speaker round trip", ("local_asr_readiness", "local_tts_readiness", "voice_gate_status")),
        "language": ("Detect likely language/script and provide a language-consistency signal without claiming translation", ("language_detection", "script_detection", "reply_language_policy")),
        "math": ("Resolve a narrowly supported deterministic arithmetic expression without dynamic evaluation", ("safe_arithmetic", "input_bounds", "expression_validation")),
        "data_analysis": ("Compute bounded descriptive statistics from explicitly supplied tabular rows without external data access", ("numeric_summary", "missing_value_report", "input_validation")),
        "code_review": ("Perform a bounded heuristic review of explicitly supplied diff text without executing or modifying code", ("risk_pattern_scan", "change_review", "review_limitations")),
        "planning": ("Validate a bounded task dependency graph and produce a deterministic proposed order without executing tasks", ("dependency_validation", "topological_order", "cycle_detection")),
        "app_builder": ("Draft an application structure from explicit requirements without writing files, building or deploying", ("screen_outline", "component_outline", "requirements_gaps")),
        "debugging": ("Triage bounded caller-supplied failure reports and identify missing reproducibility evidence without executing or changing code", ("failure_triage", "reproduction_gaps", "diagnostic_next_steps")),
        "knowledge_maintenance": ("Assess supplied knowledge metadata for staleness, duplicates and conflicts without modifying records", ("staleness_review", "duplicate_detection", "conflict_review")),
        "decision_analysis": ("Compare caller-supplied options against explicit weighted criteria without inventing scores", ("weighted_comparison", "tradeoff_summary", "tie_detection")),
        "uncertainty": ("Identify missing evidence, unresolved conflicts and limits from supplied claim metadata", ("uncertainty_assessment", "evidence_gaps", "confidence_limits")),
        "evidence_fact_checking": ("Compare supplied claims against explicit evidence and report conflicts and uncertainty", ("claim_review", "evidence_mapping", "conflict_detection")),
        "research": ("Discover public sources and collect evidence", ("research", "source_check")),
        "learning": ("Consolidate verified learning and feedback", ("learn", "memory")),
        "reasoning": ("Compare options and construct explanations", ("reason", "plan")),
        "teaching": ("Explain a supplied topic in bounded steps and examples", ("explain", "examples", "comprehension_check")),
        "coding": ("Create or review code through authorized tools", ("code", "review")),
        "text_development": ("Draft bounded text/code/model candidates in an isolated queue for Mother Brain review; never execute or promote", ("candidate_drafting", "sandbox_queue", "mother_review_required", "rollback_ready_promotion")),
        "testing": ("Analyze supplied results from tests executed through authorized tooling", ("test_report", "failure_analysis")),
        "verification": ("Check claims, evidence, conflicts and uncertainty", ("verify", "evidence")),
        "memory": ("Retrieve and organize persistent context", ("memory", "retrieve")),
        "security": ("Review boundaries, permissions and suspicious inputs", ("security", "audit")),
        "orchestration": ("Split work into tasks and coordinate specialist results", ("plan", "coordinate")),
    }

    def __init__(self) -> None:
        self._handlers: dict[str, InternalHandler] = {}

    def roles(self) -> tuple[InternalBrainRole, ...]:
        return tuple(
            InternalBrainRole(role_id, purpose, capabilities, role_id in self._handlers)
            for role_id, (purpose, capabilities) in self.ROLE_PURPOSES.items()
        )

    def register_handler(self, role_id: str, handler: InternalHandler) -> None:
        if role_id not in self.ROLE_PURPOSES:
            raise ValueError(f"unknown internal brain role: {role_id}")
        if not callable(handler):
            raise TypeError("internal brain handler must be callable")
        if role_id in self._handlers:
            raise ValueError(f"handler already registered for role: {role_id}")
        self._handlers[role_id] = handler

    def dispatch(
        self,
        role_id: str,
        request: str,
        context: dict[str, Any] | None = None,
        *,
        authorization_passed: bool = False,
        verification_passed: bool = False,
    ) -> InternalBrainDispatch:
        if role_id not in self.ROLE_PURPOSES:
            return InternalBrainDispatch(False, role_id, request, reason="unknown internal role")
        if not isinstance(authorization_passed, bool) or not isinstance(verification_passed, bool):
            return InternalBrainDispatch(
                False,
                role_id,
                str(request),
                reason="authorization and verification gates must be explicit booleans",
            )
        if context is not None and not isinstance(context, dict):
            return InternalBrainDispatch(
                False, role_id, str(request), reason="context must be a dictionary"
            )
        if not isinstance(request, str) or not request.strip():
            return InternalBrainDispatch(False, role_id, str(request), reason="non-empty request required")
        handler = self._handlers.get(role_id)
        if handler is None:
            return InternalBrainDispatch(False, role_id, request, reason="role exists in architecture but has no executable handler registered")
        if not authorization_passed:
            return InternalBrainDispatch(False, role_id, request, reason="upstream authorization is required before handler execution")
        if not verification_passed:
            return InternalBrainDispatch(False, role_id, request, reason="upstream request verification is required before handler execution")
        started = perf_counter()
        try:
            result = handler(request, dict(context or {}))
        except Exception as exc:
            record_dispatch(role_id, f"HANDLER_ERROR:{type(exc).__name__}", (perf_counter() - started) * 1000)
            return InternalBrainDispatch(False, role_id, request, reason=f"handler failed: {type(exc).__name__}: {exc}")
        record_dispatch(role_id, "HANDLER_RETURNED_UNVERIFIED", (perf_counter() - started) * 1000)
        return InternalBrainDispatch(True, role_id, request, result=result, reason="handler completed; output still requires task-appropriate verification")

    @staticmethod
    def creates_independent_child_brain() -> bool:
        return False

    @staticmethod
    def grants_permissions() -> bool:
        return False

    @staticmethod
    def can_modify_constitution() -> bool:
        return False

    @staticmethod
    def can_self_birth() -> bool:
        return False

    def specialist_catalogue_coverage(self) -> dict[str, tuple[str, ...]]:
        """Return live handler coverage; this is introspection, not dispatch."""
        from core.brain.specialist_catalogue import runtime_coverage_from_roles

        return runtime_coverage_from_roles(self.roles())
