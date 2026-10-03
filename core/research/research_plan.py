from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ResearchStep:
    """
    One controlled step inside a research plan.
    """

    step_id: str
    description: str
    source_types: List[str] = field(default_factory=list)
    required: bool = True
    metadata: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.step_id, str) or not self.step_id.strip():
            raise ValueError("step_id must be a non-empty string")

        if (
            not isinstance(self.description, str)
            or not self.description.strip()
        ):
            raise ValueError(
                "description must be a non-empty string"
            )

        if not isinstance(self.source_types, list):
            raise ValueError("source_types must be a list")

        for source_type in self.source_types:
            if (
                not isinstance(source_type, str)
                or not source_type.strip()
            ):
                raise ValueError(
                    "source_types must contain non-empty strings"
                )

        if not isinstance(self.required, bool):
            raise ValueError("required must be boolean")

        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")


@dataclass(frozen=True)
class ResearchPlan:
    """
    Validated execution plan for one research job.

    The plan itself does not execute anything.

    It defines:
        - which job the plan belongs to
        - the original research objective
        - ordered research steps
        - plan metadata
    """

    plan_id: str
    job_id: str
    objective: str
    steps: List[ResearchStep]
    metadata: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.plan_id, str) or not self.plan_id.strip():
            raise ValueError("plan_id must be a non-empty string")

        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise ValueError("job_id must be a non-empty string")

        if (
            not isinstance(self.objective, str)
            or not self.objective.strip()
        ):
            raise ValueError(
                "objective must be a non-empty string"
            )

        if not isinstance(self.steps, list):
            raise ValueError("steps must be a list")

        if not self.steps:
            raise ValueError(
                "research plan must contain at least one step"
            )

        for step in self.steps:
            if not isinstance(step, ResearchStep):
                raise ValueError(
                    "steps must contain ResearchStep objects"
                )

        step_ids = [step.step_id for step in self.steps]

        if len(step_ids) != len(set(step_ids)):
            raise ValueError(
                "research plan step_id values must be unique"
            )

        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def required_steps(self) -> List[ResearchStep]:
        return [
            step
            for step in self.steps
            if step.required
        ]

    @property
    def optional_steps(self) -> List[ResearchStep]:
        return [
            step
            for step in self.steps
            if not step.required
        ]

    def get_step(self, step_id: str) -> ResearchStep:
        if not isinstance(step_id, str) or not step_id.strip():
            raise ValueError(
                "step_id must be a non-empty string"
            )

        for step in self.steps:
            if step.step_id == step_id:
                return step

        raise KeyError(
            f"unknown research plan step: {step_id}"
        )

    def snapshot(self) -> Dict[str, object]:
        return {
            "plan_id": self.plan_id,
            "job_id": self.job_id,
            "objective": self.objective,
            "step_count": self.step_count,
            "steps": [
                {
                    "step_id": step.step_id,
                    "description": step.description,
                    "source_types": list(step.source_types),
                    "required": step.required,
                    "metadata": dict(step.metadata),
                }
                for step in self.steps
            ],
            "metadata": dict(self.metadata),
        }
