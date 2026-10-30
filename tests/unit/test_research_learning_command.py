from dataclasses import dataclass

import pytest

from core.brain.research_learning_command import (
    DepartmentOperation,
    ResearchLearningCommander,
    TaskStage,
)


@dataclass
class FakeResult:
    success: bool
    verified: bool
    verification_status: str = "VERIFIED"


def test_commander_routes_research_to_research_army_and_labour_worker():
    result = ResearchLearningCommander().dispatch(
        DepartmentOperation.RESEARCH, "AI safety", lambda: FakeResult(True, True)
    )
    assert result.result.verified is True
    assert result.trace.army_id == "research_army"
    assert result.trace.labour_brain_id == "research_pipeline_labour"
    assert result.trace.status is TaskStage.COMPLETED
    assert [event.stage for event in result.trace.events] == [
        TaskStage.RECEIVED, TaskStage.PLANNED, TaskStage.ARMY_ASSIGNED,
        TaskStage.LABOUR_ASSIGNED, TaskStage.RUNNING, TaskStage.COMPLETED,
    ]


def test_commander_routes_learning_to_learning_army():
    result = ResearchLearningCommander().dispatch(
        DepartmentOperation.LEARN, "topic", lambda: FakeResult(True, True)
    )
    assert result.trace.army_id == "learning_army"
    assert result.trace.labour_brain_id == "learning_pipeline_labour"


def test_commander_does_not_mark_unverified_result_complete():
    result = ResearchLearningCommander().dispatch(
        DepartmentOperation.RESEARCH, "current news",
        lambda: FakeResult(False, False, "PENDING"),
    )
    assert result.trace.status is TaskStage.UNVERIFIED


def test_commander_rejects_empty_subject_and_unknown_operation():
    commander = ResearchLearningCommander()
    with pytest.raises(ValueError):
        commander.dispatch(DepartmentOperation.RESEARCH, " ", lambda: object())
    with pytest.raises(TypeError):
        commander.dispatch("research", "query", lambda: object())  # type: ignore[arg-type]


def test_commander_records_failure_without_exposing_exception_text():
    commander = ResearchLearningCommander()
    def fail():
        raise RuntimeError("secret/path/query must not be in telemetry")
    with pytest.raises(RuntimeError):
        commander.dispatch(DepartmentOperation.RESEARCH, "query", fail)
    assert commander.last_trace is not None
    assert commander.last_trace.status is TaskStage.FAILED
    assert "secret/path/query" not in repr(commander.last_trace.events)


def test_commander_cannot_grant_authority_or_create_child_brains():
    contract = ResearchLearningCommander().capability_contract()
    assert contract["permission_authority"] is False
    assert contract["tool_execution_authority"] is False
    assert contract["constitution_mutation"] is False
    assert contract["child_brain_creation"] is False


def test_dispatch_workers_runs_both_callbacks_and_requires_joint_verification():
    commander = ResearchLearningCommander()
    calls = []
    result = commander.dispatch_workers(
        DepartmentOperation.RESEARCH,
        "verify claim",
        army_worker=lambda subject: calls.append(("army", subject)) or {"claim": "A"},
        labour_worker=lambda subject: calls.append(("labour", subject)) or {"evidence": "A"},
        verify_results=lambda army, labour: army["claim"] == labour["evidence"],
    )
    assert calls == [("army", "verify claim"), ("labour", "verify claim")]
    assert result.trace.status is TaskStage.COMPLETED
    assert result.result["verification_status"] == "VERIFIED"


def test_dispatch_workers_missing_or_conflicting_result_fails_closed():
    commander = ResearchLearningCommander()
    missing = commander.dispatch_workers(
        DepartmentOperation.RESEARCH, "verify",
        army_worker=lambda subject: {"claim": "A"},
        labour_worker=lambda subject: None,
        verify_results=lambda army, labour: True,
    )
    assert missing.trace.status is TaskStage.UNVERIFIED
    conflict = commander.dispatch_workers(
        DepartmentOperation.RESEARCH, "verify",
        army_worker=lambda subject: {"claim": "A"},
        labour_worker=lambda subject: {"claim": "B"},
        verify_results=lambda army, labour: army["claim"] == labour["claim"],
    )
    assert conflict.trace.status is TaskStage.UNVERIFIED


def test_dispatch_workers_rejects_same_callback_for_both_roles():
    worker = lambda subject: {"ok": True}
    try:
        ResearchLearningCommander().dispatch_workers(
            DepartmentOperation.RESEARCH, "verify",
            army_worker=worker, labour_worker=worker,
            verify_results=lambda army, labour: True,
        )
    except ValueError as exc:
        assert "distinct" in str(exc)
    else:
        raise AssertionError("same callback was accepted for both roles")
