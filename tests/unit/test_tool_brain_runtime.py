from __future__ import annotations

from pathlib import Path
import errno

from core.brain.master_brain import MasterBrain
from core.brain.tool_brain import ToolBrain
from core.policies.approval import PermissionEngine
from security.audit.execution_trace import ExecutionTraceVerifier


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_tool_brain_capability_and_security_contract() -> None:
    brain = ToolBrain(
        permission_engine=PermissionEngine(),
        project_root=PROJECT_ROOT,
    )

    capabilities = brain.capability_contract()

    assert capabilities["tool_discovery"] is True
    assert capabilities["tool_selection"] is True
    assert capabilities["permission_check"] is True
    assert capabilities["safe_execution"] is True
    assert capabilities["result_verification"] is True
    assert capabilities["failure_recovery"] is True
    assert capabilities["protected_action_support"] is True
    assert capabilities["permission_authority"] is False
    assert capabilities["constitution_mutation"] is False
    assert capabilities["human_authority_override"] is False


def test_tool_brain_discovers_and_executes_read_only_tool() -> None:
    brain = ToolBrain(
        permission_engine=PermissionEngine(),
        project_root=PROJECT_ROOT,
    )

    candidates = brain.discover("read file")

    assert candidates
    assert candidates[0].name == "read_file"

    result = brain.execute(
        "read file",
        path="tools/registry.py",
        max_bytes=2000,
    )

    assert result.success is True
    assert result.allowed is True
    assert result.tool == "read_file"
    assert result.recovery_status == "SUCCESS"
    assert result.attempts == 1
    assert result.error is None
    assert result.result is not None


def test_tool_brain_protected_tool_stops_before_execution_without_confirmation() -> None:
    brain = ToolBrain(
        permission_engine=PermissionEngine(),
        project_root=PROJECT_ROOT,
    )

    candidates = brain.discover("computer control")
    assert candidates
    assert candidates[0].name == "computer_control"

    result = brain.execute(
        "computer control",
        action="screenshot",
        parameters={},
        user_confirmation=False,
    )

    assert result.success is False
    assert result.allowed is False
    assert result.requires_confirmation is True
    assert result.tool == "computer_control"
    assert result.recovery_status == "BLOCKED"


def test_master_brain_owns_tool_brain() -> None:
    brain = MasterBrain()

    assert isinstance(brain.tool_brain, ToolBrain)
    assert brain.tool_brain.capability_contract()["human_authority_override"] is False



def test_protected_write_and_delete_have_authenticated_intent_and_result_audit(tmp_path):
    brain = ToolBrain(
        permission_engine=PermissionEngine(),
        project_root=tmp_path,
    )
    target = tmp_path / "ONLY_DISPOSABLE_TEST_FILE.txt"

    denied = brain.execute(
        "write file ONLY_DISPOSABLE_TEST_FILE.txt with DENIED",
        user_confirmation=False,
    )
    assert denied.success is False
    assert not target.exists()

    created = brain.execute(
        "write file ONLY_DISPOSABLE_TEST_FILE.txt with SAHIBEX P1 AUDIT",
        user_confirmation=True,
    )
    assert created.success is True
    assert target.read_text(encoding="utf-8") == "SAHIBEX P1 AUDIT"

    records = brain.evidence_recorder.read_recent(limit=3)
    assert [item["final_status"] for item in records] == [
        "BLOCKED", "PENDING", "SUCCESS"
    ]
    assert records[0]["permission_allowed"] is False
    assert records[1]["confirmation_required"] is True
    assert records[1]["confirmation_provided"] is True
    assert records[2]["confirmation_required"] is True
    assert records[2]["confirmation_provided"] is True
    assert records[2]["result"]["sha256"]
    assert "SAHIBEX P1 AUDIT" not in str(records[2]["result"])
    for record in records:
        assert ExecutionTraceVerifier().verify_provenance(
            record, brain.evidence_recorder.log_directory
        ).verified is True

    deleted = brain.execute(
        "delete file ONLY_DISPOSABLE_TEST_FILE.txt",
        user_confirmation=True,
    )
    assert deleted.success is True
    assert not target.exists()
    records = brain.evidence_recorder.read_recent(limit=2)
    assert [item["final_status"] for item in records] == ["PENDING", "SUCCESS"]
    assert all(item["confirmation_provided"] is True for item in records)
    for record in records:
        assert ExecutionTraceVerifier().verify_provenance(
            record, brain.evidence_recorder.log_directory
        ).verified is True


def test_protected_execution_fails_closed_when_intent_audit_cannot_be_written(
    tmp_path, monkeypatch
):
    brain = ToolBrain(
        permission_engine=PermissionEngine(),
        project_root=tmp_path,
    )
    target = tmp_path / "MUST_NOT_BE_CREATED.txt"

    def fail_audit(**kwargs):
        raise OSError("simulated audit storage failure")

    monkeypatch.setattr(brain.evidence_recorder, "record_authenticated", fail_audit)
    result = brain.execute(
        "write file MUST_NOT_BE_CREATED.txt with NO",
        user_confirmation=True,
    )
    assert result.success is False
    assert result.recovery_status == "BLOCKED"
    assert "audit could not be persisted" in (result.error or "")
    assert not target.exists()


def test_simulated_disk_full_blocks_protected_write_before_side_effect(tmp_path, monkeypatch):
    """ENOSPC in Tool Brain's authenticated intent audit must fail closed."""
    brain = ToolBrain(
        permission_engine=PermissionEngine(),
        project_root=tmp_path,
    )
    target = tmp_path / "P9_DISK_FULL_MUST_NOT_WRITE.txt"

    def disk_full(**kwargs):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(brain.evidence_recorder, "record_authenticated", disk_full)
    result = brain.execute(
        "write file P9_DISK_FULL_MUST_NOT_WRITE.txt with SHOULD NOT EXIST",
        user_confirmation=True,
    )

    assert result.success is False
    assert result.allowed is True  # permission policy allowed it; audit failure still blocked execution
    assert result.recovery_status == "BLOCKED"
    assert result.audit_recorded is False
    assert "Fail-closed audit precondition failed" in result.reason
    assert not target.exists(), "protected side effect executed despite ENOSPC"
