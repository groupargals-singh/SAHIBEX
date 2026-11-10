"""Confidence and verification decision layer for the SAHIBEX Master Brain.

Separates request-understanding confidence from factual truth. It can ask for
clarification when deterministic ambiguity is detected, but never grants
permissions, executes actions, or upgrades generated text to verified facts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from core.brain.input_confidence import InputConfidenceEngine
from core.brain.uncertainty import UncertaintyEngine


@dataclass(frozen=True)
class ConfidenceVerificationDecision:
    input_confidence: float
    intent_confidence: float
    uncertainty: float
    uncertainty_level: str
    decision: str
    clarification_required: bool
    clarification_question: str
    reasons: tuple[str, ...] = ()
    factual_claim_status: str = "NOT_FACTUALLY_VERIFIED"
    assessment_id: str = field(default="")

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_confidence": self.input_confidence,
            "intent_confidence": self.intent_confidence,
            "uncertainty": self.uncertainty,
            "uncertainty_level": self.uncertainty_level,
            "decision": self.decision,
            "clarification_required": self.clarification_required,
            "clarification_question": self.clarification_question,
            "reasons": list(self.reasons),
            "factual_claim_status": self.factual_claim_status,
            "assessment_id": self.assessment_id,
            "truth_score": False,
            "grants_permission": False,
            "executes_actions": False,
        }


class ConfidenceVerificationBrain:
    """Conservative confidence, ambiguity and factual-status coordinator."""

    VERSION = "1.0"
    _AMBIGUOUS_TERMS = {
        "bat": {
            "question_en": "By 'bat', do you mean a cricket bat or the animal?",
            "question_hi": "आप 'bat' से हिंदी 'बात' (विषय/चर्चा), क्रिकेट का बल्ला, या चमगादड़ कहना चाहते हैं?",
            "cues": ("cricket", "ball", "batsman", "batter", "baat", "talk", "conversation", "discuss", "बात", "चर्चा", "बल्ला", "क्रिकेट", "चमगादड़", "animal", "mammal"),
        },
        "bank": {
            "question_en": "Do you mean a financial bank or the bank of a river?",
            "question_hi": "आप बैंक (वित्तीय संस्था) की बात कर रहे हैं या नदी के किनारे की?",
            "cues": ("account", "money", "loan", "finance", "atm", "नदी", "किनारा", "river", "shore"),
        },
        "light": {
            "question_en": "Do you mean light as illumination or light as low weight?",
            "question_hi": "आप 'light' से रोशनी कहना चाहते हैं या हल्का वजन?",
            "cues": ("bulb", "lamp", "brightness", "roshni", "रोशनी", "weight", "luggage", "switch", "turn on", "turn off", "हल्का", "वजन"),
        },
        "right": {
            "question_en": "Do you mean 'right' as correct, a direction, or a legal right?",
            "question_hi": "आप 'right' से सही, दायाँ दिशा, या अधिकार का अर्थ ले रहे हैं?",
            "cues": ("correct", "answer", "sahi", "सही", "left", "turn", "side", "दायाँ", "direction", "अधिकार", "legal"),
        },
        "charge": {
            "question_en": "Do you mean a fee, an electrical charge, or an accusation?",
            "question_hi": "आप 'charge' से शुल्क, बिजली का आवेश, या आरोप का अर्थ ले रहे हैं?",
            "cues": ("fee", "payment", "battery", "phone", "electric", "current", "शुल्क", "बैटरी", "बिजली", "आरोप", "accuse"),
        },
        "python": {
            "question_en": "Do you mean the Python programming language or the snake?",
            "question_hi": "आप Python programming language की बात कर रहे हैं या साँप की?",
            "cues": ("code", "program", "script", "programming", "language", "भाषा", "snake", "साँप", "कोड", "प्रोग्राम"),
        },
    }
    _REFERENCE_PATTERNS = (
        r"\b(?:this|that|it|these|those)\b",
        r"\b(?:ye|yeh|woh|ise|isko|usko|isko|us)\b",
        r"(?:यह|ये|वह|वो|इसे|इसको|उसको|उसे)",
    )
    _ACTION_REFERENCE_PATTERNS = (
        r"\b(?:delete|remove|open|edit|change|send|move|fix|do)\s+(?:it|this|that|these|those)\b",
        r"\b(?:isko|ise|usko|use)\s+(?:delete|remove|open|edit|change|fix|repair|thik|theek|sahi|bhejo|hatao|karo)\b",
        r"(?:इसे|इसको|उसको|उसे)\s*(?:हटाओ|मिटाओ|खोलो|बदलो|भेजो|ठीक करो|ठीक कर दो|फिक्स करो|सही करो|करो)",
    )
    _CONTEXT_REFERENT_PATTERNS = (
        r"\b(?:file|folder|document|photo|image|picture|code|program|script|model|brain|project|topic|question|idea|plan|task|error|bug|message|answer|feature|system|weather|bank|python|river|account|loan|payment|charge|light|word|meaning|report|database|record)\b",
        r"(?:फ़ाइल|फाइल|फ़ोल्डर|फोल्डर|फोटो|तस्वीर|दस्तावेज़|कोड|प्रोग्राम|मॉडल|ब्रेन|प्रोजेक्ट|विषय|सवाल|योजना|काम|त्रुटि|संदेश|जवाब|सुविधा|सिस्टम|मौसम|बैंक|नदी|खाता|भुगतान|शब्द|अर्थ|रिपोर्ट)",
    )
    _ACTION_TARGET_PATTERNS = (
        r"\b(?:file|folder|document|photo|image|picture|record|database|account|row|item|report|code|script|task|error|bug|message)\b",
        r"(?:फ़ाइल|फाइल|फ़ोल्डर|फोल्डर|फोटो|तस्वीर|दस्तावेज़|रिकॉर्ड|खाता|रिपोर्ट|कोड|काम|त्रुटि|संदेश)",
    )
    _UNRESOLVED_TOPIC_PATTERNS = (
        r"\b(?:this|that)\s+(?:topic|subject|matter)\b",
        r"\b(?:is|iss|us|uss)\s+(?:topic|subject)\b",
        r"\b(?:is|iss|us|uss)\s+par\b",
        r"\b(?:is|iss|us|uss)\s+ke\s+baare\s+mein\b",
    )

    @classmethod
    def _has_context_referent(cls, context: str) -> bool:
        return any(
            re.search(pattern, context, flags=re.IGNORECASE)
            for pattern in cls._CONTEXT_REFERENT_PATTERNS
        )

    @classmethod
    def _has_action_target_context(cls, context: str) -> bool:
        return any(
            re.search(pattern, context, flags=re.IGNORECASE)
            for pattern in cls._ACTION_TARGET_PATTERNS
        )

    def __init__(self) -> None:
        self.input_confidence_engine = InputConfidenceEngine()
        self.uncertainty_engine = UncertaintyEngine()

    @classmethod
    def detect_ambiguity(
        cls,
        text: str,
        *,
        context_text: str = "",
        language_code: str = "und",
    ) -> tuple[bool, str, tuple[str, ...]]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if not isinstance(context_text, str):
            raise TypeError("context_text must be a string")
        lowered = " ".join(text.casefold().split())
        context = " ".join(context_text.casefold().split())
        combined = lowered + " " + context
        is_hindi = language_code.startswith("hi") or bool(re.search(r"[\u0900-\u097F]", text))

        for term, item in cls._AMBIGUOUS_TERMS.items():
            if re.search(rf"\b{re.escape(term)}\b", lowered):
                if not any(cue in combined for cue in item["cues"]):
                    question = item["question_hi" if is_hindi else "question_en"]
                    return True, question, (f"ambiguous_word:{term}",)

        unresolved_topic_reference = any(
            re.search(pattern, lowered, flags=re.IGNORECASE)
            for pattern in cls._UNRESOLVED_TOPIC_PATTERNS
        )
        if unresolved_topic_reference and not cls._has_context_referent(context):
            question = (
                "आप किस विषय पर जानकारी चाहते हैं?"
                if is_hindi else
                "Which topic or subject should I use?"
            )
            return True, question, ("unresolved_topic_reference",)

        has_action_reference = any(
            re.search(pattern, lowered, flags=re.IGNORECASE)
            for pattern in cls._ACTION_REFERENCE_PATTERNS
        )
        has_unresolved_reference = any(
            re.search(pattern, lowered, flags=re.IGNORECASE)
            for pattern in cls._REFERENCE_PATTERNS
        )
        if has_action_reference and not cls._has_action_target_context(context):
            question = (
                "आप किस फ़ाइल या वस्तु की बात कर रहे हैं?"
                if is_hindi else
                "Which file or item are you referring to?"
            )
            return True, question, ("unresolved_action_reference",)

        short_demonstrative = (
            len(re.findall(r"\w+", lowered, flags=re.UNICODE)) <= 5
            and has_unresolved_reference
        )
        if short_demonstrative and not cls._has_context_referent(context):
            question = (
                "आप किस चीज़ या विषय की बात कर रहे हैं?"
                if is_hindi else
                "What item or topic are you referring to?"
            )
            return True, question, ("unresolved_demonstrative_reference",)

        return False, "", ()

    def assess(
        self,
        *,
        input_id: str,
        text: str,
        intent_confidence: float,
        language_confidence: float,
        input_confidence: float = 1.0,
        semantic_confidence: float | None = None,
        semantic_needs_clarification: bool = False,
        semantic_question: str = "",
        ambiguity_question: str = "",
        ambiguity_reasons: tuple[str, ...] = (),
        conflict_score: float = 0.0,
        missing_information: bool = False,
        factual_claim_status: str = "NOT_FACTUALLY_VERIFIED",
    ) -> ConfidenceVerificationDecision:
        if not isinstance(input_id, str) or not input_id.strip():
            raise ValueError("input_id must be non-empty")
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        for name, value in (
            ("intent_confidence", intent_confidence),
            ("language_confidence", language_confidence),
            ("input_confidence", input_confidence),
            ("conflict_score", conflict_score),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if semantic_confidence is not None and (
            isinstance(semantic_confidence, bool)
            or not isinstance(semantic_confidence, (int, float))
            or not 0 <= float(semantic_confidence) <= 1
        ):
            raise ValueError("semantic_confidence must be between 0 and 1")
        if not isinstance(semantic_needs_clarification, bool):
            raise TypeError("semantic_needs_clarification must be bool")
        if not isinstance(semantic_question, str) or not isinstance(ambiguity_question, str):
            raise TypeError("clarification questions must be strings")
        if not isinstance(ambiguity_reasons, tuple):
            raise TypeError("ambiguity_reasons must be a tuple")
        if not isinstance(factual_claim_status, str) or not factual_claim_status.strip():
            raise ValueError("factual_claim_status must be non-empty")

        capture = self.input_confidence_engine.assess(
            input_id=input_id,
            confidence=float(input_confidence),
        )
        selected_confidence = (
            float(semantic_confidence)
            if semantic_confidence is not None
            else float(intent_confidence)
        )
        ambiguous = bool(ambiguity_question or semantic_needs_clarification)
        uncertainty = self.uncertainty_engine.assess(
            input_id=input_id,
            confidence=selected_confidence,
            quality_score=float(language_confidence),
            conflict_score=float(conflict_score),
            missing_information=missing_information,
            ambiguous=ambiguous,
            reasons=tuple(ambiguity_reasons),
        )

        clarification_required = ambiguous or (
            semantic_confidence is not None and semantic_confidence < 0.72
        )
        if clarification_required:
            decision = "CLARIFICATION_REQUIRED"
            question = (
                semantic_question.strip()
                if semantic_needs_clarification and semantic_question.strip()
                else ambiguity_question.strip()
                or "Could you clarify what you mean?"
            )
        elif selected_confidence < 0.50:
            decision = "PROCEED_WITH_LOW_CONFIDENCE"
            question = ""
        else:
            decision = "PROCEED"
            question = ""

        return ConfidenceVerificationDecision(
            input_confidence=float(capture.confidence),
            intent_confidence=selected_confidence,
            uncertainty=float(uncertainty.uncertainty),
            uncertainty_level=uncertainty.level.value,
            decision=decision,
            clarification_required=clarification_required,
            clarification_question=question,
            reasons=tuple(dict.fromkeys((*uncertainty.reasons, *ambiguity_reasons))),
            factual_claim_status=factual_claim_status.strip(),
            assessment_id=uncertainty.assessment_id,
        )

    @staticmethod
    def factual_status_for_response(verification_status: str, metadata: dict[str, Any] | None = None) -> str:
        """Describe factual evidence separately from routing/permission verification."""
        metadata = metadata if isinstance(metadata, dict) else {}
        explicit = metadata.get("factual_verification")
        if explicit is None:
            operational = metadata.get("mother_operational_integration", {})
            if isinstance(operational, dict):
                explicit = operational.get("factual_verification")
        if explicit is True:
            return "EVIDENCE_VERIFIED"
        if explicit is False:
            return "NOT_FACTUALLY_VERIFIED"
        if isinstance(explicit, str) and explicit.strip():
            return explicit.strip().upper()
        status = str(verification_status or "").strip().upper()
        if status == "CURATED_KNOWLEDGE":
            return "CURATED_KNOWLEDGE_NOT_INDEPENDENTLY_VERIFIED"
        if status == "DETERMINISTIC_ARITHMETIC":
            return "DETERMINISTIC_COMPUTATION"
        if status == "DETERMINISTIC_TEXT_TASK":
            return "DETERMINISTIC_RULE_BASED"
        if status in {"RESEARCH_VERIFIED", "EVIDENCE_VERIFIED", "VERIFIED_WITH_EVIDENCE"}:
            return "EVIDENCE_VERIFIED"
        if status in {"GENERATED", "STRUCTURALLY_VALID", "VERIFIED", "SUCCESS"}:
            return "NOT_FACTUALLY_VERIFIED"
        return "NOT_FACTUALLY_VERIFIED"

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def upgrades_guess_to_fact() -> bool:
        return False
