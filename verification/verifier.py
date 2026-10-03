from dataclasses import dataclass
from typing import Any

from core.policies.approval import ActionType, RiskLevel


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    status: str
    checks_passed: int
    checks_failed: int
    reasons: list[str]
    metadata: dict[str, Any]


class VerificationEngine:
    """
    Independent verification layer for SAHIBEX.

    This engine never executes actions.

    It verifies:
    1. Intent confidence
    2. Action confidence
    3. Action/risk consistency
    4. Confirmation policy
    5. Dangerous-action safeguards
    6. Critical-action safeguards
    """

    MIN_INTENT_CONFIDENCE = 0.30
    MIN_EXECUTABLE_ACTION_CONFIDENCE = 0.60

    LOW_RISK_ACTIONS = {
        ActionType.RESPOND,
        ActionType.RESEARCH,
        ActionType.CREATE,
        ActionType.READ_FILE,
    }

    EXECUTABLE_ACTIONS = {
        ActionType.WRITE_FILE,
        ActionType.DELETE_FILE,
        ActionType.RUN_COMMAND,
        ActionType.NETWORK_ACCESS,
        ActionType.CREDENTIAL_USE,
        ActionType.SYSTEM_CHANGE,
        ActionType.FINANCIAL_ACTION,
    }

    EXPECTED_RISK = {
        ActionType.RESPOND: RiskLevel.LOW,
        ActionType.RESEARCH: RiskLevel.LOW,
        ActionType.CREATE: RiskLevel.LOW,
        ActionType.READ_FILE: RiskLevel.LOW,

        ActionType.WRITE_FILE: RiskLevel.MEDIUM,
        ActionType.NETWORK_ACCESS: RiskLevel.MEDIUM,

        ActionType.DELETE_FILE: RiskLevel.HIGH,
        ActionType.RUN_COMMAND: RiskLevel.HIGH,
        ActionType.CREDENTIAL_USE: RiskLevel.HIGH,

        ActionType.SYSTEM_CHANGE: RiskLevel.CRITICAL,
        ActionType.FINANCIAL_ACTION: RiskLevel.CRITICAL,
    }

    CONFIRMATION_REQUIRED = {
        ActionType.WRITE_FILE,
        ActionType.NETWORK_ACCESS,
        ActionType.DELETE_FILE,
        ActionType.RUN_COMMAND,
        ActionType.CREDENTIAL_USE,
        ActionType.SYSTEM_CHANGE,
        ActionType.FINANCIAL_ACTION,
    }

    def verify(
        self,
        *,
        intent: str,
        intent_confidence: float,
        action: ActionType,
        action_confidence: float,
        risk: RiskLevel,
        permission_allowed: bool,
        confirmation_required: bool,
    ) -> VerificationResult:

        reasons: list[str] = []
        passed = 0
        failed = 0

        # --------------------------------------------------
        # CHECK 1: Intent confidence
        # --------------------------------------------------

        if intent_confidence >= self.MIN_INTENT_CONFIDENCE:
            passed += 1
            reasons.append(
                "Intent confidence meets minimum threshold."
            )
        else:
            failed += 1
            reasons.append(
                "Intent confidence is below minimum threshold."
            )

        # --------------------------------------------------
        # CHECK 2: Action confidence
        #
        # Low-risk routing actions do not require the same
        # confidence threshold as executable actions.
        # --------------------------------------------------

        if action in self.LOW_RISK_ACTIONS:
            required_confidence = 0.30
        else:
            required_confidence = (
                self.MIN_EXECUTABLE_ACTION_CONFIDENCE
            )

        if action_confidence >= required_confidence:
            passed += 1
            reasons.append(
                "Action confidence meets the policy threshold."
            )
        else:
            failed += 1
            reasons.append(
                "Action confidence is below the policy threshold."
            )

        # --------------------------------------------------
        # CHECK 3: Action ↔ Risk consistency
        # --------------------------------------------------

        expected_risk = self.EXPECTED_RISK.get(action)

        if expected_risk is None:
            failed += 1
            reasons.append(
                "Unknown action has no defined risk policy."
            )

        elif expected_risk == risk:
            passed += 1
            reasons.append(
                "Action and risk classification are consistent."
            )

        else:
            failed += 1
            reasons.append(
                "Action and risk classification conflict."
            )

        # --------------------------------------------------
        # CHECK 4: Confirmation ↔ Policy consistency
        # --------------------------------------------------

        should_require_confirmation = (
            action in self.CONFIRMATION_REQUIRED
        )

        if should_require_confirmation == confirmation_required:
            passed += 1
            reasons.append(
                "Confirmation requirement matches policy."
            )
        else:
            failed += 1
            reasons.append(
                "Confirmation requirement conflicts with policy."
            )

        # --------------------------------------------------
        # CHECK 5: Dangerous action safeguard
        # --------------------------------------------------

        dangerous = risk in {
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        }

        if dangerous and permission_allowed:
            failed += 1
            reasons.append(
                "Dangerous action is allowed without "
                "a safe confirmation state."
            )
        else:
            passed += 1
            reasons.append(
                "Dangerous-action permission safeguard passed."
            )

        # --------------------------------------------------
        # CHECK 6: Critical action safeguard
        # --------------------------------------------------

        if (
            risk == RiskLevel.CRITICAL
            and permission_allowed
        ):
            failed += 1
            reasons.append(
                "Critical action is incorrectly allowed."
            )
        else:
            passed += 1
            reasons.append(
                "Critical-action safeguard passed."
            )

        # --------------------------------------------------
        # FINAL VERIFICATION
        # --------------------------------------------------

        if failed == 0:
            verified = True
            status = "VERIFIED"
        else:
            verified = False
            status = "VERIFICATION_FAILED"

        return VerificationResult(
            verified=verified,
            status=status,
            checks_passed=passed,
            checks_failed=failed,
            reasons=reasons,
            metadata={
                "intent": intent,
                "action": action.value,
                "risk": risk.value,
                "permission_allowed": permission_allowed,
                "confirmation_required": confirmation_required,
            },
        )
