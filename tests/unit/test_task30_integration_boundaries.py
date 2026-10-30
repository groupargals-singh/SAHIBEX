from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.brain.internal_brain_team import InternalBrainTeam
from core.brain.master_brain import MasterBrain


def test_internal_dispatch_rejects_truthy_non_boolean_gate_flags() -> None:
    team = InternalBrainTeam()
    calls: list[str] = []
    team.register_handler("reading", lambda request, context: calls.append(request))

    for invalid in ("false", "yes", 1, None):
        result = team.dispatch(
            "reading", "read this", {},
            authorization_passed=invalid,  # type: ignore[arg-type]
            verification_passed=True,
        )
        assert not result.accepted
        assert "explicit booleans" in result.reason

    result = team.dispatch(
        "reading", "read this", {},
        authorization_passed=True,
        verification_passed="false",  # type: ignore[arg-type]
    )
    assert not result.accepted
    assert "explicit booleans" in result.reason
    assert calls == []


def test_internal_dispatch_rejects_non_dictionary_context() -> None:
    team = InternalBrainTeam()
    calls: list[str] = []
    team.register_handler("reading", lambda request, context: calls.append(request))
    result = team.dispatch(
        "reading", "read this", [("confirmation", True)],  # type: ignore[arg-type]
        authorization_passed=True,
        verification_passed=True,
    )
    assert not result.accepted
    assert "context must be a dictionary" in result.reason
    assert calls == []


def test_research_handler_does_not_coerce_string_confirmation_to_true() -> None:
    brain = MasterBrain()
    calls: list[bool] = []
    brain.research_learning_brain = SimpleNamespace(
        research_topic=lambda request, *, confirmation: calls.append(confirmation)
    )
    result = brain._internal_research_handler("query", {"confirmation": "false"})
    assert result["success"] is False
    assert result["verified"] is False
    assert calls == []


def test_learning_handler_does_not_coerce_integer_confirmation_to_true() -> None:
    brain = MasterBrain()
    calls: list[bool] = []
    brain.research_learning_brain = SimpleNamespace(
        learn_topic=lambda topic, *, confirmation: calls.append(confirmation)
    )
    result = brain._internal_learning_handler("topic", {"confirmation": 1})
    assert result["success"] is False
    assert result["persisted"] is False
    assert calls == []


def test_main_brain_emergency_stop_is_shared_with_tool_brain() -> None:
    brain = MasterBrain()
    assert brain.tool_brain.emergency_stop is brain.emergency_stop

    brain.emergency_stop.engage("task 30 integration regression")
    result = brain.tool_brain.execute("list directory")
    assert result.success is False
    assert result.allowed is False
    assert result.recovery_status == "BLOCKED"
    assert "Emergency stop is engaged" in (result.error or "")
