from __future__ import annotations

from core.brain.multimodal_safety import (
    MultimodalSafetyPolicy,
    MultimodalSafetyResult,
)


def main() -> None:
    policy = MultimodalSafetyPolicy()

    text_result = policy.evaluate(
        modality="text",
        action="read",
    )

    assert isinstance(text_result, MultimodalSafetyResult)
    assert text_result.allowed is True
    assert text_result.requires_confirmation is False
    assert text_result.reason

    voice_result = policy.evaluate(
        modality="voice",
        action="write",
    )

    assert isinstance(voice_result, MultimodalSafetyResult)
    assert voice_result.allowed is False
    assert voice_result.requires_confirmation is True
    assert voice_result.reason

    image_result = policy.evaluate(
        modality="image",
        action="delete",
    )

    assert image_result.allowed is False
    assert image_result.requires_confirmation is True
    assert image_result.reason

    try:
        policy.evaluate(
            modality="",
            action="read",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty modality must be rejected."
        )

    try:
        policy.evaluate(
            modality="text",
            action="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty action must be rejected."
        )

    fields = MultimodalSafetyResult.__dataclass_fields__

    forbidden_fields = {
        "api_key",
        "credential",
        "permission_grant",
        "authorization_token",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    assert not hasattr(
        MultimodalSafetyPolicy,
        "grant_permission",
    )

    print(
        "SAHIBEX 6M-9 MULTIMODAL PERMISSION SAFETY CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
