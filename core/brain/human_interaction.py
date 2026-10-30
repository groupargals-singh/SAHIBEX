from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from core.brain.context import ConversationTurn, ContextManager
from core.brain.intent import IntentEngine, IntentResult
from core.brain.multimodal import InputModality, MultimodalInput
from core.brain.voice import VoiceInput
from core.brain.voice_output import VoiceOutput
from core.brain.vision import VisionInput
from core.brain.universal_language_brain import UniversalLanguageBrain


class InteractionLanguage(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    HINGLISH = "hi-Latn"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class InteractionAssessment:
    interaction_id: str = field(default_factory=lambda: str(uuid4()))
    language: InteractionLanguage = InteractionLanguage.UNKNOWN
    normalized_text: str = ""
    intent: IntentResult | None = None
    clarification_required: bool = False
    clarification_question: str | None = None
    correction_detected: bool = False
    correction_text: str | None = None
    context_summary: dict = field(default_factory=dict)
    language_code: str = "und"
    language_name: str = "Undetermined"

    def __post_init__(self) -> None:
        if not isinstance(self.interaction_id, str) or not self.interaction_id.strip():
            raise ValueError("interaction_id must be non-empty.")
        if not isinstance(self.normalized_text, str):
            raise TypeError("normalized_text must be a string.")
        if not isinstance(self.language, InteractionLanguage):
            raise TypeError("language must be InteractionLanguage.")
        if self.clarification_required and not (
            isinstance(self.clarification_question, str)
            and self.clarification_question.strip()
        ):
            raise ValueError(
                "clarification_question is required when clarification is required."
            )
        if self.correction_detected and not (
            isinstance(self.correction_text, str)
            and self.correction_text.strip()
        ):
            raise ValueError(
                "correction_text is required when a correction is detected."
            )


class HumanInteractionEngine:
    """
    SAHIBEX human-interaction boundary.

    It owns interaction normalization and context decisions while leaving
    authority, permissions, execution, and protected actions to the existing
    Main Brain security/execution layers.
    """

    _HINGLISH_MARKERS = {
        "kya", "hai", "h", "mujhe", "mujhko", "mera", "meri", "mere",
        "kar", "karo", "karen", "chahiye", "batao", "bata", "dekho",
        "isko", "use", "kaise", "kyu", "kyon", "haan", "nahi", "nahin",
        "acha", "achha", "theek", "thik", "ab", "pahle", "pehle",
    }

    _CORRECTION_MARKERS = (
        "nahi, mera matlab",
        "nahin, mera matlab",
        "mera matlab",
        "i mean",
        "no, i mean",
        "actually i mean",
        "galat samjhe",
        "galat samjha",
        "not that",
        "instead",
    )

    _AMBIGUOUS_MARKERS = (
        "ye karo",
        "yah karo",
        "isko karo",
        "use karo",
        "do it",
        "do that",
        "make it",
        "fix it",
        "change it",
        "banao",
        "kar do",
    )

    def __init__(
        self,
        *,
        context: ContextManager | None = None,
        intent_engine: IntentEngine | None = None,
    ) -> None:
        self.context = context or ContextManager()
        self.intent_engine = intent_engine or IntentEngine()
        self.language_brain = UniversalLanguageBrain()

    def detect_language(self, text: str) -> InteractionLanguage:
        if not isinstance(text, str):
            raise TypeError("text must be a string.")
        assessment = self.language_brain.detect(text)
        if assessment.language_code == "hi":
            return InteractionLanguage.HINDI
        if assessment.language_code == "hi-Latn":
            return InteractionLanguage.HINGLISH
        if assessment.language_code == "en":
            return InteractionLanguage.ENGLISH
        return InteractionLanguage.UNKNOWN

    def assess_language(self, text: str):
        """Return the full Universal Language Brain assessment."""
        return self.language_brain.detect(text)

    def normalize_text(self, text: str) -> str:
        if not isinstance(text, str):
            raise TypeError("text must be a string.")
        normalized = " ".join(text.strip().split())
        if not normalized:
            raise ValueError("text must be non-empty.")
        return normalized

    def _detect_correction(self, text: str) -> tuple[bool, str | None]:
        lowered = text.lower().strip()
        for marker in self._CORRECTION_MARKERS:
            index = lowered.find(marker)
            if index >= 0:
                correction = text[index + len(marker):].strip(" :-,")
                if correction:
                    return True, correction
        return False, None

    def _needs_clarification(
        self,
        text: str,
        intent: IntentResult,
    ) -> tuple[bool, str | None]:
        lowered = text.lower()
        if intent.intent == "empty":
            return True, "Aap kya karwana chahte hain?"
        if intent.intent == "general_request" and len(text.split()) <= 2:
            return True, "Thoda aur detail bataiye, aap mujhse kya karwana chahte hain?"
        if any(marker in lowered for marker in self._AMBIGUOUS_MARKERS):
            recent = self.context.recent(1)
            if not recent:
                return True, "Aap kis cheez ke baare mein keh rahe hain? Thoda context bataiye."
        if intent.confidence < 0.50:
            return True, "Main request ko lekar sure nahi hoon. Kripya thoda aur clear karein."
        return False, None

    def assess(self, text: str) -> InteractionAssessment:
        normalized = self.normalize_text(text)
        language = self.detect_language(normalized)
        intent = self.intent_engine.detect(normalized)
        if intent.intent == "general_request":
            lowered = normalized.lower()
            if any(
                marker in lowered.split()
                for marker in ("batao", "samjhao", "samjhaao", "samjha", "kyu", "kyon")
            ):
                intent = IntentResult(
                    intent="explain",
                    confidence=0.75,
                    entities={},
                )
            elif any(
                marker in lowered.split()
                for marker in ("karo", "kar", "banao", "banado")
            ):
                intent = IntentResult(
                    intent="create",
                    confidence=0.70,
                    entities={},
                )
        correction_detected, correction_text = self._detect_correction(normalized)
        clarification_required, question = self._needs_clarification(
            normalized, intent
        )

        return InteractionAssessment(
            language=language,
            normalized_text=normalized,
            intent=intent,
            clarification_required=clarification_required,
            clarification_question=question,
            correction_detected=correction_detected,
            correction_text=correction_text,
            context_summary=self.context.summary(),
            language_code=self.language_brain.detect(normalized).language_code,
            language_name=self.language_brain.detect(normalized).language_name,
        )

    def record_turn(
        self,
        *,
        user: str,
        assistant: str,
        intent: str,
    ) -> None:
        self.context.add_turn(user, assistant, intent)

    def prepare_voice_input(self, voice: VoiceInput) -> str:
        if not isinstance(voice, VoiceInput):
            raise TypeError("voice must be VoiceInput.")
        return self.normalize_text(voice.content)

    def prepare_voice_output(self, output: VoiceOutput) -> VoiceOutput:
        if not isinstance(output, VoiceOutput):
            raise TypeError("output must be VoiceOutput.")
        return output

    def prepare_vision_input(self, vision: VisionInput) -> MultimodalInput:
        if not isinstance(vision, VisionInput):
            raise TypeError("vision must be VisionInput.")
        return MultimodalInput(
            content=vision.content,
            modality=InputModality.IMAGE,
        )

    def prepare_multimodal(self, inputs: list[MultimodalInput]) -> list[MultimodalInput]:
        if not isinstance(inputs, list):
            raise TypeError("inputs must be a list.")
        for item in inputs:
            if not isinstance(item, MultimodalInput):
                raise TypeError("every input must be MultimodalInput.")
        return list(inputs)
