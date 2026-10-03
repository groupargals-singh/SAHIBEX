from __future__ import annotations

from core.brain.multimodal_memory import (
    MultimodalMemoryIntegration,
    MultimodalMemoryReference,
)


def main() -> None:
    integration = MultimodalMemoryIntegration()

    text_ref = integration.create_reference(
        input_id="text-123",
        modality="text",
        summary="User asked about SAHIBEX.",
    )

    assert isinstance(text_ref, MultimodalMemoryReference)
    assert text_ref.input_id == "text-123"
    assert text_ref.modality == "text"
    assert text_ref.summary == "User asked about SAHIBEX."
    assert text_ref.reference_id

    vision_ref = integration.create_reference(
        input_id="vision-456",
        modality="image",
        summary="A red object is visible.",
    )

    assert vision_ref.input_id == "vision-456"
    assert vision_ref.modality == "image"
    assert vision_ref.summary == "A red object is visible."

    assert text_ref.reference_id != vision_ref.reference_id

    try:
        integration.create_reference(
            input_id="",
            modality="text",
            summary="Test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty input_id must be rejected."
        )

    try:
        integration.create_reference(
            input_id="input-123",
            modality="",
            summary="Test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty modality must be rejected."
        )

    try:
        integration.create_reference(
            input_id="input-123",
            modality="text",
            summary="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty summary must be rejected."
        )

    fields = MultimodalMemoryReference.__dataclass_fields__

    forbidden_fields = {
        "permission",
        "authorization",
        "api_key",
        "credential",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    print(
        "SAHIBEX 6M-8 MULTIMODAL MEMORY INTEGRATION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
