from pathlib import Path
import sys
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.brain.master_brain import MasterBrain
from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.research.storage import ResearchStorage
from security.audit.audit_logger import AuditLogger


def _brain(tmp_path):
    storage = ResearchStorage(tmp_path / "mother-dynamic-tools.db")
    operational = MotherOperationalIntegration(storage=storage)
    return MasterBrain(
        mother_operational=operational,
        audit_logger=AuditLogger(tmp_path / "audit"),
        tool_project_root=tmp_path,
    )



def test_mother_brain_dynamic_tool_proposal_requires_separate_explicit_approval(tmp_path):
    brain = _brain(tmp_path)
    candidate = brain.propose_dynamic_tool(
        "create a tool to list files",
        context={"name": "user_custom_listing_brain"},
    )
    assert candidate.status == "STAGED"
    assert not brain.tool_brain.registry.has("user_custom_listing_brain")

    with pytest.raises(PermissionError):
        brain.approve_dynamic_tool_candidate(candidate.candidate_id)

    activated = brain.approve_dynamic_tool_candidate(
        candidate.candidate_id, user_approved=True
    )
    assert activated["status"] == "ACTIVE"
    assert activated["tool_activated"] is True
    assert brain.tool_brain.registry.has("user_custom_listing_brain")


def test_mother_brain_dynamic_tool_internal_role_is_authorization_and_verification_gated(tmp_path):
    brain = _brain(tmp_path)
    blocked = brain.internal_brain_team.dispatch(
        "web_tools", "create a tool to list files",
        {"name": "dispatch_list", "action": "propose_dynamic_tool"},
    )
    assert blocked.accepted is False
    assert "authorization" in blocked.reason

    proposed = brain.internal_brain_team.dispatch(
        "web_tools", "create a tool to list files",
        {"name": "dispatch_list", "action": "propose_dynamic_tool"},
        authorization_passed=True, verification_passed=True,
    )
    assert proposed.accepted is True
    assert proposed.result["status"] == "STAGED"
    assert proposed.result["tool_activated"] is False
    assert not brain.tool_brain.registry.has("dispatch_list")


def test_mother_brain_dynamic_tool_rollback_requires_explicit_approval(tmp_path):
    brain = _brain(tmp_path)
    candidate = brain.propose_dynamic_tool(
        "create a tool to list files", context={"name": "rollback_list"}
    )
    brain.approve_dynamic_tool_candidate(candidate.candidate_id, user_approved=True)
    with pytest.raises(PermissionError):
        brain.rollback_dynamic_tool_candidate(candidate.candidate_id)
    result = brain.rollback_dynamic_tool_candidate(
        candidate.candidate_id, user_approved=True
    )
    assert result["status"] == "ROLLED_BACK"
    assert not brain.tool_brain.registry.has("rollback_list")


def test_mother_brain_exposes_static_verification_and_status_without_execution(tmp_path):
    brain = _brain(tmp_path)
    candidate = brain.propose_dynamic_tool(
        "create a tool to list files", context={"name": "mother_verify_tool"}
    )
    verification = brain.verify_dynamic_tool_candidate(candidate.candidate_id)
    assert verification["valid"] is True
    assert verification["executed"] is False
    status = brain.dynamic_tool_creation_status()
    assert status["candidate_counts"]["STAGED"] == 1
    assert status["arbitrary_code_execution"] is False
    assert not brain.tool_brain.registry.has("mother_verify_tool")


def test_mother_brain_rejected_proposal_path_never_references_missing_candidate(tmp_path):
    brain = _brain(tmp_path)
    result = brain._internal_dynamic_tool_creation_handler(
        "ambiguous request", {"name": "should_not_exist"}
    )
    assert result["success"] is False
    assert result["tool_activated"] is False
    assert result["approval_required"] is True
