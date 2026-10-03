from __future__ import annotations

from core.brain.vision import VisionInput, VisionInputFormat


def main() -> None:
    assert VisionInputFormat.IMAGE.value == "image"
    assert VisionInputFormat.FRAME.value == "frame"

    image_input = VisionInput(
        content="image-data",
        input_format=VisionInputFormat.IMAGE,
        source="camera",
    )

    frame_input = VisionInput(
        content="frame-data",
        input_format=VisionInputFormat.FRAME,
        source="camera",
    )

    assert image_input.content == "image-data"
    assert image_input.input_format is VisionInputFormat.IMAGE
    assert image_input.source == "camera"

    assert frame_input.content == "frame-data"
    assert frame_input.input_format is VisionInputFormat.FRAME
    assert frame_input.source == "camera"

    assert image_input.input_id != frame_input.input_id

    try:
        VisionInput(
            content="image-data",
            input_format="invalid",
            source="camera",
        )
    except TypeError:
        pass
    else:
        raise AssertionError("Invalid input_format must be rejected.")

    try:
        VisionInput(
            content="",
            input_format=VisionInputFormat.IMAGE,
            source="camera",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Empty content must be rejected.")

    try:
        VisionInput(
            content="image-data",
            input_format=VisionInputFormat.IMAGE,
            source="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Empty source must be rejected.")

    fields = VisionInput.__dataclass_fields__

    forbidden_fields = {
        "permission",
        "authorization",
        "api_key",
        "credential",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    print("SAHIBEX 6M-4 VISION INPUT CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
