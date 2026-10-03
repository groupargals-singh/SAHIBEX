from __future__ import annotations

from core.brain.multimodal_master_integration import (
    MultimodalMasterBrainIntegration,
    MultimodalMasterBrainResult,
)


def main() -> None:
    integration = MultimodalMasterBrainIntegration()

    result = integration.integrate(
        multimodal_result_id="multimodal-result-001",
        modalities=[
            "text",
            "voice",
            "image",
        ],
        summary="Multimodal context prepared for the master brain.",
    )

    assert isinstance(
        result,
        MultimodalMasterBrainResult,
    )

    assert result.success is True
    assert result.multimodal_result_id == (
        "multimodal-result-001"
    )
    assert result.modalities == [
        "text",
        "voice",
        "image",
    ]
    assert result.summary == (
        "Multimodal context prepared for the master brain."
    )
    assert result.integration_id

    second_result = integration.integrate(
        multimodal_result_id="multimodal-result-002",
        modalities=["text"],
        summary="Additional multimodal context.",
    )

    assert second_result.success is True
    assert second_result.integration_id != (
        result.integration_id
    )

    try:
        integration.integrate(
            multimodal_result_id="",
            modalities=["text"],
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty multimodal result ID must be rejected."
        )

    try:
        integration.integrate(
            multimodal_result_id="multimodal-result-001",
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
        integration.integrate(
            multimodal_result_id="multimodal-result-001",
            modalities=[""],
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty modality must be rejected."
        )

    try:
        integration.integrate(
            multimodal_result_id="multimodal-result-001",
            modalities=["text"],
            summary="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty summary must be rejected."
        )

    fields = MultimodalMasterBrainResult.__dataclass_fields__

    forbidden_fields = {
        "api_key",
        "credential",
        "authorization_token",
        "permission_grant",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    assert not hasattr(
        MultimodalMasterBrainIntegration,
        "grant_permission",
    )

    assert not hasattr(
        MultimodalMasterBrainIntegration,
        "execute_action",
    )

    print(
        "SAHIBEX 6N-6 MULTIMODAL MASTER BRAIN INTEGRATION "
        "CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
