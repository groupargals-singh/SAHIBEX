from __future__ import annotations

from core.brain.voice import (
    VoiceInput,
    VoiceInputFormat,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    check(
        VoiceInputFormat.TEXT.value == "text",
        "TEXT format must exist.",
    )

    check(
        VoiceInputFormat.AUDIO.value == "audio",
        "AUDIO format must exist.",
    )

    voice = VoiceInput(
        content="Hello SAHIBEX",
        input_format=VoiceInputFormat.TEXT,
        language="en",
    )

    check(
        voice.content == "Hello SAHIBEX",
        "Voice input content must be preserved.",
    )

    check(
        voice.input_format == VoiceInputFormat.TEXT,
        "Voice input format must be preserved.",
    )

    check(
        voice.language == "en",
        "Voice language must be preserved.",
    )

    check(
        isinstance(voice.input_id, str)
        and bool(voice.input_id.strip()),
        "Voice input must have a unique ID.",
    )

    second_voice = VoiceInput(
        content="Another input",
        input_format=VoiceInputFormat.AUDIO,
        language="hi",
    )

    check(
        voice.input_id != second_voice.input_id,
        "Each voice input must have a unique ID.",
    )

    invalid_format_rejected = False

    try:
        VoiceInput(
            content="Invalid",
            input_format="audio",
            language="en",
        )
    except (TypeError, ValueError):
        invalid_format_rejected = True

    check(
        invalid_format_rejected,
        "Invalid voice format must be rejected.",
    )

    empty_content_rejected = False

    try:
        VoiceInput(
            content="",
            input_format=VoiceInputFormat.TEXT,
            language="en",
        )
    except ValueError:
        empty_content_rejected = True

    check(
        empty_content_rejected,
        "Empty voice content must be rejected.",
    )

    empty_language_rejected = False

    try:
        VoiceInput(
            content="Hello",
            input_format=VoiceInputFormat.TEXT,
            language="",
        )
    except ValueError:
        empty_language_rejected = True

    check(
        empty_language_rejected,
        "Empty language must be rejected.",
    )

    fields = set(VoiceInput.__dataclass_fields__)

    check(
        "permission" not in fields,
        "Voice input must not contain permission fields.",
    )

    check(
        "authorization" not in fields,
        "Voice input must not contain authorization fields.",
    )

    check(
        "api_key" not in fields,
        "Voice input must not contain credential fields.",
    )

    print("SAHIBEX 6M-2 VOICE INPUT CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
