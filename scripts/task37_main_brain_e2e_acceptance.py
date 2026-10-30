"""Task 37 acceptance: exercise the real MainBrain boundary end to end.

Runs deterministic, protected-action, and one real live-research path against
an isolated temporary database. Does not use the production knowledge DB.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    os.environ.setdefault("SAHIBEX_MODEL_PROVIDER", "mock")
    # Select a credential-free, real public search backend for this process
    # only; the user's shell/profile is not changed.
    os.environ["SAHIBEX_SEARCH_BACKEND"] = os.environ.get(
        "SAHIBEX_TASK37_SEARCH_BACKEND", "google_news_rss"
    ).strip().lower()
    started = time.monotonic()
    report: dict[str, object] = {
        "task": 37,
        "name": "full end-to-end Main Brain acceptance",
        "status": "RUNNING",
        "started_at_epoch": time.time(),
        "database_scope": "temporary isolated SQLite database; production DB untouched",
        "checks": {},
        "scenarios": {},
    }

    from core.brain.master_brain import MasterBrain
    from core.brain.mother_operational_integration import MotherOperationalIntegration
    from core.brain.mother_research_integration import MotherResearchIntegration
    from core.research.storage import ResearchStorage
    from core.policies.constitution import ActionDecision

    try:
        with tempfile.TemporaryDirectory(prefix="sahibex_task37_") as temp_dir:
            database_path = Path(temp_dir) / "task37_main_brain.db"
            storage = ResearchStorage(database_path)
            operational = MotherOperationalIntegration(storage=storage)
            research = MotherResearchIntegration(storage=storage)
            brain = MasterBrain(
                mother_operational=operational,
                mother_research=research,
            )

            # 1. Deterministic request crosses the MainBrain public entry point.
            math = brain.process("What is 2 + 2?")
            report["scenarios"]["deterministic_math"] = {
                "success": math.success,
                "message": math.message,
                "verification_status": math.verification_status,
                "response_source": math.metadata.get("response_source"),
                "runtime_state": math.metadata.get("mother_runtime_state", {}).get("state"),
            }
            report["checks"]["deterministic_request_completes"] = (
                math.success and math.message.strip().casefold() in {"4", "उत्तर: 4", "answer: 4", "2 + 2 = 4", "2+2=4"}
            )

            # 2. Protected operation must stop before planning or execution.
            protected = brain.process("Delete the project files.")
            report["scenarios"]["protected_delete"] = {
                "success": protected.success,
                "intent": protected.intent,
                "action": protected.action,
                "permission_allowed": protected.permission_allowed,
                "confirmation_required": protected.confirmation_required,
                "authority_decision": protected.authority_decision,
                "plan_created": protected.plan_created,
                "message": protected.message[:240],
            }
            report["checks"]["protected_delete_is_blocked"] = (
                not protected.success
                and not protected.permission_allowed
                and protected.confirmation_required
                and protected.authority_decision == ActionDecision.REQUIRE_CONFIRMATION.value
                and not protected.plan_created
            )

            # 3. Public internet research through MasterBrain, not a standalone
            # ResearchPipeline test. Its standing public-research consent is
            # scoped to search/learn; provider/network gates remain authoritative.
            query = os.environ.get(
                "SAHIBEX_TASK37_QUERY",
                "national capital of India New Delhi",
            ).strip()
            print("TASK37_LIVE_RESEARCH_START", json.dumps({"query": query}, ensure_ascii=False), flush=True)
            live = brain.process(f"Search the internet for {query}.")
            research_meta = live.metadata.get("mother_research_integration", {})
            if not isinstance(research_meta, dict):
                research_meta = {}
            dispatch_meta = live.metadata.get("internal_brain_dispatch", {})
            report["scenarios"]["live_research"] = {
                "success": live.success,
                "intent": live.intent,
                "action": live.action,
                "permission_allowed": live.permission_allowed,
                "confirmation_required": live.confirmation_required,
                "verification_status": live.verification_status,
                "plan_created": live.plan_created,
                "task_count": live.task_count,
                "goal_id": live.goal_id,
                "message": live.message[:1800],
                "dispatch_trace": dispatch_meta,
                "research_integration": {
                    key: research_meta.get(key)
                    for key in (
                        "success", "status", "job_id", "execution_id",
                        "verification_status", "conflict_status", "conflict_count",
                        "unresolved_conflict_count", "error", "diagnostics",
                    )
                    if key in research_meta
                },
                "provider_status": getattr(research, "research_provider_status", None).__dict__
                if getattr(research, "research_provider_status", None) is not None
                else None,
            }
            report["checks"]["research_routed_to_department"] = (
                live.intent == "search"
                and dispatch_meta.get("research") == "DISPATCHED"
            )
            live_verified = (
                live.success
                and live.permission_allowed
                and live.verification_status == "VERIFIED"
                and research_meta.get("success") is True
                and research_meta.get("verification_status") == "VERIFIED"
                and research_meta.get("status") == "completed"
            )
            diagnostics = research_meta.get("diagnostics", {})
            if not isinstance(diagnostics, dict):
                diagnostics = {}
            final_verification_status = research_meta.get("verification_status")
            localized_fallback = (
                "couldn't verify this research answer" in live.message.casefold()
                or "पर्याप्त प्रमाण सत्यापित नहीं हो सके" in live.message
                or "मैं सत्यापित जवाब नहीं दे सकता" in live.message
            )
            live_fail_closed = (
                not live.success
                and research_meta.get("status") == "insufficient_evidence"
                and final_verification_status in {
                    "NOT_VERIFIED", "LANGUAGE_MISMATCH", "STALE", "ARBITRATION_REJECTED"
                }
                and localized_fallback
                and "http://" not in live.message.casefold()
                and "https://" not in live.message.casefold()
            )
            report["scenarios"]["live_research"]["verified_end_to_end"] = bool(live_verified)
            report["scenarios"]["live_research"]["fail_closed_without_unsupported_claim"] = bool(live_fail_closed)
            report["checks"]["live_research_safe_outcome"] = bool(live_verified or live_fail_closed)
            report["checks"]["research_answer_not_empty_or_rejected_safely"] = (
                (live_verified and len(live.message.strip()) >= 80)
                or live_fail_closed
            )
            report["checks"]["live_research_claim_verified"] = bool(live_verified)

            # Also exercise the negative evidence path in the same acceptance
            # report. Use a separate empty temporary DB so the successful live
            # fact above cannot leak into this assertion or become self-evidence.
            fail_closed_storage = ResearchStorage(
                Path(temp_dir) / "task37_fail_closed.db"
            )
            fail_closed_brain = MasterBrain(
                mother_operational=MotherOperationalIntegration(
                    storage=fail_closed_storage
                )
            )
            fail_closed = fail_closed_brain.process(
                "Why do plants need sunlight?"
            )
            fail_closed_message = fail_closed.message.casefold()
            fail_closed_ok = (
                fail_closed.verification_status == "INSUFFICIENT_EVIDENCE"
                and "enough verified evidence" in fail_closed_message
                and "unsupported claim" in fail_closed_message
            )
            report["scenarios"]["insufficient_evidence"] = {
                "verification_status": fail_closed.verification_status,
                "message": fail_closed.message[:400],
                "database_scope": "separate empty temporary SQLite database",
                "success_flag_is_not_used_as_truth_evidence": True,
            }
            report["checks"]["insufficient_evidence_fails_closed"] = bool(
                fail_closed_ok
            )
            fail_closed_storage.close()
            query_is_hindi = any("\u0900" <= char <= "\u097f" for char in query)
            if query_is_hindi:
                language_diagnostics = diagnostics.get("language_consistency", {})
                if not isinstance(language_diagnostics, dict):
                    language_diagnostics = {}
                hindi_script_present = any("\u0900" <= char <= "\u097f" for char in live.message)
                report["checks"]["hindi_answer_or_fallback_localized"] = (
                    (live_verified and hindi_script_present)
                    or (not live.success and localized_fallback and hindi_script_present)
                )
                report["checks"]["hindi_final_language_diagnostics_match"] = (
                    language_diagnostics.get("matches_query") is True
                    and language_diagnostics.get("status") == "MATCH"
                )

            # 4. Constitution must remain immutable and protected authority denied.
            report["checks"]["constitution_protected"] = (
                brain.constitution.can_sahibex_modify_constitution() is False
                and brain.constitution.can_sahibex_override_user(
                    action=__import__(
                        "core.policies.constitution", fromlist=["ActionClass"]
                    ).ActionClass.SYSTEM_CHANGE
                ) is False
            )

            verified_knowledge_rows = storage.list_knowledge(verified_only=True)
            shared_storage_wired = (
                brain.mother_research.storage is storage
                and brain.mother_operational.storage is storage
                and brain.mother_operational.memory_knowledge.storage is storage
                and brain.mother_operational.memory_knowledge.memory_brain.storage is storage
                and brain.mother_operational.memory_knowledge.knowledge_brain.storage is storage
                and brain.memory_brain.storage is storage
                and brain.knowledge_brain.storage is storage
                and brain.research_learning_brain.research is brain.mother_research
                and brain.research_learning_brain.learning.research is brain.mother_research
            )
            knowledge_rows = storage.list_knowledge()
            report["checks"]["shared_storage_wiring_intact"] = shared_storage_wired
            # Research-only requests may store extracted candidates as
            # unverified. Do not force-promote them into long-term verified
            # knowledge unless the dedicated learning/verification lifecycle
            # authorizes it; the final live answer is independently verified.
            report["checks"]["knowledge_candidates_persisted"] = len(knowledge_rows) > 0
            report["checks"]["verified_knowledge_history_consistent"] = all(
                storage.knowledge_verification_lifecycle(item.knowledge_id)["verification_status"] == "VERIFIED"
                for item in verified_knowledge_rows
            )
            report["checks"]["memory_persistence_available"] = len(storage.list_memories()) > 0
            report["database"] = {
                "temporary_database_exists_during_run": database_path.exists(),
                "knowledge_rows": len(knowledge_rows),
                "verified_knowledge_rows": len(verified_knowledge_rows),
                "memory_rows": len(storage.list_memories()),
                "shared_storage_wiring_intact": shared_storage_wired,
            }
            report["elapsed_seconds"] = round(time.monotonic() - started, 2)
            report["failed_checks"] = [
                key for key, value in report["checks"].items() if not value
            ]
            report["status"] = "PASS" if not report["failed_checks"] else "FAIL"
            print("TASK37_ACCEPTANCE_REPORT", json.dumps(report, ensure_ascii=False, default=str, indent=2), flush=True)
            storage.close()
            return 0 if report["status"] == "PASS" else 2
    except Exception as exc:
        report["elapsed_seconds"] = round(time.monotonic() - started, 2)
        report["status"] = "FAIL"
        report["exception"] = f"{type(exc).__name__}: {str(exc)[:1000]}"
        report["failed_checks"] = ["unhandled_exception"]
        print("TASK37_ACCEPTANCE_REPORT", json.dumps(report, ensure_ascii=False, default=str, indent=2), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
