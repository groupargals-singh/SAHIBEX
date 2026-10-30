"""P2 acceptance: real MainBrain request executes a harmless registered tool."""
from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from core.brain.master_brain import MasterBrain
from core.brain.sahibex_execution_loop import SahibexExecutionLoop
from security.audit.execution_evidence import ExecutionEvidenceRecorder
from security.audit.execution_trace import ExecutionTraceVerifier

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    started = time.monotonic()
    report = {
        "task": "P2-real-task-execution",
        "scenario": "user asks MainBrain to read an existing source file",
        "request": "Read file core/brain/master_brain.py",
        "side_effect_scope": "read-only source file; audit stored in temporary directory",
        "checks": {},
    }
    with tempfile.TemporaryDirectory(prefix="sahibex_p2_execution_") as directory:
        recorder = ExecutionEvidenceRecorder(Path(directory) / "audit")
        loop = SahibexExecutionLoop(
            brain=MasterBrain(),
            project_root=ROOT,
            evidence_recorder=recorder,
        )
        result = loop.process(report["request"])
        evidence = recorder.read_recent()
        audit_verified = bool(evidence) and all(
            ExecutionTraceVerifier().verify_provenance(item, recorder.log_directory).verified
            for item in evidence
        )
        report["result"] = {
            "success": result.success,
            "status": result.status,
            "intent": result.brain.intent,
            "action": result.brain.action,
            "plan_created": result.brain.plan_created,
            "goal_id_present": bool(result.brain.goal_id),
            "tool_name": result.tool.tool if result.tool else None,
            "tool_success": result.tool.success if result.tool else False,
            "tool_allowed": result.tool.allowed if result.tool else False,
            "verified": result.metadata.get("verified"),
            "audit_recorded": result.metadata.get("audit_recorded"),
            "observation_count": result.observation_count,
            "response_excerpt": result.response[:180],
        }
        checks = report["checks"]
        checks["request_planned"] = bool(result.brain.plan_created and result.brain.goal_id)
        checks["registered_read_tool_executed"] = bool(
            result.tool and result.tool.tool == "read_file" and result.tool.success and result.tool.allowed
        )
        checks["actual_content_returned"] = "master_brain.py" in result.response
        checks["post_execution_verification"] = result.metadata.get("verified") is True
        checks["authenticated_audit_recorded"] = result.metadata.get("audit_recorded") is True
        checks["audit_provenance_valid"] = audit_verified
        checks["observed_and_completed"] = result.status == "COMPLETED" and result.observation_count >= 1
        checks["no_protected_action_or_permission_escalation"] = not loop.recovery.grants_permission()
        report["audit_record_count"] = len(evidence)
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        report["failed_checks"] = [name for name, passed in checks.items() if not passed]
        report["status"] = "PASS" if not report["failed_checks"] else "FAIL"
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
