from __future__ import annotations

from core.brain.multimodal_context import (
    MultimodalContext,
)


def main() -> None:
    context = MultimodalContext()

    assert context.context_id
    assert context.inputs == []

    context.add_input("text-1")
    context.add_input("voice-1")
    context.add_input("image-1")

    assert context.inputs == [
        "text-1",
        "voice-1",
        "image-1",
    ]

    assert context.input_count == 3

    removed = context.remove_input("voice-1")

    assert removed is True
    assert context.inputs == [
        "text-1",
        "image-1",
    ]

    assert context.input_count == 2

    assert context.remove_input("missing") is False

    try:
        context.add_input("")
    except ValueError:
        pass
    else:
        raise AssertionError("Empty input ID must be rejected.")

    try:
        context.add_input(123)
    except TypeError:
        pass
    else:
        raise AssertionError("Non-string input ID must be rejected.")

    fields = MultimodalContext.__dataclass_fields__

    forbidden_fields = {
        "permission",
        "authorization",
        "api_key",
        "credential",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    print("SAHIBEX 6M-5 MULTIMODAL CONTEXT CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
