from dataclasses import dataclass
import re


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float
    entities: dict[str, str]


class IntentEngine:
    """
    Deterministic intent classifier for SAHIBEX.

    The classifier uses:
    1. Strong/specific patterns
    2. Normal patterns
    3. Match count
    4. Specificity priority

    Important:
    This layer only understands the request.
    It does not execute anything.
    """

    PATTERNS = {
        "system_status": [
            r"\bstatus\b",
            r"\bhow are you\b",
            r"\bstate\b",
        ],

        "search": [
            r"\bsearch\b",
            r"\bfind\b",
            r"\blook up\b",
            r"\bweb\b",
            r"\binternet\b",
            r"\bresearch\b",
        ],

        "learn": [
            r"\blearn\b",
            r"\blearning\b",
            r"\bstudy\b",
            r"\bteach me\b",
            r"\bhelp me learn\b",
            r"\bhelp me understand\b",
        ],

        "code": [
            r"\bwrite\s+(?:a\s+)?(?:python|javascript|java|c\+\+|rust|go)\b",
            r"\bcode\b",
            r"\bprogram\b",
            r"\bprogramming\b",
            r"\bscript\b",
            r"\bdebug\b",
            r"\bpython\b",
            r"\bjavascript\b",
            r"\bsource code\b",
        ],

        "create": [
            r"\bcreate\b",
            r"\bmake\b",
            r"\bbuild\b",
            r"\bgenerate\b",
            r"\bdesign\b",
        ],

        "explain": [
            r"\bexplain\b",
            r"\bwhat is\b",
            r"\bhow does\b",
            r"\bwhy\b",
        ],

        "file_operation": [
            r"\bfile\b",
            r"\bfolder\b",
            r"\bdirectory\b",
            r"\bopen file\b",
            r"\bread file\b",
            r"\bview file\b",
        ],
    }

    # Higher value = more specific intent.
    INTENT_PRIORITY = {
        "system_status": 100,
        "code": 90,
        "search": 80,
        "file_operation": 70,
        "explain": 60,
        "create": 50,
        "learn": 95,
    }

    def detect(self, text: str) -> IntentResult:
        normalized = text.lower().strip()

        if not normalized:
            return IntentResult(
                intent="empty",
                confidence=1.0,
                entities={},
            )

        scores: dict[str, int] = {}

        for intent, patterns in self.PATTERNS.items():
            score = 0

            for pattern in patterns:
                if re.search(pattern, normalized):
                    score += 1

            if score:
                scores[intent] = score

        if not scores:
            return IntentResult(
                intent="general_request",
                confidence=0.30,
                entities={},
            )

        best_intent = max(
            scores,
            key=lambda intent: (
                scores[intent],
                self.INTENT_PRIORITY.get(
                    intent,
                    0,
                ),
            ),
        )

        best_score = scores[best_intent]

        confidence = min(
            0.95,
            0.50 + (best_score * 0.15),
        )

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            entities={},
        )
