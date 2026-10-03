from __future__ import annotations

from core.brain.multimodal import (
    InputModality,
    MultimodalInput,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    check(
        InputModality.TEXT.value == "text",
        "TEXT modality must exist.",
    )

    check(
        InputModality.VOICE.value == "voice",
        "VOICE modality must exist.",
    )

    check(
        InputModality.IMAGE.value == "image",
        "IMAGE modality must exist.",
    )

    text_input = MultimodalInput(
        modality=InputModality.TEXT,
        content="Hello SAHIBEX",
    )

    check(
        text_input.modality == InputModality.TEXT,
        "Input modality must be preserved.",
    )

    check(
        text_input.content == "Hello SAHIBEX",
        "Input content must be preserved.",
    )

    check(
        isinstance(text_input.input_id, str)
        and bool(text_input.input_id.strip()),
        "Input must have a unique identity.",
    )

    second_input = MultimodalInput(
        modality=InputModality.VOICE,
        content="Test voice input",
    )

    check(
        text_input.input_id != second_input.input_id,
        "Each multimodal input must have a unique ID.",
    )

    invalid_modality_rejected = False

    try:
        MultimodalInput(
            modality="voice",
            content="invalid",
        )
    except (TypeError, ValueError):
        invalid_modality_rejected = True

    check(
        invalid_modality_rejected,
        "Invalid modality must be rejected.",
    )

    empty_content_rejected = False

    try:
        MultimodalInput(
            modality=InputModality.TEXT,
            content="",
        )
    except ValueError:
        empty_content_rejected = True

    check(
        empty_content_rejected,
        "Empty content must be rejected.",
    )

    fields = set(MultimodalInput.__dataclass_fields__)

    check(
        "permission" not in fields,
        "Multimodal input must not contain permission fields.",
    )

    check(
        "authorization" not in fields,
        "Multimodal input must not contain authorization fields.",
    )

    check(
        "api_key" not in fields,
        "Multimodal input must not contain credential fields.",
    )

    print("SAHIBEX 6M-1 MULTIMODAL INPUT CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
