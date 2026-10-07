from datetime import timezone

from core.brain.observability_expansion import (
    ErrorObservation,
    ModelToolObservation,
    ObservationEvent,
    ObservabilityEngine,
)


def test_phase_y_observation_records_core_fields():
    engine = ObservabilityEngine(max_events=2)
    event = engine.record(
        ObservationEvent(
            event_type="task.completed",
            actor_id="root",
            task_id="task-1",
            model_id="mock",
            tool_id="read_file",
            result_status="success",
            verification_status="verified",
            resource_usage={"duration_ms": 4},
        )
    )
    assert event.actor_id == "root"
    assert event.timestamp.tzinfo is not None
    assert event.timestamp.utcoffset() is not None
    assert engine.is_authority is False
    assert engine.grants_permission is False
    assert engine.model_tool_events() == (event,)
    assert engine.resource_usage() == ({"duration_ms": 4},)


def test_phase_y_error_observation_is_visible():
    engine = ObservabilityEngine()
    error = ErrorObservation("tool_error", "failed", True)
    event = engine.record(
        ObservationEvent(
            event_type="task.failed",
            actor_id="root",
            error_class=error.error_class,
            metadata={"message": error.message, "recoverable": error.recoverable},
        )
    )
    assert engine.errors() == (event,)


def test_phase_y_retains_bounded_history():
    engine = ObservabilityEngine(max_events=2)
    for index in range(3):
        engine.record(ObservationEvent("tick", "root", metadata={"i": index}))
    assert len(engine.snapshot()) == 2
    assert engine.latest().metadata["i"] == 2


def test_phase_y_model_tool_value_object():
    item = ModelToolObservation("model-a", "tool-a", "provider-a", "read", True)
    assert item.model_id == "model-a"
    assert item.tool_id == "tool-a"
