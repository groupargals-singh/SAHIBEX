from __future__ import annotations

import json
import tempfile
from pathlib import Path

from security.audit.audit_logger import AuditLogger


def test_real_audit_logger_accepts_execution_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        logger = AuditLogger(Path(tmp))

        event = logger.record(
            request="read test file",
            intent="read",
            intent_confidence=0.95,
            action="read_file",
            action_confidence=0.95,
            risk="low",
            permission_allowed=True,
            confirmation_required=False,
            reason="6P-19 identity binding test.",
            execution_id="execution-A",
        )

        assert event["execution_id"] == "execution-A"


def test_real_audit_record_persists_execution_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        logger = AuditLogger(Path(tmp))

        logger.record(
            request="read test file",
            intent="read",
            intent_confidence=0.95,
            action="read_file",
            action_confidence=0.95,
            risk="low",
            permission_allowed=True,
            confirmation_required=False,
            reason="6P-19 persistence test.",
            execution_id="execution-A",
        )

        lines = logger.log_file.read_text(
            encoding="utf-8"
        ).splitlines()

        assert len(lines) == 1

        event = json.loads(lines[0])

        assert event["execution_id"] == "execution-A"


def test_audit_execution_identity_is_not_mutable_by_readback() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        logger = AuditLogger(Path(tmp))

        event = logger.record(
            request="read test file",
            intent="read",
            intent_confidence=0.95,
            action="read_file",
            action_confidence=0.95,
            risk="low",
            permission_allowed=True,
            confirmation_required=False,
            reason="6P-19 immutability test.",
            execution_id="execution-A",
        )

        assert event["execution_id"] == "execution-A"

        recent = logger.read_recent(limit=1)

        assert len(recent) == 1
        assert recent[0]["execution_id"] == "execution-A"


def test_different_execution_ids_remain_distinct() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        logger = AuditLogger(Path(tmp))

        logger.record(
            request="first execution",
            intent="read",
            intent_confidence=0.95,
            action="read_file",
            action_confidence=0.95,
            risk="low",
            permission_allowed=True,
            confirmation_required=False,
            reason="First execution.",
            execution_id="execution-A",
        )

        logger.record(
            request="second execution",
            intent="read",
            intent_confidence=0.95,
            action="read_file",
            action_confidence=0.95,
            risk="low",
            permission_allowed=True,
            confirmation_required=False,
            reason="Second execution.",
            execution_id="execution-B",
        )

        recent = logger.read_recent(limit=2)

        ids = {
            event["execution_id"]
            for event in recent
        }

        assert ids == {
            "execution-A",
            "execution-B",
        }


def test_audit_identity_cannot_be_empty() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        logger = AuditLogger(Path(tmp))

        try:
            logger.record(
                request="invalid execution",
                intent="read",
                intent_confidence=0.95,
                action="read_file",
                action_confidence=0.95,
                risk="low",
                permission_allowed=True,
                confirmation_required=False,
                reason="Empty identity test.",
                execution_id="",
            )
        except ValueError:
            return

        raise AssertionError(
            "AuditLogger must reject an empty execution_id."
        )


def run_all_tests() -> None:
    test_real_audit_logger_accepts_execution_identity()
    test_real_audit_record_persists_execution_identity()
    test_audit_execution_identity_is_not_mutable_by_readback()
    test_different_execution_ids_remain_distinct()
    test_audit_identity_cannot_be_empty()


if __name__ == "__main__":
    run_all_tests()

    print(
        "SAHIBEX 6P-19 REAL AUDIT IDENTITY BINDING TEST: PASS"
    )
