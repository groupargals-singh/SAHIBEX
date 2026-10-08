from __future__ import annotations

from core.brain.human_interaction import (
    HumanInteractionEngine,
    InteractionLanguage,
)
from core.brain.multimodal import InputModality, MultimodalInput
from core.brain.voice import VoiceInput, VoiceInputFormat
from core.brain.voice_output import VoiceOutput, VoiceOutputFormat
from core.brain.vision import VisionInput, VisionInputFormat


def main() -> None:
    engine = HumanInteractionEngine()

    assert engine.detect_language("Hello SAHIBEX") is InteractionLanguage.ENGLISH
    assert engine.detect_language("मुझे यह समझाओ") is InteractionLanguage.HINDI
    assert engine.detect_language("Mujhe ye batao kaise karna hai") is InteractionLanguage.HINGLISH

    assessment = engine.assess("Mujhe SAHIBEX ke baare mein batao")
    assert assessment.language is InteractionLanguage.HINGLISH
    assert assessment.intent is not None
    assert assessment.intent.intent in {"explain", "general_request"}
    assert assessment.clarification_required is False

    correction = engine.assess("Nahi, mera matlab SAHIBEX ka reasoning system hai")
    assert correction.correction_detected is True
    assert correction.correction_text == "SAHIBEX ka reasoning system hai"

    ambiguous = engine.assess("ye karo")
    assert ambiguous.clarification_required is True
    assert ambiguous.clarification_question

    engine.record_turn(
        user="SAHIBEX ka logo dikhao",
        assistant="Theek hai.",
        intent="create",
    )
    contextual = engine.assess("isko karo")
    assert contextual.clarification_required is False

    voice = VoiceInput(
        content="Mujhe help karo",
        input_format=VoiceInputFormat.AUDIO,
        language="hi-Latn",
    )
    assert engine.prepare_voice_input(voice) == "Mujhe help karo"

    output = VoiceOutput(
        content="Main taiyar hoon.",
        output_format=VoiceOutputFormat.AUDIO,
        language="hi",
    )
    assert engine.prepare_voice_output(output) is output

    vision = VisionInput(
        content="image-bytes-or-reference",
        input_format=VisionInputFormat.IMAGE,
        source="camera",
    )
    vision_input = engine.prepare_vision_input(vision)
    assert isinstance(vision_input, MultimodalInput)
    assert vision_input.modality is InputModality.IMAGE
    assert vision_input.content == "image-bytes-or-reference"

    frame = VisionInput(
        content="frame-reference",
        input_format=VisionInputFormat.FRAME,
        source="android-camera",
    )
    frame_input = engine.prepare_vision_input(frame)
    assert frame_input.modality is InputModality.IMAGE

    multimodal = engine.prepare_multimodal([vision_input, frame_input])
    assert len(multimodal) == 2

    print("SAHIBEX PHASE 13 HUMAN INTERACTION TEST: PASS")


if __name__ == "__main__":
    main()
