from pathlib import Path
import json

registry = Path("docs/ROADMAP/SAHIBEX_PHASE_GATE_REGISTRY_2026-10-21.md")
lines = registry.read_text().splitlines()
new = """| P3 Persistence | PASS (bounded persistence/recovery acceptance, 2026-10-22; production DB never modified) | `logs/p3_acceptance_final_attempt_20261021.log`; `logs/p3_pre_reboot_backup_20261021.json`; `logs/p3_post_restart_recovery_20261021.json`; `logs/p3_live_post_restart_quick_check_20261022.log` (quick_check=ok); `logs/p3_live_post_restart_memory_readback_20261022.log` (10,592 memories, sample JSON/timestamps parsed); `logs/p3_staging_restore_drill_20261022.json` (isolated staging restore, 26 tables, integrity ok, real MasterBrain get_memory hash match); `logs/p3_targeted_final_after_staging_restore_20261022.log` (18 passed); compileall and diff check PASS | persistence/backup/restore implementation changes or new acceptance requirements | Defined bounded gate closed. No live production restore/write or destructive production drill was performed; overall release readiness depends on other open gates. |"""
for i, line in enumerate(lines):
    if line.startswith("| P3 Persistence |"):
        lines[i] = new
        break
else:
    raise SystemExit("P3 registry row not found")
registry.write_text("\n".join(lines) + "\n")

master = Path("docs/ROADMAP/MASTER_REMAINING_WORK_LIST_2026-10-10.md")
s = master.read_text()
old = "- [ ] Complete P3 physical power-loss/maintenance-window restore; P6 physical voice round-trip; P7 OCR/vision; **P8 physical device acceptance** (install, enable service, UI tree/tap/type/screenshot, stop/restart); P10 original-source recovery or user-approved reconstructed baseline."
replacement = "- [x] P3 bounded persistence/recovery gate closed on 2026-10-22: phone restart followed by live read-only DB quick_check=ok, 10,592 memory count and sample JSON/timestamp read-back; verified backup restored to isolated staging with 26-table integrity checks and real MasterBrain get_memory hash match; 18 focused tests passed. Evidence: logs/p3_staging_restore_drill_20261022.json and logs/p3_targeted_final_after_staging_restore_20261022.log. No production restore/write was performed.\n- [ ] Remaining physical/specification gates: P6 physical voice round-trip; P7 OCR/vision; **P8 physical device acceptance** (install, enable service, UI tree/tap/type/screenshot, stop/restart); P10 original-source recovery or user-approved reconstructed baseline."
if old in s:
    s = s.replace(old, replacement)
elif "P3 bounded persistence/recovery gate closed on 2026-10-22" not in s:
    raise SystemExit("Master checklist target not found; refusing update")
s += """
\n\n## P3 closure update — 2026-10-22
P3 is PASS for its defined bounded persistence/recovery scope. The verified pre-restart backup hash matched; after the user-performed phone restart, model and bridge health passed, live read-only SQLite quick_check returned ok, live memories count was 10,592, and a sample memory JSON/timestamp parsed. A separate staging restore from that verified backup passed quick/integrity checks across 26 tables and real MasterBrain get_memory content-hash read-back. The focused P3 regression set passed 18 tests; compileall and git diff --check passed. Production DB was not modified and no live service restart/restore was performed. Overall SAHIBEX remains NOT LIVE-READY because P6/P7/P8/P10 remain open.
"""
master.write_text(s)

report = {
 "status": "PASS",
 "gate": "P3 Persistence",
 "scope": "defined bounded persistence, backup/restore and recovery acceptance",
 "date": "2026-10-22",
 "production_db_modified": False,
 "production_service_restarted_by_test": False,
 "checks": {
  "pre_restart_backup_sha256_verified": "69a2fe74d58ae2db1735e6dd7497cea89d17e9fc67cf35a8e47d3c5955f84db6",
  "physical_phone_restart_completed_by_user": True,
  "post_restart_model_health": "PASS",
  "post_restart_media_bridge_health": "PASS",
  "live_readonly_sqlite_quick_check": "ok",
  "live_memories_count": 10592,
  "live_sample_memory_json_and_timestamps": "PASS",
  "isolated_staging_restore": "PASS",
  "staging_table_count": 26,
  "staging_quick_check": "ok",
  "staging_integrity_check": "ok",
  "real_masterbrain_get_memory_hash_match": "PASS",
  "focused_regression": "18 passed",
  "compileall": "PASS",
  "git_diff_check": "PASS"
 },
 "evidence": [
  "logs/p3_post_restart_recovery_20261021.json",
  "logs/p3_live_post_restart_quick_check_20261022.log",
  "logs/p3_live_post_restart_memory_readback_20261022.log",
  "logs/p3_staging_restore_drill_20261022.json",
  "logs/p3_targeted_final_after_staging_restore_20261022.log"
 ],
 "limitations": [
  "No production database restore or write was performed; staging restore was isolated and application-read-back verified.",
  "PASS is limited to P3 defined scope and does not imply overall SAHIBEX release readiness."
 ]
}
Path("logs/p3_final_acceptance_20261022.json").write_text(json.dumps(report, indent=2) + "\n")
print("P3 registry, master remaining-work list, and final acceptance report updated")
