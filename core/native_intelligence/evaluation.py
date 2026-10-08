from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class EvaluationResult:
    passed: bool
    score: float
    checks: dict[str, bool] = field(default_factory=dict)

    def require_pass(self) -> None:
        if not self.passed:
            raise AssertionError(f"evaluation failed: {self.checks}")


class EvaluationSuite:
    REQUIRED_TASKS = {
        "reasoning", "tool_use", "memory_use", "verification",
    }

    def __init__(self) -> None:
        self._checks: dict[str, Callable[[], bool]] = {}

    def add_check(self, name: str, check: Callable[[], bool]) -> None:
        if not name.strip():
            raise ValueError("evaluation check name is required")
        self._checks[name] = check

    def run(self) -> EvaluationResult:
        checks: dict[str, bool] = {}
        for name, check in self._checks.items():
            try:
                checks[name] = bool(check())
            except Exception:
                checks[name] = False
        score = sum(checks.values()) / len(checks) if checks else 0.0
        return EvaluationResult(bool(checks) and all(checks.values()), score, checks)

    def run_dataset_contract(self, tasks: set[str]) -> EvaluationResult:
        checks = {task: task in tasks for task in self.REQUIRED_TASKS}
        score = sum(checks.values()) / len(checks)
        return EvaluationResult(all(checks.values()), score, checks)
