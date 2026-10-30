"""Declarative catalogue for SAHIBEX specialist roles.

Catalogue entries are capability descriptions, NOT executable handlers or permissions.
Actual execution remains behind the existing router, permission gateway and verifier.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SpecialistProfile:
    role_id: str
    department: str
    purpose: str
    input_contract: str = "task + scoped context + constraints"
    output_contract: str = "result + evidence + uncertainty + status"
    model_policy: str = "reuse_loaded_model; escalate_only_if_needed"
    memory_scope: str = "task_scoped; no_cross_user_or_child_access"
    tools: tuple[str, ...] = ()
    executable_handler_required: bool = True


# Stable role IDs are API identifiers; labels may change without breaking callers.
_ROLE_ROWS = (
    # Existing core specialist concepts
    ("learning", "knowledge", "Consolidate verified learning and feedback"),
    ("teaching", "knowledge", "Explain concepts and adapt lessons to the learner"),
    ("coding", "engineering", "Create or explain code through authorized tools"),
    ("app_builder", "engineering", "Plan application structure, screens and components"),
    ("thinking", "reasoning", "Compare alternatives and construct explanations"),
    ("reading", "knowledge", "Read, summarize and extract source material"),
    ("research", "knowledge", "Discover sources and collect evidence"),
    ("vision", "perception", "Interpret images only through a configured vision backend"),
    ("audio", "perception", "Analyze audio through an available audio backend"),
    ("voice", "perception", "Coordinate speech recognition and speech output"),
    ("language", "knowledge", "Handle language understanding and translation"),
    ("knowledge", "knowledge", "Retrieve and organize verified knowledge"),
    ("memory", "core", "Retrieve and maintain scoped memories"),
    ("verification", "trust", "Check claims, evidence, conflicts and uncertainty"),
    ("debugging", "engineering", "Diagnose failures from reproducible evidence"),
    ("testing", "engineering", "Design tests and analyze executed test results"),
    ("web_tools", "operations", "Use registered tools and approved web capabilities"),
    ("data_analysis", "reasoning", "Analyze datasets and report limitations"),
    ("math", "reasoning", "Solve and verify mathematical tasks"),
    ("planning", "reasoning", "Build plans with dependencies and acceptance criteria"),
    ("automation", "operations", "Design approved repeatable workflows"),
    ("security", "trust", "Review security boundaries and suspicious inputs"),
    ("health_monitor", "operations", "Monitor runtime health and report degradation"),
    ("audit", "trust", "Record provenance, actions and acceptance evidence"),
    ("brain_creator", "governance", "Propose specialist definitions for controlled review"),
    ("evaluation", "trust", "Benchmark outputs against explicit criteria"),
    ("finance", "domain", "Analyze financial information with uncertainty and safeguards"),
    ("personal_assistant", "interaction", "Coordinate user-directed personal tasks"),
    ("creative", "creation", "Generate and refine original creative work"),
    ("collaboration", "coordination", "Coordinate tasks and reconcile specialist outputs"),
    ("recovery", "operations", "Plan safe recovery, checkpoints and rollback"),
    ("policy", "governance", "Check requests against project policies"),
    # Additional specialist roles
    ("orchestration", "coordination", "Decompose tasks and coordinate specialist execution"),
    ("evidence_fact_checking", "trust", "Separate evidence-backed facts from inference"),
    ("system_architecture", "engineering", "Review modules, dependencies and data-flow"),
    ("privacy_data_governance", "trust", "Enforce data minimization, retention and isolation"),
    ("performance_resource", "operations", "Schedule work under RAM, CPU, GPU and latency limits"),
    ("backup_continuity", "operations", "Validate backups, checkpoints and recovery paths"),
    ("conversation", "interaction", "Resolve conversational intent and local context"),
    ("personalization", "interaction", "Apply explicitly permitted user preferences"),
    ("knowledge_graph", "knowledge", "Represent entities and verified relationships"),
    ("document_file", "knowledge", "Process documents and structured files"),
    ("database", "engineering", "Design and validate schemas, queries and migrations"),
    ("api_integration", "engineering", "Integrate external APIs behind permission controls"),
    ("ui_ux_design", "creation", "Design usable interfaces and navigation"),
    ("devops_deployment", "operations", "Build, package and deploy through approved workflows"),
    ("code_review", "engineering", "Review maintainability, defects and risky changes"),
    ("scientific_research", "knowledge", "Structure hypotheses and research methodology"),
    ("scheduling", "coordination", "Schedule work and resolve dependency constraints"),
    ("simulation", "reasoning", "Explore hypothetical outcomes without real-world actions"),
    ("decision_analysis", "reasoning", "Compare choices, risks and trade-offs"),
    ("uncertainty", "trust", "Identify ambiguity, missing evidence and confidence limits"),
    ("multimodal_coordination", "perception", "Combine text, image and audio observations with provenance"),
    ("accessibility", "interaction", "Review accessibility and alternative interaction paths"),
    ("localization", "knowledge", "Handle locale-sensitive language and formatting"),
    ("notification_events", "operations", "Coordinate approved notifications and scheduled events"),
    ("compliance", "governance", "Review applicable rules and project requirements"),
    ("experiment_benchmark", "trust", "Compare models and system versions reproducibly"),
    ("human_handoff", "interaction", "Request clarification or human approval when required"),
    ("knowledge_maintenance", "knowledge", "Identify stale, duplicate and conflicting knowledge"),
    ("text_development", "engineering", "Draft isolated candidates for Mother Brain review; never execute or self-promote"),
)


def build_catalogue() -> tuple[SpecialistProfile, ...]:
    """Return immutable profiles; no model, tool or permission is activated."""
    profiles = tuple(SpecialistProfile(role_id, department, purpose)
                     for role_id, department, purpose in _ROLE_ROWS)
    ids = [profile.role_id for profile in profiles]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate specialist role_id in catalogue")
    return profiles


SPECIALIST_CATALOGUE = build_catalogue()
SPECIALIST_BY_ID = {profile.role_id: profile for profile in SPECIALIST_CATALOGUE}


def get_specialist(role_id: str) -> SpecialistProfile | None:
    if not isinstance(role_id, str):
        raise TypeError("role_id must be a string")
    return SPECIALIST_BY_ID.get(role_id.strip().lower())


def list_specialists(*, department: str | None = None) -> tuple[SpecialistProfile, ...]:
    if department is None:
        return SPECIALIST_CATALOGUE
    if not isinstance(department, str) or not department.strip():
        raise ValueError("department must be a non-empty string")
    normalized = department.strip().lower()
    return tuple(profile for profile in SPECIALIST_CATALOGUE
                 if profile.department == normalized)


def runtime_coverage(registered_handler_ids: Iterable[str]) -> dict[str, tuple[str, ...]]:
    """Compare the design catalogue to actual runtime handlers without guessing."""
    registered = {item.strip().lower() for item in registered_handler_ids
                  if isinstance(item, str) and item.strip()}
    implemented = tuple(p.role_id for p in SPECIALIST_CATALOGUE if p.role_id in registered)
    missing = tuple(p.role_id for p in SPECIALIST_CATALOGUE if p.role_id not in registered)
    return {"handler_registered": implemented, "handler_missing": missing}


# Explicit aliases only: similar names are not treated as equivalent unless reviewed.
INTERNAL_ROLE_ALIASES = {
    "reasoning": "thinking",
}


def runtime_coverage_from_roles(roles: Iterable[object]) -> dict[str, tuple[str, ...]]:
    """Map live InternalBrainTeam role records to catalogue coverage.

    A role counts as implemented only when the runtime record explicitly reports
    handler_registered=True. A matching role name without a handler is missing.
    """
    live: dict[str, bool] = {}
    for role in roles:
        role_id = getattr(role, "role_id", None)
        handler_registered = getattr(role, "handler_registered", None)
        if not isinstance(role_id, str) or not isinstance(handler_registered, bool):
            continue
        catalogue_id = INTERNAL_ROLE_ALIASES.get(role_id, role_id)
        live[catalogue_id] = live.get(catalogue_id, False) or handler_registered

    implemented = tuple(p.role_id for p in SPECIALIST_CATALOGUE if live.get(p.role_id) is True)
    missing = tuple(p.role_id for p in SPECIALIST_CATALOGUE if live.get(p.role_id) is not True)
    return {
        "implemented": implemented,
        "missing_or_unwired": missing,
        "catalogue_total": (str(len(SPECIALIST_CATALOGUE)),),
        "implemented_count": (str(len(implemented)),),
        "missing_count": (str(len(missing)),),
    }
