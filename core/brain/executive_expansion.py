from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PHASE_I_VERSION = "PHASE-I-EXECUTIVE-1"


@dataclass(frozen=True)
class ExecutiveAssessment:
    """Read-only executive/prefrontal assessment."""

    item_id: str
    name: str
    score: float
    ready: bool
    evidence: tuple[str, ...]
    blocked_reason: str = ""

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("item_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0 and 1")
        if not isinstance(self.ready, bool):
            raise TypeError("ready must be boolean")
        if not isinstance(self.evidence, tuple):
            raise TypeError("evidence must be a tuple")


class ExecutiveBrainExpansion:
    """Non-destructive executive-function coverage assessor.

    This layer evaluates prepared executive inputs only. It does not
    execute actions, grant permissions, alter the Constitution, or
    override Human Authority.
    """

    ITEM_NAMES = (
        "Executive Brain Foundation",
        "Goal Management",
        "Goal Prioritization",
        "Decision Formation",
        "Decision Evaluation",
        "Planning Control",
        "Task Decomposition",
        "Task Prioritization",
        "Resource Allocation",
        "Multi-Step Coordination",
        "Action Selection",
        "Risk-Aware Decision Support",
        "Uncertainty-Aware Decision Support",
        "Memory/Knowledge → Executive Decision",
        "Specialist Brain Coordination",
        "Execution Monitoring",
        "Human Approval / Executive Authority Boundary",
    )

    ITEM_IDS = tuple(f"I-{index:02d}" for index in range(1, 18))

    def assess(
        self,
        *,
        goal: str,
        priority: float = 0.5,
        decision_confidence: float = 0.5,
        risk: float = 0.0,
        uncertainty: float = 0.0,
        memory_available: bool = True,
        knowledge_available: bool = True,
        specialists_available: bool = True,
        execution_monitored: bool = True,
        human_approval_required: bool = True,
    ) -> tuple[ExecutiveAssessment, ...]:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("goal must be a non-empty string")

        numeric = {
            "priority": priority,
            "decision_confidence": decision_confidence,
            "risk": risk,
            "uncertainty": uncertainty,
        }
        for name, value in numeric.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be numeric")
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

        for name, value in {
            "memory_available": memory_available,
            "knowledge_available": knowledge_available,
            "specialists_available": specialists_available,
            "execution_monitored": execution_monitored,
            "human_approval_required": human_approval_required,
        }.items():
            if not isinstance(value, bool):
                raise TypeError(f"{name} must be boolean")

        priority = float(priority)
        decision_confidence = float(decision_confidence)
        risk = float(risk)
        uncertainty = float(uncertainty)

        scores = (
            1.0,
            1.0,
            priority,
            decision_confidence,
            decision_confidence * (1.0 - risk),
            1.0,
            1.0,
            priority,
            1.0 - risk,
            1.0,
            decision_confidence,
            1.0 - risk,
            1.0 - uncertainty,
            (float(memory_available) + float(knowledge_available)) / 2.0,
            float(specialists_available),
            float(execution_monitored),
            float(human_approval_required),
        )

        evidence = (
            ("goal_received",),
            ("goal_received",),
            ("priority_signal",),
            ("decision_confidence",),
            ("decision_confidence", "risk_signal"),
            ("planning_pipeline",),
            ("decomposition_pipeline",),
            ("priority_signal",),
            ("risk_signal",),
            ("coordination_pipeline",),
            ("decision_confidence",),
            ("risk_signal",),
            ("uncertainty_signal",),
            ("memory_available", "knowledge_available"),
            ("specialist_availability",),
            ("execution_monitoring",),
            ("human_authority_boundary",),
        )

        assessments = []
        for item_id, name, score, item_evidence in zip(
            self.ITEM_IDS, self.ITEM_NAMES, scores, evidence
        ):
            ready = score >= 0.5
            blocked_reason = "" if ready else "executive readiness below threshold"
            assessments.append(
                ExecutiveAssessment(
                    item_id=item_id,
                    name=name,
                    score=max(0.0, min(1.0, float(score))),
                    ready=ready,
                    evidence=item_evidence,
                    blocked_reason=blocked_reason,
                )
            )
        return tuple(assessments)

    @staticmethod
    def security_summary() -> dict[str, Any]:
        return {
            "read_only": True,
            "executes_actions": False,
            "grants_permission": False,
            "modifies_constitution": False,
            "overrides_human_authority": False,
        }
