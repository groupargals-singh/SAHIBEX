from __future__ import annotations

from core.brain.multimodal import (
    InputModality,
    MultimodalInput,
)
from core.brain.multimodal_context import MultimodalContext
from core.brain.multimodal_intelligence import (
    MultimodalIntelligence,
)


def main() -> None:
    file_input = MultimodalInput(
        modality=InputModality.FILE,
        content="example.pdf",
    )

    assert file_input.modality == InputModality.FILE
    assert file_input.content == "example.pdf"
    assert file_input.input_id

    context = MultimodalContext()

    context.add_input(
        file_input.input_id
    )

    assert context.input_count == 1
    assert file_input.input_id in context.inputs

    intelligence = MultimodalIntelligence()

    result = intelligence.process(
        modalities=["file"],
        summary="File input normalized for reasoning.",
    )

    assert result.success is True
    assert result.modalities == ["file"]
    assert result.summary == (
        "File input normalized for reasoning."
    )
    assert result.result_id

    fields = set(
        MultimodalInput.__dataclass_fields__
    )

    forbidden_fields = {
        "permission",
        "authorization",
        "api_key",
        "credential",
        "permission_grant",
    }

    assert forbidden_fields.isdisjoint(fields)

    print(
        "SAHIBEX PHASE 1 #19 FILE INPUT UNIFIED PIPELINE TEST: PASS"
    )


if __name__ == "__main__":
    main()
