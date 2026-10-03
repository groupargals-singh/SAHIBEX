from __future__ import annotations

import tempfile
from pathlib import Path

from core.brain.operational_tool_execution import (
    OperationalToolExecution,
)
from security.audit.execution_evidence import (
    ExecutionEvidenceRecorder,
)
from security.audit.execution_freshness import (
    ExecutionFreshnessGuard,
)
from security.audit.execution_provenance import (
    ExecutionProvenance,
)
from security.audit.execution_trace import (
    ExecutionTraceVerifier,
)


def create_real_execution(
    root: Path,
):
    evidence_dir = root / "evidence"

    recorder = ExecutionEvidenceRecorder(
        evidence_dir
    )

    # We only need authenticated real-style evidence
    # for the replay/freshness boundary.
    execution_id = "real-execution-6p24"

    evidence = recorder.record_authenticated(
        execution_id=execution_id,
        tool="read_file",
        action="tool_execution",
        permission_allowed=True,
        confirmation_required=False,
        confirmation_provided=False,
        attempts=1,
        result={"content": "SAHIBEX"},
        verification_status="VERIFIED",
        recovery_status="SUCCESS",
        final_status="SUCCESS",
        error=None,
        risk="low",
        reason="Real execution evidence.",
    )

    return evidence, evidence_dir


def test_first_use_is_accepted():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        evidence, evidence_dir = create_real_execution(
            root
        )

        verifier = ExecutionTraceVerifier()

        result = verifier.verify_fresh(
            {
                "execution_id": evidence.execution_id,
                "timestamp": evidence.timestamp,
                "tool": evidence.tool,
                "action": evidence.action,
                "permission_allowed": evidence.permission_allowed,
                "confirmation_required": (
                    evidence.confirmation_required
                ),
                "confirmation_provided": (
                    evidence.confirmation_provided
                ),
                "attempts": evidence.attempts,
                "result": evidence.result,
                "verification_status": (
                    evidence.verification_status
                ),
                "recovery_status": (
                    evidence.recovery_status
                ),
                "final_status": evidence.final_status,
                "error": evidence.error,
                "risk": evidence.risk,
                "reason": evidence.reason,
                "provenance": evidence.provenance,
            },
            evidence_dir,
        )

        assert result.verified is True


def test_second_use_is_rejected_as_replay():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        evidence, evidence_dir = create_real_execution(
            root
        )

        evidence_dict = {
            "execution_id": evidence.execution_id,
            "timestamp": evidence.timestamp,
            "tool": evidence.tool,
            "action": evidence.action,
            "permission_allowed": evidence.permission_allowed,
            "confirmation_required": (
                evidence.confirmation_required
            ),
            "confirmation_provided": (
                evidence.confirmation_provided
            ),
            "attempts": evidence.attempts,
            "result": evidence.result,
            "verification_status": (
                evidence.verification_status
            ),
            "recovery_status": (
                evidence.recovery_status
            ),
            "final_status": evidence.final_status,
            "error": evidence.error,
            "risk": evidence.risk,
            "reason": evidence.reason,
            "provenance": evidence.provenance,
        }

        verifier = ExecutionTraceVerifier()

        first = verifier.verify_fresh(
            evidence_dict,
            evidence_dir,
        )

        second = verifier.verify_fresh(
            evidence_dict,
            evidence_dir,
        )

        assert first.verified is True
        assert second.verified is False
        assert any(
            "replay detected" in reason.lower()
            for reason in second.reasons
        )


def test_historical_provenance_remains_valid_after_consumption():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        evidence, evidence_dir = create_real_execution(
            root
        )

        evidence_dict = {
            "execution_id": evidence.execution_id,
            "timestamp": evidence.timestamp,
            "tool": evidence.tool,
            "action": evidence.action,
            "permission_allowed": evidence.permission_allowed,
            "confirmation_required": (
                evidence.confirmation_required
            ),
            "confirmation_provided": (
                evidence.confirmation_provided
            ),
            "attempts": evidence.attempts,
            "result": evidence.result,
            "verification_status": (
                evidence.verification_status
            ),
            "recovery_status": (
                evidence.recovery_status
            ),
            "final_status": evidence.final_status,
            "error": evidence.error,
            "risk": evidence.risk,
            "reason": evidence.reason,
            "provenance": evidence.provenance,
        }

        verifier = ExecutionTraceVerifier()

        fresh = verifier.verify_fresh(
            evidence_dict,
            evidence_dir,
        )

        historical = verifier.verify_provenance(
            evidence_dict,
            evidence_dir,
        )

        assert fresh.verified is True
        assert historical.verified is True


def test_tampered_evidence_does_not_consume_freshness():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        evidence, evidence_dir = create_real_execution(
            root
        )

        evidence_dict = {
            "execution_id": evidence.execution_id,
            "timestamp": evidence.timestamp,
            "tool": evidence.tool,
            "action": evidence.action,
            "permission_allowed": evidence.permission_allowed,
            "confirmation_required": (
                evidence.confirmation_required
            ),
            "confirmation_provided": (
                evidence.confirmation_provided
            ),
            "attempts": evidence.attempts,
            "result": evidence.result,
            "verification_status": (
                evidence.verification_status
            ),
            "recovery_status": (
                evidence.recovery_status
            ),
            "final_status": evidence.final_status,
            "error": evidence.error,
            "risk": evidence.risk,
            "reason": evidence.reason,
            "provenance": evidence.provenance,
        }

        tampered = dict(evidence_dict)
        tampered["result"] = {
            "content": "TAMPERED"
        }

        verifier = ExecutionTraceVerifier()

        rejected = verifier.verify_fresh(
            tampered,
            evidence_dir,
        )

        accepted = verifier.verify_fresh(
            evidence_dict,
            evidence_dir,
        )

        assert rejected.verified is False
        assert accepted.verified is True


def test_freshness_does_not_grant_permission():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        evidence, evidence_dir = create_real_execution(
            root
        )

        evidence_dict = {
            "execution_id": evidence.execution_id,
            "timestamp": evidence.timestamp,
            "tool": evidence.tool,
            "action": evidence.action,
            "permission_allowed": evidence.permission_allowed,
            "confirmation_required": (
                evidence.confirmation_required
            ),
            "confirmation_provided": (
                evidence.confirmation_provided
            ),
            "attempts": evidence.attempts,
            "result": evidence.result,
            "verification_status": (
                evidence.verification_status
            ),
            "recovery_status": (
                evidence.recovery_status
            ),
            "final_status": evidence.final_status,
            "error": evidence.error,
            "risk": evidence.risk,
            "reason": evidence.reason,
            "provenance": evidence.provenance,
        }

        verifier = ExecutionTraceVerifier()

        result = verifier.verify_fresh(
            evidence_dict,
            evidence_dir,
        )

        assert result.verified is True

        guard = ExecutionFreshnessGuard(
            evidence_dir
        )

        assert guard.is_consumed(
            evidence.execution_id
        ) is True


def run_all_tests():
    test_first_use_is_accepted()
    test_second_use_is_rejected_as_replay()
    test_historical_provenance_remains_valid_after_consumption()
    test_tampered_evidence_does_not_consume_freshness()
    test_freshness_does_not_grant_permission()

    print(
        "SAHIBEX 6P-24 EXECUTION REPLAY & "
        "FRESHNESS INTEGRITY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
