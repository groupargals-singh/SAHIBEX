from dataclasses import dataclass
import re


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float
    entities: dict[str, str]


class IntentEngine:
    """Deterministic request classifier; it never authorizes execution."""

    PATTERNS = {
        "system_status": [
            r"\bstatus\b", r"\bhow are you\b", r"\bstate\b",
            r"सिस्टम की स्थिति", r"सिस्टम स्टेटस",
        ],
        "search": [
            r"\bsearch\b", r"\bfind\b", r"\blook up\b",
            r"\bweb\b", r"\binternet\b", r"\bresearch\b",
            r"आज.*(?:नया|ताज़ा|ताजा|अपडेट)",
            r"(?:नवीनतम|ताज़ा जानकारी|ताजा जानकारी|लेटेस्ट अपडेट)",
            r"(?:इंटरनेट|वेब) पर (?:खोज|ढूँढ|ढूंढ|देख)",
            r"(?:रिसर्च|शोध) करो",
        ],
        "learn": [
            r"\blearn\b", r"\blearning\b", r"\bstudy\b",
            r"\bteach me\b", r"\bhelp me learn\b",
            r"\bhelp me understand\b",
            r"मुझे .* सिखाओ", r"सीखना चाहता", r"सीखना चाहती",
        ],
        "code": [
            r"\bwrite\s+(?:a\s+)?(?:python|javascript|java|c\+\+|rust|go)\b",
            r"\bcode\b", r"\bprogram\b", r"\bprogramming\b",
            r"\bscript\b", r"\bdebug\b", r"\bpython\b",
            r"\bjavascript\b", r"\bsource code\b",
        ],
        "create": [
            r"\bcreate\b", r"\bmake\b", r"\bbuild\b",
            r"\bgenerate\b", r"\bdesign\b",
        ],
        "explain": [
            r"\bexplain\b", r"\bwhat is\b", r"\bhow does\b",
            r"\bwhy\b", r"क्यों", r"क्या है", r"समझाओ",
            r"बताओ",
        ],
        "file_operation": [
            r"\bfile\b", r"\bfolder\b", r"\bdirectory\b",
            r"\bopen file\b", r"\bread file\b", r"\bview file\b",
        ],
    }

    INTENT_PRIORITY = {
        "system_status": 100, "code": 90, "search": 80,
        "file_operation": 70, "explain": 60, "create": 50,
        "learn": 95,
    }

    def detect(self, text: str) -> IntentResult:
        normalized = text.lower().strip()
        if not normalized:
            return IntentResult(intent="empty", confidence=1.0, entities={})

        scores: dict[str, int] = {}
        for intent, patterns in self.PATTERNS.items():
            score = sum(1 for pattern in patterns if re.search(pattern, normalized))
            if score:
                scores[intent] = score

        if not scores:
            return IntentResult(intent="general_request", confidence=0.30, entities={})

        best_intent = max(
            scores,
            key=lambda intent: (scores[intent], self.INTENT_PRIORITY.get(intent, 0)),
        )
        confidence = min(0.95, 0.50 + scores[best_intent] * 0.15)
        return IntentResult(intent=best_intent, confidence=confidence, entities={})
