from core.brain.input_fusion import (
    FusionInput,
    FusionStatus,
    InputFusionEngine,
    InputFusionResult,
)
from core.brain.multimodal import (
    InputModality,
    MultimodalInput,
)


def main() -> None:
    engine = InputFusionEngine()

    # 1. Direct multi-source fusion
    text_input = FusionInput(
        source_id="text-source-001",
        modality="text",
        content="Machine temperature is high.",
        timestamp="2026-10-05T10:00:00+05:30",
        confidence=0.90,
        input_id="input-text-001",
    )

    sensor_input = FusionInput(
        source_id="sensor-source-001",
        modality="sensor",
        content="Temperature: 82 C.",
        timestamp="2026-10-05T10:00:01+05:30",
        confidence=0.95,
        input_id="input-sensor-001",
    )

    child_input = FusionInput(
        source_id="child-source-001",
        modality="child",
        content="Thermal anomaly detected.",
        timestamp="2026-10-05T10:00:02+05:30",
        confidence=0.85,
        input_id="input-child-001",
    )

    result = engine.fuse(
        [
            text_input,
            sensor_input,
            child_input,
        ]
    )

    assert isinstance(result, InputFusionResult)
    assert result.status is FusionStatus.FUSED
    assert len(result.inputs) == 3

    assert result.source_ids == [
        "text-source-001",
        "sensor-source-001",
        "child-source-001",
    ]

    assert result.modalities == [
        "text",
        "sensor",
        "child",
    ]

    assert result.confidence == (0.90 + 0.95 + 0.85) / 3

    assert "Machine temperature is high." in result.summary
    assert "Temperature: 82 C." in result.summary
    assert "Thermal anomaly detected." in result.summary

    # 2. Duplicate input IDs must be removed
    duplicate = FusionInput(
        source_id="sensor-source-duplicate",
        modality="sensor",
        content="Duplicate observation.",
        timestamp="2026-10-05T10:00:03+05:30",
        confidence=0.50,
        input_id="input-sensor-001",
    )

    duplicate_result = engine.fuse(
        [
            text_input,
            sensor_input,
            duplicate,
        ]
    )

    assert len(duplicate_result.inputs) == 2
    assert duplicate_result.source_ids == [
        "text-source-001",
        "sensor-source-001",
    ]

    # 3. Single input must be classified separately
    single_result = engine.fuse(
        [text_input]
    )

    assert single_result.status is FusionStatus.SINGLE
    assert len(single_result.inputs) == 1

    # 4. Multimodal input integration
    multimodal_inputs = [
        MultimodalInput(
            modality=InputModality.TEXT,
            content="User reports unusual machine noise.",
            input_id="multi-text-001",
        ),
        MultimodalInput(
            modality=InputModality.CHILD,
            content="Child reports vibration anomaly.",
            input_id="multi-child-001",
        ),
    ]

    multimodal_result = engine.from_multimodal(
        multimodal_inputs,
        source_id="multimodal-test",
        timestamp="2026-10-05T10:01:00+05:30",
        confidence=0.88,
    )

    assert isinstance(
        multimodal_result,
        InputFusionResult,
    )

    assert multimodal_result.status is FusionStatus.FUSED
    assert len(multimodal_result.inputs) == 2

    assert multimodal_result.modalities == [
        "text",
        "child",
    ]

    assert multimodal_result.source_ids == [
        "multimodal-test",
    ]

    assert multimodal_result.confidence == 0.88

    # 5. Duplicate multimodal input IDs must be removed
    multimodal_duplicate_result = engine.from_multimodal(
        [
            multimodal_inputs[0],
            multimodal_inputs[0],
        ],
        source_id="multimodal-test",
        timestamp="2026-10-05T10:02:00+05:30",
        confidence=0.80,
    )

    assert len(
        multimodal_duplicate_result.inputs
    ) == 1

    # 6. Invalid empty input must fail closed
    try:
        engine.fuse([])
        raise AssertionError(
            "empty fusion input was accepted"
        )
    except ValueError:
        pass

    # 7. Invalid confidence must fail closed
    try:
        FusionInput(
            source_id="invalid-source",
            modality="sensor",
            content="Invalid confidence.",
            timestamp="2026-10-05T10:03:00+05:30",
            confidence=1.5,
            input_id="invalid-001",
        )
        raise AssertionError(
            "invalid confidence was accepted"
        )
    except ValueError:
        pass

    # 8. Security / authority boundary
    assert engine.is_read_only() is True
    assert engine.grants_permission() is False
    assert engine.executes_actions() is False
    assert engine.modifies_memory() is False
    assert engine.modifies_sources() is False

    print(
        "SAHIBEX PHASE 1 #24 MULTI-SOURCE INPUT FUSION TEST: PASS"
    )


if __name__ == "__main__":
    main()
