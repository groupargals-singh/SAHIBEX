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

    _CONVERSATION_CONTEXT_REQUEST = re.compile(
        r"\b(?:what were we discussing|what were we working on|what was our last "
        r"task|what did i ask you to do last|continue (?:the )?(?:previous|last) "
        r"task|resume (?:the )?(?:previous|last) task|pick up where we left off|"
        r"recap our (?:last|previous) conversation)\b|"
        r"(?:hum\s+(?:kya|kis)\s+par\s+baat\s+kar\s+rahe\s+the|"
        r"pichhla\s+task\s+(?:kya|kaun sa)\s+tha|"
        r"pichhla\s+kaam\s+(?:continue|jaari)\s+karo|"
        r"jahan\s+chhoda\s+tha\s+wahan\s+se\s+shuru\s+karo)|"
        r"(?:हम\s+क्या\s+बात\s+कर\s+रहे\s+थे|हम\s+किस\s+विषय\s+पर\s+बात\s+कर\s+रहे\s+थे|"
        r"पिछला\s+काम\s+(?:क्या|कौन सा)\s+था|"
        r"पिछला\s+काम\s+(?:जारी|आगे)\s+करो|"
        r"जहाँ\s+छोड़ा\s+था\s+वहीं\s+से\s+शुरू\s+करो)",
        re.IGNORECASE,
    )

    _KNOWLEDGE_REQUEST = re.compile(
        r"\b(?:what verified knowledge do you have about|what do you know from "
        r"verified knowledge about|search (?:the )?knowledge base for|find "
        r"verified knowledge about|search verified knowledge for|retrieve "
        r"verified knowledge about)\s+(.+)$|"
        r"(?:verified knowledge (?:ke )?(?:me|mein)\s+(.+?)\s+(?:search|khojo|dhundo)|"
        r"(.+?)\s+ke ba(?:a)?re me(?:in)? verified knowledge (?:batao|dikhao|khojo))|"
        r"(?:सत्यापित ज्ञान में\s*(.+?)\s*(?:खोजो|ढूँढो|ढूंढो)|"
        r"(.+?)\s+के बारे में सत्यापित जानकारी\s*(?:बताओ|दिखाओ|खोजो))",
        re.IGNORECASE | re.DOTALL,
    )

    _MEMORY_REQUEST = re.compile(
        r"\b(?:what do you remember about|do you remember|recall|"
        r"find in memory|search memory for|remember our discussion about)\s+(.+)$",
        re.IGNORECASE | re.DOTALL,
    )
    _MEMORY_REQUEST_HINGLISH = re.compile(
        r"\b(?:tumhe|tumko)\s+(?:kya\s+)?yaad\s+hai\s+(.+)$|"
        r"\b(?:tumhe|tumko)\s+(.+?)\s+ke\s+bare\s+me\s+kya\s+yaad\s+hai\b",
        re.IGNORECASE | re.DOTALL,
    )

    _DOCUMENT_REQUEST = re.compile(
        r"\b(?:summari[sz]e|summarise|extract key points from|review)\s+"
        r"(?:this\s+)?(?:document|doc)\b|"
        r"(?:इस दस्तावेज़ का सार|दस्तावेज़ का सार|इस डॉक्यूमेंट का सार)|"
        r"\b(?:is|iss)\s+document\s+ka\s+(?:summary|saransh)\b",
        re.IGNORECASE,
    )
    _READING_REQUEST = re.compile(
        r"\b(?:read|extract|analy[sz]e|analyse)\s+(?:this\s+)?"
        r"(?:text|passage|content)\b|"
        r"(?:इस टेक्स्ट को पढ़|इस पाठ को पढ़|दिए गए पाठ को पढ़)|"
        r"\b(?:is|iss)\s+text\s+ko\s+(?:padho|read karo|analyse karo)\b",
        re.IGNORECASE,
    )
    _DOCUMENT_PAYLOAD = re.compile(
        r"^\s*(?:(?:please|kindly|can you|could you|would you)\s+)?"
        r"(?:summari[sz]e|summarise|extract key points from|review)\s+"
        r"(?:this\s+)?(?:document|doc)\s*[:\n]\s*(.+)$|"
        r"^\s*(?:is|iss)\s+document\s+ka\s+(?:summary|saransh)\s*[:\n]\s*(.+)$|"
        r"^\s*(?:इस दस्तावेज़ का सार|दस्तावेज़ का सार|इस डॉक्यूमेंट का सार)\s*[:\n]\s*(.+)$",
        re.IGNORECASE | re.DOTALL,
    )
    _READING_PAYLOAD = re.compile(
        r"^\s*(?:(?:please|kindly|can you|could you|would you)\s+)?"
        r"(?:read|extract|analy[sz]e|analyse)\s+"
        r"(?:this\s+)?(?:text|passage|content)\s*[:\n]\s*(.+)$|"
        r"^\s*(?:is|iss)\s+text\s+ko\s+(?:padho|read karo|analyse karo)\s*[:\n]\s*(.+)$|"
        r"^\s*(?:इस टेक्स्ट को पढ़|इस पाठ को पढ़|दिए गए पाठ को पढ़)\s*[:\n]\s*(.+)$",
        re.IGNORECASE | re.DOTALL,
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

        if self._CONVERSATION_CONTEXT_REQUEST.search(text):
            return SpecialistRoute(
                "conversation", "explicit request to recall or continue bounded conversation context",
                {"max_turns": 8},
            )

        knowledge_match = self._KNOWLEDGE_REQUEST.search(text)
        if knowledge_match:
            knowledge_query = next(
                (group for group in knowledge_match.groups() if group), ""
            ).strip().strip(" ?.!\n\t")
            if knowledge_query:
                return SpecialistRoute(
                    "knowledge", "explicit request to search verified stored knowledge",
                    {"query": knowledge_query[:1000], "verified_only": True, "min_confidence": 0.0},
                )

        memory_match = self._MEMORY_REQUEST.search(text) or self._MEMORY_REQUEST_HINGLISH.search(text)
        if memory_match:
            memory_query = next((group for group in memory_match.groups() if group), "").strip().strip(" ?.!\n\t")
            if memory_query:
                return SpecialistRoute(
                    "memory", "explicit request to recall stored memory",
                    {"query": memory_query[:1000]},
                )

        # These handlers process only text included in the request. They do not
        # resolve file paths or access the filesystem.
        document_match = self._DOCUMENT_PAYLOAD.match(text)
        if self._DOCUMENT_REQUEST.search(text):
            payload = next((group for group in document_match.groups() if group), "").strip() if document_match else ""
            return SpecialistRoute(
                "document_file", "explicit document summary/review request",
                {"document_text": payload[:12000], "max_chars": 12000, "max_points": 8},
            )

        reading_match = self._READING_PAYLOAD.match(text)
        if self._READING_REQUEST.search(text):
            payload = next((group for group in reading_match.groups() if group), "").strip() if reading_match else ""
            return SpecialistRoute(
                "reading", "explicit supplied-text reading/extraction request",
                {"source_text": payload[:12000], "max_chars": 12000},
            )

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
