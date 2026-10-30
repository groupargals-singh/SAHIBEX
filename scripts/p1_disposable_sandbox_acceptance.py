from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from uuid import uuid4

from core.policies.approval import ActionType, PermissionEngine
from security.audit.execution_evidence import ExecutionEvidenceRecorder
from security.audit.execution_trace import ExecutionTraceVerifier
from tools.executor import SafeToolExecutor
from tools.permission_gateway import ToolPermissionGateway
from tools.registry import ToolRegistry


def digest(value) -> dict:
    raw = json.dumps(value, sort_keys=True, default=str).encode("utf-8")
    return {"type": type(value).__name__, "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sahibex_p1_disposable_") as tmp:
        sandbox_root = Path(tmp).resolve()
        target = (sandbox_root / "ONLY_DISPOSABLE_TEST_FILE.txt").resolve()
        assert target.parent == sandbox_root and not target.exists()
        expected = b"SAHIBEX P1 disposable sandbox acceptance\nbytes=17\n"
        handler_calls = []

        def guarded_target(path: str | None = None) -> Path:
            if path is None or Path(path).resolve() != target:
                raise PermissionError("Test tool accepts only the one disposable test file.")
            if target.parent != sandbox_root:
                raise PermissionError("Sandbox escape blocked.")
            return target

        def write_handler(path=None, content=None, _permission_granted=False, _confirmation_provided=False):
            if _permission_granted is not True or _confirmation_provided is not True:
                raise PermissionError("Protected write requires gateway approval and explicit confirmation.")
            destination = guarded_target(path)
            if not isinstance(content, bytes):
                raise TypeError("Test payload must be bytes.")
            handler_calls.append("write")
            destination.write_bytes(content)
            return {"path": str(destination), "bytes_written": len(content), "sha256": hashlib.sha256(content).hexdigest()}

        def read_handler(path=None):
            source = guarded_target(path)
            if not source.is_file():
                raise FileNotFoundError("Disposable file not present.")
            handler_calls.append("read")
            data = source.read_bytes()
            return {"path": str(source), "content_hex": data.hex(), "bytes_read": len(data), "sha256": hashlib.sha256(data).hexdigest()}

        def delete_handler(path=None, _permission_granted=False, _confirmation_provided=False):
            if _permission_granted is not True or _confirmation_provided is not True:
                raise PermissionError("Protected delete requires gateway approval and explicit confirmation.")
            destination = guarded_target(path)
            if not destination.is_file():
                raise FileNotFoundError("Disposable file not present.")
            handler_calls.append("delete")
            destination.unlink()
            return {"path": str(destination), "deleted": not destination.exists()}

        registry = ToolRegistry()
        registry.register(name="p1_disposable_write", description="Write only the disposable test file", handler=write_handler, read_only=False, requires_confirmation=True, protected_action=ActionType.WRITE_FILE)
        registry.register(name="p1_disposable_read", description="Read only the disposable test file", handler=read_handler, read_only=True, requires_confirmation=False)
        registry.register(name="p1_disposable_delete", description="Delete only the disposable test file", handler=delete_handler, read_only=False, requires_confirmation=True, protected_action=ActionType.DELETE_FILE)
        permission_engine = PermissionEngine()
        gateway = ToolPermissionGateway(permission_engine, registry)
        executor = SafeToolExecutor(registry, permission_gateway=gateway)
        audit_dir = sandbox_root / "audit"
        recorder = ExecutionEvidenceRecorder(audit_dir)
        trace_verifier = ExecutionTraceVerifier()
        audit_results = []

        # Negative control: write without approval must not invoke the handler.
        denied = gateway.check("p1_disposable_write", confirmation=False)
        assert not denied.allowed and denied.requires_confirmation
        assert not target.exists() and handler_calls == []
        denied_evidence = recorder.record_authenticated(
            execution_id=str(uuid4()), tool="p1_disposable_write", action="sandbox_write",
            permission_allowed=False, confirmation_required=True, confirmation_provided=False,
            attempts=1, result=None, verification_status="NOT_EXECUTED", recovery_status="BLOCKED",
            final_status="BLOCKED", error="No explicit confirmation supplied.", risk=denied.risk,
            reason="Negative control: protected write denied before handler execution.",
        )
        audit_results.append({"step": "write_without_approval", "allowed": denied.allowed, "file_exists": target.exists(), "handler_calls": list(handler_calls)})

        # Approved write: explicit confirmation is supplied to the canonical gateway/executor.
        write_permission = gateway.check("p1_disposable_write", confirmation=True)
        assert write_permission.allowed
        write_result = executor.execute("p1_disposable_write", path=str(target), content=expected, _confirmation_provided=True)
        assert write_result.success, write_result.error
        assert target.is_file() and target.read_bytes() == expected
        write_record = recorder.record_authenticated(
            execution_id=str(uuid4()), tool="p1_disposable_write", action="sandbox_write",
            permission_allowed=True, confirmation_required=True, confirmation_provided=True,
            attempts=1, result=digest(write_result.result), verification_status="VERIFIED", recovery_status="SUCCESS",
            final_status="SUCCESS", error=None, risk=write_permission.risk,
            reason="Explicitly approved disposable-file write; bytes and SHA-256 independently checked.",
        )
        audit_results.append({"step": "approved_write", "bytes_on_disk": len(target.read_bytes()), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "matches_expected": target.read_bytes() == expected})

        # Read back through a registered read-only tool and compare exact bytes.
        read_result = executor.execute("p1_disposable_read", path=str(target))
        assert read_result.success, read_result.error
        read_back = bytes.fromhex(read_result.result["content_hex"])
        assert read_back == expected and read_result.result["bytes_read"] == len(expected)
        read_record = recorder.record_authenticated(
            execution_id=str(uuid4()), tool="p1_disposable_read", action="sandbox_read",
            permission_allowed=True, confirmation_required=False, confirmation_provided=False,
            attempts=1, result=digest(read_result.result), verification_status="VERIFIED", recovery_status="SUCCESS",
            final_status="SUCCESS", error=None, risk="low",
            reason="Read-only roundtrip verified exact bytes and SHA-256.",
        )
        audit_results.append({"step": "read_back", "bytes_read": len(read_back), "exact_match": read_back == expected, "sha256": hashlib.sha256(read_back).hexdigest()})

        # Delete requires its own explicit confirmation and gateway decision.
        delete_denied = gateway.check("p1_disposable_delete", confirmation=False)
        assert not delete_denied.allowed and delete_denied.requires_confirmation and target.exists()
        delete_permission = gateway.check("p1_disposable_delete", confirmation=True)
        assert delete_permission.allowed
        delete_result = executor.execute("p1_disposable_delete", path=str(target), _confirmation_provided=True)
        assert delete_result.success, delete_result.error
        assert not target.exists()
        delete_record = recorder.record_authenticated(
            execution_id=str(uuid4()), tool="p1_disposable_delete", action="sandbox_delete",
            permission_allowed=True, confirmation_required=True, confirmation_provided=True,
            attempts=1, result=digest(delete_result.result), verification_status="VERIFIED", recovery_status="SUCCESS",
            final_status="SUCCESS", error=None, risk=delete_permission.risk,
            reason="Explicitly approved disposable-file delete; absence independently checked.",
        )
        audit_results.append({"step": "approved_delete", "file_exists_after": target.exists(), "handler_calls": list(handler_calls)})

        # Verify every persisted audit record's consistency and authenticated provenance.
        records = recorder.read_recent(limit=20)
        assert len(records) == 4, f"Expected 4 audit records, got {len(records)}"
        for record in records:
            trace = trace_verifier.verify_provenance(record, audit_dir)
            assert trace.verified, (record.get("tool"), trace.reasons)
        assert records[0]["final_status"] == "BLOCKED" and records[0]["permission_allowed"] is False
        assert records[1]["final_status"] == "SUCCESS" and records[1]["confirmation_provided"] is True
        assert records[2]["final_status"] == "SUCCESS" and records[2]["verification_status"] == "VERIFIED"
        assert records[3]["final_status"] == "SUCCESS" and records[3]["confirmation_provided"] is True
        assert not target.exists()

        print(json.dumps({
            "result": "PASS",
            "sandbox": "temporary directory; automatically removed after test",
            "test_file_only": target.name,
            "expected_bytes": len(expected),
            "negative_write_blocked_without_handler": True,
            "approved_write_exact_bytes_verified": True,
            "read_back_exact_bytes_verified": True,
            "delete_only_after_explicit_confirmation": True,
            "file_absent_after_delete": True,
            "authenticated_audit_records": len(records),
            "provenance_verified_records": len(records),
            "steps": audit_results,
            "handler_calls": handler_calls,
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
