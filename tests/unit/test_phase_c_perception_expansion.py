from core.brain.perception import PerceptionParser
from core.brain.entity_identification import EntityIdentificationEngine
from core.brain.event_detection import EventDetectionEngine
from core.brain.context_extraction import ContextExtractionEngine
from core.brain.meaning_interpretation import MeaningInterpretationEngine
from core.brain.intent import IntentEngine
from core.brain.uncertainty import UncertaintyEngine
from core.brain.perception_expansion import (
    ObjectTargetIdentificationEngine,
    TemporalUnderstandingEngine,
    SpatialUnderstandingEngine,
    PerceptionResultFusionEngine,
)


def main() -> None:
    text = "SAHIBEX is working here today after the event."

    p = PerceptionParser().parse(input_id="c-1", content=text)
    assert p.content
    assert p.objects

    e = EntityIdentificationEngine().identify(input_id="c-1", content="SAHIBEX AI")
    assert e.candidates

    ev = EventDetectionEngine().detect(input_id="c-1", events=("completed",))
    assert ev.events

    ctx = ContextExtractionEngine().extract(
        input_id="c-1", content=text, source_id="user",
        timestamp="2026-10-07T10:00:00+00:00", subjects=p.subjects,
        actions=p.actions, objects=p.objects, events=p.events,
        attributes=p.attributes,
    )
    assert ctx.signal_count > 0

    meaning = MeaningInterpretationEngine().interpret(input_id="c-1", content=text)
    assert meaning

    intent = IntentEngine().detect("create a program")
    assert intent.intent in {"create", "code"}

    uncertainty = UncertaintyEngine().assess(
        input_id="c-1", confidence=0.8, quality_score=0.9
    )
    assert 0.0 <= uncertainty.uncertainty <= 1.0

    target = ObjectTargetIdentificationEngine().identify(input_id="c-1", content="open website")
    assert "website" in target.targets

    temporal = TemporalUnderstandingEngine().understand(input_id="c-1", content=text)
    assert "today" in temporal.temporal_markers
    assert "after" in temporal.temporal_markers

    spatial = SpatialUnderstandingEngine().understand(input_id="c-1", content=text)
    assert "here" in spatial.spatial_markers

    fused = PerceptionResultFusionEngine().fuse(
        input_id="c-1",
        signal_groups=[("sahibex", "today"), ("today", "here")],
    )
    assert fused.merged_signals == ("sahibex", "today", "here")

    print("SAHIBEX PHASE C PERCEPTION EXPANSION TEST: PASS")


if __name__ == "__main__":
    main()
