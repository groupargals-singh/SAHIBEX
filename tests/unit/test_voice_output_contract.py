from __future__ import annotations

from core.brain.voice_output import VoiceOutput, VoiceOutputFormat


def main() -> None:
    assert VoiceOutputFormat.TEXT.value == "text"
    assert VoiceOutputFormat.AUDIO.value == "audio"

    text_output = VoiceOutput(
        content="Hello from SAHIBEX.",
        output_format=VoiceOutputFormat.TEXT,
        language="en",
    )

    audio_output = VoiceOutput(
        content="Hello from SAHIBEX.",
        output_format=VoiceOutputFormat.AUDIO,
        language="en",
    )

    assert text_output.content == "Hello from SAHIBEX."
    assert text_output.output_format is VoiceOutputFormat.TEXT
    assert text_output.language == "en"

    assert audio_output.content == "Hello from SAHIBEX."
    assert audio_output.output_format is VoiceOutputFormat.AUDIO
    assert audio_output.language == "en"

    assert text_output.output_id != audio_output.output_id

    try:
        VoiceOutput(
            content="Hello",
            output_format="invalid",
            language="en",
        )
    except TypeError:
        pass
    else:
        raise AssertionError("Invalid output_format must be rejected.")

    try:
        VoiceOutput(
            content="",
            output_format=VoiceOutputFormat.TEXT,
            language="en",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Empty content must be rejected.")

    try:
        VoiceOutput(
            content="Hello",
            output_format=VoiceOutputFormat.TEXT,
            language="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Empty language must be rejected.")

    fields = VoiceOutput.__dataclass_fields__

    forbidden_fields = {
        "permission",
        "authorization",
        "api_key",
        "credential",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    print("SAHIBEX 6M-3 VOICE OUTPUT CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
