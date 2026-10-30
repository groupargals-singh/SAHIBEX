from pathlib import Path

from core.brain.master_brain import MasterBrain
from core.brain.sahibex_execution_loop import SahibexExecutionLoop
from security.audit.execution_evidence import ExecutionEvidenceRecorder


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_main_execution_loop_read_only_tool(tmp_path) -> None:
    loop = SahibexExecutionLoop(
        brain=MasterBrain(),
        project_root=PROJECT_ROOT,
        evidence_recorder=ExecutionEvidenceRecorder(tmp_path / "audit"),
    )

    result = loop.process(
        "Read file core/brain/master_brain.py"
    )

    assert result.success is True
    assert result.status == "COMPLETED"
    assert result.brain.plan_created is True
    assert result.brain.goal_id
    assert result.tool is not None
    assert result.tool.success is True
    assert result.tool.allowed is True
    assert result.tool.tool == "read_file"
    assert result.metadata["verified"] is True
    assert result.observation_count == 1
    assert "master_brain.py" in result.response
    assert result.metadata["audit_recorded"] is True
    evidence = loop.evidence_recorder.read_recent()
    assert len(evidence) == 1
    assert evidence[0]["permission_allowed"] is True
    assert evidence[0]["final_status"] == "SUCCESS"
    assert evidence[0]["verification_status"] == "VERIFIED"
    assert evidence[0]["result"]["sha256"]
    assert "master_brain.py" not in str(evidence[0]["result"])
    assert loop.recovery.state.value == "ready"


def test_main_execution_loop_protected_request_stops_before_execution(tmp_path) -> None:
    loop = SahibexExecutionLoop(
        brain=MasterBrain(),
        project_root=PROJECT_ROOT,
        evidence_recorder=ExecutionEvidenceRecorder(tmp_path / "audit"),
    )

    result = loop.process(
        "Delete the project files."
    )

    assert result.success is False
    assert result.status == "WAITING_APPROVAL"
    assert result.tool is None
    assert result.brain.confirmation_required is True
    assert result.metadata["execution_skipped"] is True
    evidence = loop.evidence_recorder.read_recent()
    assert len(evidence) == 1
    assert evidence[0]["permission_allowed"] is False
    assert evidence[0]["confirmation_required"] is True
    assert evidence[0]["final_status"] == "BLOCKED"
    assert evidence[0]["result"] is None


def test_main_execution_loop_cognitive_request(tmp_path) -> None:
    loop = SahibexExecutionLoop(
        brain=MasterBrain(),
        project_root=PROJECT_ROOT,
        evidence_recorder=ExecutionEvidenceRecorder(tmp_path / "audit"),
    )

    result = loop.process(
        "Explain how SAHIBEX works."
    )

    # With no verified knowledge, the loop completes safely by disclosing
    # uncertainty; no tool is invoked and no factual claim is fabricated.
    assert result.success is True
    assert result.status == "COMPLETED"
    assert result.tool is None
    assert result.brain.plan_created is True
    assert result.brain.verification_status == "INSUFFICIENT_EVIDENCE"
    assert "enough verified evidence" in result.response.lower()


def test_main_execution_loop_never_grants_authority(tmp_path) -> None:
    loop = SahibexExecutionLoop(
        brain=MasterBrain(),
        project_root=PROJECT_ROOT,
        evidence_recorder=ExecutionEvidenceRecorder(tmp_path / "audit"),
    )

    assert loop.recovery.grants_permission() is False
    assert loop.recovery.executes_actions() is False
    assert loop.recovery.overrides_human_authority() is False
    assert loop.observability.grants_permission is False
    assert loop.observability.is_authority is False
