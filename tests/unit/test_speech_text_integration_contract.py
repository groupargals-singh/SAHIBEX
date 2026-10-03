from __future__ import annotations

from core.brain.speech_text import (
    SpeechTextIntegration,
    SpeechTextResult,
)


def main() -> None:
    integration = SpeechTextIntegration()

    result = integration.transcribe(
        voice_input_id="voice-123",
        text="Hello SAHIBEX",
        language="en",
    )

    assert isinstance(result, SpeechTextResult)
    assert result.voice_input_id == "voice-123"
    assert result.text == "Hello SAHIBEX"
    assert result.language == "en"
    assert result.result_id

    output = integration.prepare_speech(
        text="Hello from SAHIBEX",
        language="en",
    )

    assert isinstance(output, SpeechTextResult)
    assert output.voice_input_id is None
    assert output.text == "Hello from SAHIBEX"
    assert output.language == "en"
    assert output.result_id

    assert result.result_id != output.result_id

    try:
        integration.transcribe(
            voice_input_id="",
            text="Hello",
            language="en",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty voice_input_id must be rejected."
        )

    try:
        integration.transcribe(
            voice_input_id="voice-123",
            text="",
            language="en",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty transcription text must be rejected."
        )

    try:
        integration.prepare_speech(
            text="Hello",
            language="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty language must be rejected."
        )

    fields = SpeechTextResult.__dataclass_fields__

    forbidden_fields = {
        "permission",
        "authorization",
        "api_key",
        "credential",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    print(
        "SAHIBEX 6M-6 SPEECH TEXT INTEGRATION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
