from dataclasses import dataclass
import re

from core.policies.approval import ActionType


@dataclass(frozen=True)
class ActionClassification:
    action: ActionType
    confidence: float
    reason: str


class ActionClassifier:
    """
    Fine-grained action classifier.

    Important:
    This class ONLY classifies the requested action.
    It never executes anything.
    """

    PATTERNS = {
        ActionType.DELETE_FILE: [
            r"\bdelete\b",
            r"\bremove\b",
            r"\berase\b",
            r"\bdestroy\b",
            r"\buninstall\b",
        ],

        ActionType.WRITE_FILE: [
            r"\bwrite\b",
            r"\bsave\b",
            r"\bmodify\b",
            r"\bedit\b",
            r"\bupdate file\b",
            r"\boverwrite\b",
        ],

        ActionType.READ_FILE: [
            r"\bread file\b",
            r"\bopen file\b",
            r"\bview file\b",
            r"\bshow file\b",
            r"\bread\b",
        ],

        ActionType.RUN_COMMAND: [
            r"\brun command\b",
            r"\bexecute command\b",
            r"\bexecute\b",
            r"\brun\b",
            r"\bshell\b",
            r"\bterminal\b",
        ],

        ActionType.CREDENTIAL_USE: [
            r"\bpassword\b",
            r"\bapi key\b",
            r"\bapi token\b",
            r"\bsecret\b",
            r"\bcredential\b",
            r"\baccess token\b",
        ],

        ActionType.SYSTEM_CHANGE: [
            r"\bsystem change\b",
            r"\bchange system\b",
            r"\binstall system\b",
            r"\bconfigure system\b",
            r"\bchange configuration\b",
        ],

        ActionType.NETWORK_ACCESS: [
            r"\bconnect to\b",
            r"\bnetwork access\b",
            r"\bdownload\b",
            r"\bupload\b",
            r"\bhttp\b",
            r"\bhttps\b",
        ],

        ActionType.FINANCIAL_ACTION: [
            r"\btransfer money\b",
            r"\bsend money\b",
            r"\bmake payment\b",
            r"\bpay\b",
            r"\bbuy\b",
            r"\bsell\b",
        ],
    }

    def classify(self, text: str) -> ActionClassification:
        normalized = text.lower().strip()

        if not normalized:
            return ActionClassification(
                action=ActionType.RESPOND,
                confidence=1.0,
                reason="Empty input defaults to response.",
            )

        matches: list[tuple[ActionType, int]] = []

        for action, patterns in self.PATTERNS.items():
            score = 0

            for pattern in patterns:
                if re.search(pattern, normalized):
                    score += 1

            if score:
                matches.append((action, score))

        if not matches:
            return ActionClassification(
                action=ActionType.RESPOND,
                confidence=0.50,
                reason="No executable action pattern detected.",
            )

        # Highest pattern score wins.
        # If scores tie, use the safer action.
        matches.sort(
            key=lambda item: (
                item[1],
                self._safety_priority(item[0]),
            ),
            reverse=True,
        )

        action, score = matches[0]

        confidence = min(
            0.98,
            0.60 + (score * 0.10),
        )

        return ActionClassification(
            action=action,
            confidence=confidence,
            reason=f"Matched {score} action pattern(s).",
        )

    @staticmethod
    def _safety_priority(action: ActionType) -> int:
        """
        Higher number means safer fallback when pattern scores tie.
        """

        priorities = {
            ActionType.RESPOND: 100,
            ActionType.READ_FILE: 90,
            ActionType.RESEARCH: 80,
            ActionType.CREATE: 70,
            ActionType.NETWORK_ACCESS: 50,
            ActionType.WRITE_FILE: 40,
            ActionType.RUN_COMMAND: 30,
            ActionType.DELETE_FILE: 20,
            ActionType.CREDENTIAL_USE: 10,
            ActionType.SYSTEM_CHANGE: 5,
            ActionType.FINANCIAL_ACTION: 1,
        }

        return priorities.get(action, 0)
