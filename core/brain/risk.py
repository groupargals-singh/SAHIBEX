from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from core.policies.approval import RiskLevel


RISK_VERSION = "P1-38-1"


@dataclass(frozen=True)
class RiskInput:
    likelihood: float
    impact: float
    exposure: float
    irreversibility: float
    uncertainty: float
    input_id: str


@dataclass(frozen=True)
class RiskAssessment:
    input_id: str
    risk_score: float
    level: RiskLevel
    reason: str
    assessment_id: str = field(default_factory=lambda: str(uuid4()))
    version: str = RISK_VERSION

    @property
    def high_risk(self) -> bool:
        return self.level in (
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        )


class RiskEngine:
    """
    Cognitive risk assessment.

    This layer:
    - assesses potential risk
    - does not authorize actions
    - does not execute actions
    - does not grant permission
    - does not replace PermissionEngine
    - does not modify the Constitution
    """

    LIKELIHOOD_WEIGHT = 0.25
    IMPACT_WEIGHT = 0.30
    EXPOSURE_WEIGHT = 0.15
    IRREVERSIBILITY_WEIGHT = 0.20
    UNCERTAINTY_WEIGHT = 0.10

    def assess(self, risk_input: RiskInput) -> RiskAssessment:
        self._validate(risk_input)

        score = (
            risk_input.likelihood * self.LIKELIHOOD_WEIGHT
            + risk_input.impact * self.IMPACT_WEIGHT
            + risk_input.exposure * self.EXPOSURE_WEIGHT
            + risk_input.irreversibility * self.IRREVERSIBILITY_WEIGHT
            + risk_input.uncertainty * self.UNCERTAINTY_WEIGHT
        )

        score = round(max(0.0, min(1.0, score)), 4)
        level = self._level(score)

        reason = (
            f"risk={level.value}; "
            f"score={score:.4f}"
        )

        return RiskAssessment(
            input_id=risk_input.input_id.strip(),
            risk_score=score,
            level=level,
            reason=reason,
        )

    @staticmethod
    def _validate(risk_input: RiskInput) -> None:
        if not isinstance(risk_input, RiskInput):
            raise TypeError("risk_input must be RiskInput")

        if not isinstance(risk_input.input_id, str):
            raise TypeError("input_id must be a string")

        if not risk_input.input_id.strip():
            raise ValueError("input_id cannot be empty")

        values = (
            risk_input.likelihood,
            risk_input.impact,
            risk_input.exposure,
            risk_input.irreversibility,
            risk_input.uncertainty,
        )

        for value in values:
            if not isinstance(value, (int, float)):
                raise TypeError("risk signals must be numeric")

            if isinstance(value, bool):
                raise TypeError("risk signals cannot be bool")

            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(
                    "risk signals must be between 0 and 1"
                )

    @staticmethod
    def _level(score: float) -> RiskLevel:
        if score >= 0.80:
            return RiskLevel.CRITICAL

        if score >= 0.60:
            return RiskLevel.HIGH

        if score >= 0.35:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    @staticmethod
    def authorizes_actions() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def modifies_constitution() -> bool:
        return False

    @staticmethod
    def replaces_permission_engine() -> bool:
        return False


if __name__ == "__main__":
    engine = RiskEngine()

    result = engine.assess(
        RiskInput(
            likelihood=0.90,
            impact=0.90,
            exposure=0.80,
            irreversibility=0.80,
            uncertainty=0.70,
            input_id="demo",
        )
    )

    print(result)
