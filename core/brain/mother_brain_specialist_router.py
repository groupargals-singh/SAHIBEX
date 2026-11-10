"""Conservative task-to-role routing for the Mother Brain.

Selection is advisory and deterministic. It never authorizes execution, invokes
tools, creates child brains, or fans a request out to every specialist.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SpecialistRoute:
    role_id: str
    reason: str
    context: dict[str, str]


class MotherBrainSpecialistRouter:
    """Select at most one eligible in-process specialist for a text request."""

    _MATH = re.compile(
        r"(?:\b(?:calculate|math|arithmetic|plus|minus|multiply|divide|"
        r"kitna|kitne|kitni|jodo|jod|guna|bhag)\b|[+*=])",
        re.IGNORECASE,
    )
    _LEARN = re.compile(
        r"\b(?:learn|teach me|study|sikhao|sikhaiye|seekhna|sikhna)\b|"
        r"(?:मुझे|मुझको).{0,30}(?:सीखना|सिखना|सिखाओ)",
        re.IGNORECASE,
    )
    _LANGUAGE = re.compile(
        r"\b(?:detect language|identify language|which language|language detection)\b|"
        r"(?:भाषा पहचानो|भाषा बताओ|कौन सी भाषा|किस भाषा)",
        re.IGNORECASE,
    )

    _DEBUGGING_REQUEST = re.compile(
        r"(?:\b(?:debug|fix|repair|troubleshoot|diagnose)\b.{0,80}"
        r"\b(?:bug|error|exception|traceback|crash|failure|failing test)\b|"
        r"\b(?:bug|error|exception|traceback|crash|failure|failing test)\b.{0,80}"
        r"\b(?:debug|fix|repair|troubleshoot|diagnose)\b|"
        r"\b(?:fix|debug|repair|troubleshoot)\s+(?:it|this|that)\b|"
        r"\b(?:bug|error|exception|crash)\s+ko\s+(?:thik|theek|fix)\b|"
        r"(?:बग|एरर|त्रुटि|क्रैश|टेस्ट फेल).{0,35}(?:ठीक|फिक्स|डिबग|जाँच)|"
        r"(?:ठीक|फिक्स|डिबग|जाँच).{0,35}(?:बग|एरर|त्रुटि|क्रैश|टेस्ट))",
        re.IGNORECASE,
    )

    def select(self, request: str, intent: str) -> SpecialistRoute | None:
        if not isinstance(request, str) or not request.strip():
            return None
        if not isinstance(intent, str):
            return None
        text = request.strip()
        normalized_intent = intent.strip().lower()

        # Debugging is triage-only until a separate approved repair workflow exists.
        # Missing reproduction evidence stays missing; the router never invents it.
        if normalized_intent == "code" and self._DEBUGGING_REQUEST.search(text):
            return SpecialistRoute(
                "debugging", "explicit bug/error diagnosis or repair request",
                {"failures": [{
                    "issue_id": "current-request",
                    "symptom": text[:2000],
                    "reproduction_steps": [],
                    "expected": None,
                    "observed": None,
                    "error_excerpt": "",
                }]},
            )

        # Arithmetic is routed only for a bounded-looking arithmetic question.
        if self._MATH.search(text) and re.search(r"\d", text):
            return SpecialistRoute(
                "math", "bounded arithmetic expression detected",
                {"expression": text[:300]},
            )
        if normalized_intent == "learn" or self._LEARN.search(text):
            return SpecialistRoute(
                "teaching", "explicit learning/teaching request",
                {"topic": text[:240], "language": "auto", "level": "beginner"},
            )
        if self._LANGUAGE.search(text):
            return SpecialistRoute(
                "language", "explicit language-identification request",
                {"text": text[:10000]},
            )
        return None
