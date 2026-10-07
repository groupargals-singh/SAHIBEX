from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConstraintReasoningResult:
    conclusion: Any
    valid: bool
    steps: tuple[str, ...]
    conflicts: tuple[str, ...]
    metadata: dict[str, Any]


class ConstraintReasoningEngine:
    """Read-only multi-step and constraint reasoning."""

    def solve(self, *, steps: list[str], constraints: list[bool], conclusion: Any) -> ConstraintReasoningResult:
        if not isinstance(steps, list) or not all(isinstance(x, str) and x.strip() for x in steps):
            raise TypeError("steps must be a list of non-empty strings")
        if not isinstance(constraints, list) or not all(isinstance(x, bool) for x in constraints):
            raise TypeError("constraints must be a list of bool")
        valid = all(constraints)
        conflicts = tuple(f"constraint_{i}" for i, value in enumerate(constraints) if not value)
        return ConstraintReasoningResult(conclusion, valid, tuple(steps), conflicts, {"step_count": len(steps), "constraint_count": len(constraints)})

    def detect_conflict(self, *, claims: list[Any]) -> tuple[bool, tuple[Any, ...]]:
        if not isinstance(claims, list):
            raise TypeError("claims must be a list")
        unique = []
        for claim in claims:
            if claim not in unique:
                unique.append(claim)
        return len(unique) > 1, tuple(unique)
