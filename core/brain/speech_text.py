from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class SpeechTextResult:
    """
    Contract representing a speech-to-text or text-to-speech
    preparation result.

    This layer does not access a microphone, speaker, speech
    recognition engine, text-to-speech engine, or external service.
    """

    voice_input_id: str | None
    text: str
    language: str
    result_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if self.voice_input_id is not None:
            if not isinstance(self.voice_input_id, str):
                raise TypeError(
                    "voice_input_id must be a string or None."
                )

            if not self.voice_input_id.strip():
                raise ValueError(
                    "voice_input_id must be non-empty when provided."
                )

        if not isinstance(self.text, str):
            raise TypeError("text must be a string.")

        if not self.text.strip():
            raise ValueError("text must be a non-empty string.")

        if not isinstance(self.language, str):
            raise TypeError("language must be a string.")

        if not self.language.strip():
            raise ValueError("language must be a non-empty string.")

        if not isinstance(self.result_id, str) or not self.result_id.strip():
            raise ValueError("result_id must be a non-empty string.")


class SpeechTextIntegration:
    """
    Contract-level speech ↔ text integration.

    This class only creates validated representations.
    It does not perform actual speech recognition or synthesis.
    """

    def transcribe(
        self,
        *,
        voice_input_id: str,
        text: str,
        language: str,
    ) -> SpeechTextResult:
        if not isinstance(voice_input_id, str):
            raise TypeError("voice_input_id must be a string.")

        if not voice_input_id.strip():
            raise ValueError(
                "voice_input_id must be a non-empty string."
            )

        return SpeechTextResult(
            voice_input_id=voice_input_id,
            text=text,
            language=language,
        )

    def prepare_speech(
        self,
        *,
        text: str,
        language: str,
    ) -> SpeechTextResult:
        return SpeechTextResult(
            voice_input_id=None,
            text=text,
            language=language,
        )
