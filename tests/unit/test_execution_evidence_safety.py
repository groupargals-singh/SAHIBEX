from __future__ import annotations

import json
import tempfile
from pathlib import Path

from security.audit.execution_evidence import (
    ExecutionEvidence,
    ExecutionEvidenceRecorder,
)


def test_execution_evidence_records_complete_execution_chain(
    tmp_path: Path,
) -> None:
    recorder = ExecutionEvidenceRecorder(tmp_path)

    evidence = recorder.record(
        tool="read_file",
        action="read_file",
        permission_allowed=True,
        confirmation_required=False,
        confirmation_provided=False,
        attempts=1,
        result={"content": "hello"},
        verification_status="VERIFIED",
        recovery_status="SUCCESS",
        final_status="SUCCESS",
        error=None,
        risk="low",
        reason="Tool result verified successfully.",
    )

    assert isinstance(evidence, ExecutionEvidence)
    assert evidence.execution_id
    assert evidence.tool == "read_file"
    assert evidence.action == "read_file"
    assert evidence.permission_allowed is True
    assert evidence.confirmation_required is False
    assert evidence.confirmation_provided is False
    assert evidence.attempts == 1
    assert evidence.verification_status == "VERIFIED"
    assert evidence.recovery_status == "SUCCESS"
    assert evidence.final_status == "SUCCESS"
    assert evidence.error is None


def test_execution_id_can_be_provided(tmp_path: Path) -> None:
    recorder = ExecutionEvidenceRecorder(tmp_path)

    evidence = recorder.record(
        execution_id="execution-test-001",
        tool="file_info",
        action="read_file",
        permission_allowed=True,
        confirmation_required=False,
        confirmation_provided=False,
        attempts=1,
        result={"exists": True},
        verification_status="VERIFIED",
        recovery_status="SUCCESS",
        final_status="SUCCESS",
        error=None,
        risk="low",
        reason="Verified.",
    )

    assert evidence.execution_id == "execution-test-001"


def test_confirmation_state_is_protected(tmp_path: Path) -> None:
    recorder = ExecutionEvidenceRecorder(tmp_path)

    try:
        recorder.record(
            tool="read_file",
            action="read_file",
            permission_allowed=True,
            confirmation_required=False,
            confirmation_provided=True,
            attempts=1,
            result={"content": "hello"},
            verification_status="VERIFIED",
            recovery_status="SUCCESS",
            final_status="SUCCESS",
            error=None,
            risk="low",
            reason="Invalid confirmation state.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Invalid confirmation state was accepted."
        )


def test_execution_attempt_count_is_validated(tmp_path: Path) -> None:
    recorder = ExecutionEvidenceRecorder(tmp_path)

    try:
        recorder.record(
            tool="read_file",
            action="read_file",
            permission_allowed=True,
            confirmation_required=False,
            confirmation_provided=False,
            attempts=0,
            result={"content": "hello"},
            verification_status="VERIFIED",
            recovery_status="SUCCESS",
            final_status="SUCCESS",
            error=None,
            risk="low",
            reason="Invalid attempt count.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Invalid attempt count was accepted."
        )


def test_evidence_is_persisted_as_jsonl(tmp_path: Path) -> None:
    recorder = ExecutionEvidenceRecorder(tmp_path)

    recorder.record(
        tool="search_local_files",
        action="read_file",
        permission_allowed=True,
        confirmation_required=False,
        confirmation_provided=False,
        attempts=1,
        result={"matches": ["test.py"]},
        verification_status="VERIFIED",
        recovery_status="SUCCESS",
        final_status="SUCCESS",
        error=None,
        risk="low",
        reason="Search completed and verified.",
    )

    assert recorder.log_file.exists()

    lines = recorder.log_file.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    record = json.loads(lines[0])

    assert record["tool"] == "search_local_files"
    assert record["permission_allowed"] is True
    assert record["verification_status"] == "VERIFIED"
    assert record["recovery_status"] == "SUCCESS"
    assert record["final_status"] == "SUCCESS"


def test_read_recent_returns_valid_records(
    tmp_path: Path,
) -> None:
    recorder = ExecutionEvidenceRecorder(tmp_path)

    recorder.record(
        tool="file_info",
        action="read_file",
        permission_allowed=True,
        confirmation_required=False,
        confirmation_provided=False,
        attempts=1,
        result={"exists": True},
        verification_status="VERIFIED",
        recovery_status="SUCCESS",
        final_status="SUCCESS",
        error=None,
        risk="low",
        reason="Verified.",
    )

    records = recorder.read_recent()

    assert len(records) == 1
    assert records[0]["tool"] == "file_info"


def test_security_boundary_has_no_execution_authority(
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        forbidden_methods = {
            "execute",
            "invoke",
            "grant_permission",
            "require_permission",
            "modify_constitution",
            "update_constitution",
        }

        public_methods = set(dir(recorder))

        assert not (
            forbidden_methods & public_methods
        ), (
            "Execution evidence recorder exposes "
            "forbidden authority."
        )


def test_security_boundary_does_not_change_permission(
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = ExecutionEvidenceRecorder(
            Path(directory)
        )

        evidence = recorder.record(
            tool="read_file",
            action="read_file",
            permission_allowed=False,
            confirmation_required=True,
            confirmation_provided=False,
            attempts=1,
            result=None,
            verification_status="NOT_VERIFIED",
            recovery_status="BLOCKED",
            final_status="BLOCKED",
            error="Permission required.",
            risk="medium",
            reason=(
                "Protected action requires "
                "user confirmation."
            ),
        )

        assert evidence.permission_allowed is False
        assert evidence.confirmation_required is True
        assert evidence.confirmation_provided is False
        assert evidence.final_status == "BLOCKED"


def run_all_tests() -> None:
    with tempfile.TemporaryDirectory() as directory:
        test_execution_evidence_records_complete_execution_chain(
            Path(directory)
        )

    with tempfile.TemporaryDirectory() as directory:
        test_execution_id_can_be_provided(
            Path(directory)
        )

    with tempfile.TemporaryDirectory() as directory:
        test_confirmation_state_is_protected(
            Path(directory)
        )

    with tempfile.TemporaryDirectory() as directory:
        test_execution_attempt_count_is_validated(
            Path(directory)
        )

    with tempfile.TemporaryDirectory() as directory:
        test_evidence_is_persisted_as_jsonl(
            Path(directory)
        )

    with tempfile.TemporaryDirectory() as directory:
        test_read_recent_returns_valid_records(
            Path(directory)
        )

    test_security_boundary_has_no_execution_authority()
    test_security_boundary_does_not_change_permission()

if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-10 EXECUTION EVIDENCE SAFETY TEST: PASS"
    )
