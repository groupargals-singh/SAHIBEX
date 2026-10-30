from __future__ import annotations

from pathlib import Path

from core.brain.master_brain import MasterBrain
from core.brain.operational_verification import OperationalVerificationResult
from core.brain.sahibex_execution_loop import SahibexExecutionLoop
from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.brain.mother_research_integration import MotherResearchIntegration
from core.brain.tool_brain import ToolBrain
from core.policies.approval import PermissionEngine
from core.research.storage import ResearchStorage
from security.audit.execution_evidence import ExecutionEvidenceRecorder
from security.audit.execution_trace import ExecutionTraceVerifier


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_main_brain_execution_fails_closed_if_audit_write_fails(tmp_path, monkeypatch) -> None:
    recorder = ExecutionEvidenceRecorder(tmp_path / "audit")

    def fail_audit_write(**kwargs):
        raise OSError("simulated audit storage failure")

    monkeypatch.setattr(recorder, "record_authenticated", fail_audit_write)
    loop = SahibexExecutionLoop(
        brain=MasterBrain(),
        project_root=PROJECT_ROOT,
        evidence_recorder=recorder,
    )

    result = loop.process("Read file core/brain/master_brain.py")

    assert result.success is False
    assert result.status == "FAILED"
    assert result.metadata["audit_recorded"] is False
    assert result.metadata["verified"] is False
    assert "execution evidence" in result.response.lower()


def test_main_brain_execution_does_not_bypass_failed_verifier(tmp_path, monkeypatch) -> None:
    recorder = ExecutionEvidenceRecorder(tmp_path / "audit")
    loop = SahibexExecutionLoop(
        brain=MasterBrain(),
        project_root=PROJECT_ROOT,
        evidence_recorder=recorder,
    )

    def reject_tool_result(_tool_result):
        return OperationalVerificationResult(
            success=False,
            verified=False,
            verification_status="VERIFICATION_FAILED",
            recovery_status="FAILED",
            attempts=1,
            retryable=False,
            reason="Forced independent-verification rejection.",
            result=None,
        )

    monkeypatch.setattr(loop.verifier, "verify_tool_result", reject_tool_result)
    result = loop.process("Read file core/brain/master_brain.py")

    assert result.success is False
    assert result.status == "FAILED"
    assert result.metadata["verified"] is False
    assert result.metadata["verification_status"] == "VERIFICATION_FAILED"
    evidence = recorder.read_recent()
    assert len(evidence) == 1
    assert evidence[0]["final_status"] == "FAILED"
    assert evidence[0]["verification_status"] == "VERIFICATION_FAILED"
    assert evidence[0]["result"] is None



def test_main_brain_protected_write_is_verified_and_audited_in_disposable_root(tmp_path):
    storage = ResearchStorage(tmp_path / "main-brain.db")
    try:
        operational = MotherOperationalIntegration(storage=storage)
        research = MotherResearchIntegration(storage=storage)
        brain = MasterBrain(
            mother_operational=operational,
            mother_research=research,
        )
        # Replace only this test instance's Tool Brain root; no project paths
        # or production storage are used by the protected write.
        brain.tool_brain = ToolBrain(
            permission_engine=brain.permission,
            project_root=tmp_path,
        )
        loop_recorder = ExecutionEvidenceRecorder(tmp_path / "loop-audit")
        loop = SahibexExecutionLoop(
            brain=brain,
            project_root=tmp_path,
            evidence_recorder=loop_recorder,
        )

        result = loop.process(
            "Write file ONLY_DISPOSABLE_MAIN_BRAIN_TEST.txt with MAIN BRAIN AUDIT PASS",
            user_confirmation=True,
        )
        target = tmp_path / "ONLY_DISPOSABLE_MAIN_BRAIN_TEST.txt"
        assert result.success is True
        assert result.status == "COMPLETED"
        assert result.metadata["execution_kind"] == "protected_tool"
        assert result.metadata["verified"] is True
        assert result.metadata["audit_recorded"] is True
        assert target.read_text(encoding="utf-8") == "MAIN BRAIN AUDIT PASS"

        # Exercise the read path through the same Main Brain loop, then delete
        # only this disposable target through the protected-action path.
        read_result = loop.process("Read file ONLY_DISPOSABLE_MAIN_BRAIN_TEST.txt")
        assert read_result.success is True
        assert read_result.metadata.get("verified") is True
        assert "MAIN BRAIN AUDIT PASS" in read_result.response
        assert target.read_text(encoding="utf-8") == "MAIN BRAIN AUDIT PASS"

        delete_result = loop.process(
            "Delete file ONLY_DISPOSABLE_MAIN_BRAIN_TEST.txt",
            user_confirmation=True,
        )
        assert delete_result.success is True
        assert delete_result.metadata.get("verified") is True
        assert delete_result.metadata.get("audit_recorded") is True
        assert not target.exists()

        evidence = brain.tool_brain.evidence_recorder.read_recent(limit=4)
        assert [item["final_status"] for item in evidence] == [
            "PENDING", "SUCCESS", "PENDING", "SUCCESS"
        ]
        assert all(item["confirmation_required"] is True for item in evidence)
        assert all(item["confirmation_provided"] is True for item in evidence)
        assert all(
            ExecutionTraceVerifier().verify_provenance(
                item, brain.tool_brain.evidence_recorder.log_directory
            ).verified
            for item in evidence
        )
        # The independent read-only loop writes its own success evidence;
        # protected write/delete evidence remains in the Tool Brain recorder.
        loop_records = loop_recorder.read_recent()
        assert len(loop_records) == 1
        assert loop_records[0]["final_status"] == "SUCCESS"
        assert loop_records[0]["verification_status"] == "VERIFIED"
        assert ExecutionTraceVerifier().verify_provenance(
            loop_records[0], loop_recorder.log_directory
        ).verified
    finally:
        storage.close()
