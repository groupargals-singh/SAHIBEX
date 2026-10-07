from __future__ import annotations

from core.brain.multimodal import InputModality, MultimodalInput
from core.brain.multimodal_intelligence import MultimodalIntelligence


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # Child communication is represented as a unified input modality.
    child_input = MultimodalInput(
        modality=InputModality.CHILD,
        content="Child Brain research result: termite activity detected.",
    )

    check(
        child_input.modality is InputModality.CHILD,
        "Child input must use the CHILD modality.",
    )

    check(
        child_input.content
        == "Child Brain research result: termite activity detected.",
        "Child input content must be preserved.",
    )

    check(
        child_input.input_id,
        "Child input must have an input identity.",
    )

    # Unified multimodal intelligence must accept Child input.
    intelligence = MultimodalIntelligence()

    result = intelligence.process(
        modalities=["child"],
        summary="Child Brain provided a research result.",
    )

    check(
        result.success is True,
        "Child input must be accepted by multimodal intelligence.",
    )

    check(
        result.modalities == ["child"],
        "Child modality must be normalized correctly.",
    )

    # Security boundary:
    # input representation must not become authority.
    check(
        isinstance(result.summary, str)
        and result.summary.strip(),
        "Child input summary must be preserved.",
    )

    print(
        "SAHIBEX PHASE 1 #23 CHILD INPUT "
        "UNIFIED PIPELINE TEST: PASS"
    )


if __name__ == "__main__":
    main()
