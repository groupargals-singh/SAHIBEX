from __future__ import annotations

from core.brain.multimodal_intelligence import (
    MultimodalIntelligence,
    MultimodalIntelligenceResult,
)


def main() -> None:
    intelligence = MultimodalIntelligence()

    result = intelligence.process(
        modalities=["text", "voice"],
        summary="User asked a question using text and voice context.",
    )

    assert isinstance(
        result,
        MultimodalIntelligenceResult,
    )

    assert result.success is True
    assert result.modalities == ["text", "voice"]
    assert result.summary == (
        "User asked a question using text and voice context."
    )
    assert result.result_id

    image_result = intelligence.process(
        modalities=["image"],
        summary="Image observation prepared for reasoning.",
    )

    assert image_result.success is True
    assert image_result.modalities == ["image"]
    assert image_result.result_id

    file_result = intelligence.process(
        modalities=["file"],
        summary="File input prepared for reasoning.",
    )

    assert file_result.success is True
    assert file_result.modalities == ["file"]
    assert file_result.summary == (
        "File input prepared for reasoning."
    )
    assert file_result.result_id

    mixed_result = intelligence.process(
        modalities=["text", "file", "image"],
        summary="Mixed multimodal input.",
    )

    assert mixed_result.success is True
    assert mixed_result.modalities == [
        "text",
        "file",
        "image",
    ]

    assert result.result_id != image_result.result_id
    assert image_result.result_id != file_result.result_id
    assert file_result.result_id != mixed_result.result_id

    try:
        intelligence.process(
            modalities=[],
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty modalities must be rejected."
        )

    try:
        intelligence.process(
            modalities=["text"],
            summary="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty summary must be rejected."
        )

    try:
        intelligence.process(
            modalities=["invalid"],
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Invalid modality must be rejected."
        )

    fields = (
        MultimodalIntelligenceResult
        .__dataclass_fields__
    )

    forbidden_fields = {
        "api_key",
        "credential",
        "authorization_token",
        "permission_grant",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    assert not hasattr(
        MultimodalIntelligence,
        "grant_permission",
    )

    assert not hasattr(
        MultimodalIntelligence,
        "execute_action",
    )

    print(
        "SAHIBEX 6M-10 MULTIMODAL INTELLIGENCE CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
