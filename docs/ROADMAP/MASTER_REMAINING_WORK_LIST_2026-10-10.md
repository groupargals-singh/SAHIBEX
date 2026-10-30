# SAHIBEX — Authoritative Live Brain Roadmap & Status
Date: 2026-10-21
Workspace: ~/SAHIBEX
Authoritative gate registry: `docs/ROADMAP/SAHIBEX_PHASE_GATE_REGISTRY_2026-10-21.md` (do not repeat accepted gates unless the registry's reopen condition is met).
Status: ACTIVE — overall Live Brain acceptance is NOT COMPLETE

## 1. The important correction
The 38-item list is the Research/Learning + Main Brain integration verification checklist. Its tests and one live-research acceptance are green, but that does NOT mean the entire SAHIBEX product is live or complete. The prior Task 38 report needs to be read with this scope correction.

Fresh re-verification status on 2026-10-21:
- Full repository regression: **2,015 passed in 186.71s**; focused P-series regression: **44 passed**; `compileall`, shell syntax, and `git diff --check` PASS.
- P1 real MainBrain answer reliability smoke PASS; P2 live network edge matrix PASS; Task 37 MainBrain E2E PASS with `failed_checks: []`. Evidence: `logs/phase_p_series_reverification_20261021.md`.
- P3 safe online backup/restore and disposable abrupt-process recovery PASS; P4 child lifecycle acceptance 11/11 PASS; P5 controlled self-improvement focused recheck 13 PASS.
- Android debug APK build/signature and OCR runtime plumbing have been verified, but physical voice and Accessibility are not re-tested without a connected/authorized device.
- Overall release remains BLOCKED/PENDING on P3 physical restore, P6 physical voice, P7 camera/visual understanding and OCR accuracy, P8 physical-device acceptance, and P10 original specification reconciliation. P9 bounded integrated security/reliability acceptance is now PASS. P4's defined worker/child acceptance is now PASS; separate model backends remain untested as a non-blocking scope limit. P11 release is not PASS.
## 2. Status vocabulary — use every time
- PASS: the exact named test ran now or has a specific saved, relevant acceptance artifact.
- IMPLEMENTED: code exists, but the feature's final integration/live gate may still be pending.
- PENDING: not yet tested to its required acceptance level.
- BLOCKED: an observed condition currently prevents the next acceptance step.
- NEEDS-RECONCILIATION: required specification or mapping is missing.
- COMPLETE: implementation + integration + security/authority checks + dedicated tests + required live/device acceptance all pass.
A unit test PASS never upgrades a hardware feature or the whole product to COMPLETE. Keep historic PASS evidence and current live status separate.

## 3. Fixed 38-item checklist — scope-limited status
The current recorded test/acceptance evidence supports the following checklist statuses. These are not claims of universal production coverage:
1 PASS — Multi-Source Agreement Engine
2 PASS — Multi-Source Verification
3 PASS — Research Core, Evidence & Integration
4 PASS — Hindi Intent Routing
5 PASS — Source / Publisher Identity Verification
6 PASS — Claim-to-Evidence Linking
7 PASS — Contradictory Evidence Detection
8 PASS — Verified-Only Knowledge Retrieval
9 PASS — End-to-End Research Answer Verification (automated paths)
10 PASS — Live Internet Source Acquisition (one accepted live run)
11 PASS — Multiple-Publisher Research (two publishers in the accepted run)
12 PASS — Source Reliability Assessment (test coverage)
13 PASS — Duplicate / Aggregator Source Detection (test coverage)
14 PASS — Evidence Freshness & Timestamps (test coverage / accepted run metadata)
15 PASS — Conflicting Reports Comparison (test coverage)
16 PASS — Answer Source Traceability (one accepted answer + tests)
17 PASS — Reading Pipeline Verification (test coverage)
18 PASS — Research Findings-to-Knowledge Linking (test coverage)
19 PASS — Evidence-Based Learning (test coverage)
20 PASS — Unsupported Knowledge Rejection (test coverage)
21 PASS — Learning History & Persistence (isolated-database tests)
22 PASS — Research / Reading Verification & Filtering (test coverage)
23 PASS — Brain-module connection checks (integration-test scope)
24 PASS — Data-flow audit (repository/test evidence; full product acceptance still pending)
25 PASS — Intent-to-research routing (MainBrain E2E)
26 PASS — Memory/knowledge wiring (isolated-database E2E)
27 PASS — Verification/conflict integration (test evidence)
28 PASS — Worker/department coordination (test evidence)
29 PASS — Permission/security boundary tests (test evidence; current live adversarial gate pending)
30 PASS — Integration bug-fix regression (test evidence)
31 PASS — Main Brain architecture integration acceptance (code-level)
32 PASS — Targeted regression suite
33 PASS — Research integration suite
34 PASS — Persistence/restart tests in isolated DB
35 PASS — Failure/recovery tests with injected failures
36 PASS — Bounded real-source acceptance (English current news, Hindi current news with explicit translation opt-in, stable fact, and HTTP edge cases)
37 PASS — Full MainBrain E2E acceptance (English and Hindi verified live-research runs; protected-action boundary; isolated temporary DB)
38 PASS — Final P6 integration/self-improvement acceptance report saved; overall product-release scope remains separate
Scope caveats: Task 36/37 prove bounded query/path coverage, not all topics. P2 passed live research cases and four live HTTP acquisition edge cases; conflict/stale/duplicate/empty-result behavior has regression coverage. Current Task 37 runs use a temporary DB and do not prove automatic promotion into the dedicated verified-knowledge table. P6 final integrated acceptance is now PASS for verified English/Hindi live research and metadata-only controlled self-improvement with persistent audit, approval, activation, rollback and failed-update recovery. Executable-code self-update, persistent skill-version restore across process restart, physical-device voice/vision/Accessibility and broader product-release gates remain separate.

## 4. The actual remaining work — ordered master queue
Do these in order; update this file after each gate. Do not restart the 38-item checklist unless a regression breaks it.

### P0 — Stabilize supervised text runtime (COMPLETE — 2026-10-17)
Status: PASS — supervisor-owned model recovery, single-instance protection, interactive entry point, port-conflict handling, and final health snapshot verified. Evidence: logs/p0_runtime_recovery_full_verification_20261017.md.

- [x] Start the model using the existing startup script and confirm /health.
- [x] Confirm a real local completion works with enable_thinking=false after recovery.
- [x] Start/verify the background supervisor and prove it restarts the model after a controlled stop without duplicate processes.
- [x] Start/verify the actual interactive app.main entry point and confirm it handles multiple requests.
- [x] Confirm model, search, supervisor, and bridge HTTP health independently; save full output.
- [x] Test cold/recovery start, controlled model stop, port conflict, and recovery; save exact logs.
- [x] Full repository regression after script changes: 1,869 passed in 141.76s; compileall PASS; bash -n PASS; git diff --check PASS. Evidence: logs/p0_full_regression_20261017.log and logs/p0_post_regression_final_verification_20261017.log.
Gate result: PASS for supervised text runtime. The physical phone voice round-trip remains a separate P6 gate; bridge HTTP health alone is not voice acceptance.

### P1 — Make the text-first Live Brain MVP reliable (CURRENT CORE BLOCKER)
Status: PASS for the defined P1 acceptance matrix (2026-10-17); broader SAHIBEX release remains NOT LIVE-READY because P2–P11 and physical-device release gates remain.
- [x] Add safe rejected-answer diagnostics (language mismatch vs quality reasons/score) to MainBrain result metadata; no answer body or private memory is added to the diagnostics.
- [x] Do not treat `STRUCTURALLY_VALID` as factual verification. Model-generated responses remain structurally valid/unverified; factual queries require relevant verified knowledge with evidence or return explicit uncertainty/conflict.
- [x] Add fixed Hindi/English factual tests for verified evidence, no evidence, conflicting claims, and quality-rejection diagnostics; assertions check the final verification status and evidence metadata.
- [x] Real MainBrain read-only tool path: user text -> intent/context -> plan -> permission gateway -> selected registered tool -> real result -> independent post-execution verification -> final response -> authenticated audit evidence. Evidence: `tests/unit/test_sahibex_execution_loop.py`, `tests/unit/test_main_brain_execution_audit_gate.py`, `logs/p1_tool_execution_audit_acceptance_20261017.log`.
- [x] Denied protected delete request is stopped before tool execution and produces `BLOCKED` authenticated evidence; the audit record confirms permission denied and no result. Evidence: `tests/unit/test_sahibex_execution_loop.py`.
- [x] Fail-closed controls: a rejected post-execution verifier cannot be bypassed, and audit-storage failure prevents the Main Brain from returning tool success. Evidence: `tests/unit/test_main_brain_execution_audit_gate.py`.
- [x] Disposable sandbox write/read/delete acceptance: bytes verified after write/read, file absence verified after delete, and authenticated intent/result audit traces verified. Evidence: `tests/unit/test_main_brain_execution_audit_gate.py`, `tests/unit/test_tool_brain_runtime.py`.
- [x] Permitted harmless protected write and delete with explicit approval: authenticated `PENDING` intent plus `SUCCESS` result records verified; audit-write failure blocks the side effect. Evidence: `tests/unit/test_main_brain_execution_audit_gate.py`, `tests/unit/test_tool_brain_runtime.py`.
- [x] Limited live-source research acceptance passed through acquisition, publisher fetch, extraction, evidence verification, multi-source traceability, and answer arbitration. Evidence: `logs/p1_task36_live_research_acceptance_20261017.log`, `logs/p1_task37_main_brain_e2e_acceptance_20261017.log`; broader P2 live matrix remains pending.
- [x] Run Hindi and English insufficient-evidence cases through `MasterBrain.process()`; both return `INSUFFICIENT_EVIDENCE` and explicit uncertainty.
- [x] Isolated persistence/restart/recall/provenance acceptance passed; unverified research remains unpromoted in the Task 37 temporary database. Evidence: `tests/unit/test_memory_brain_runtime.py`, `tests/unit/test_task34_persistence_restart_recovery.py`, Task 37 acceptance log.
- [x] Cancellation stops later research stages; bounded retry/timeout classification and tool failure recovery tests pass. Evidence: `tests/unit/test_research_execution_manager.py`, `tests/unit/test_task35_failure_recovery.py`, `tests/unit/test_tool_failure_recovery_runtime.py`.
- [x] Real MainBrain acceptance matrix: Hindi/English insufficient evidence, Hindi/English evidence-backed answers, conflicting verified claims, and safe rejected-answer diagnostics. Evidence: `tests/unit/test_main_brain_answer_reliability.py`, `tests/unit/test_factual_answer_gate.py`, `logs/p1_live_answer_reliability_smoke_20261017.log`.
Gate: every scenario passes through the actual production entry point, with logs/reports and production-like persistent storage where safe.

### P2 — Research reliability across a matrix + complete task execution
Status: PASS — bounded acceptance matrix completed on 2026-10-17. Overall SAHIBEX remains NOT LIVE-READY because later P3–P11 and physical-device release gates remain.
- [x] Live current-news acceptance in English: publisher fetch, multi-domain evidence, dates, claim traceability, arbitration and language consistency passed (32.37s; `failed_checks: []`). Evidence: `logs/p2_matrix_20261017/english_current_news_with_language_gate.json`.
- [x] Hindi live issue was fixed and retested: the final source-backed Hindi query passes with explicit translation opt-in, language gate, traceability, and stage/time/page budgets. Initial failure evidence retained in `logs/p2_matrix_20261017/hindi_current_news_with_language_gate.json`; final PASS: `logs/p2_matrix_20261017/hindi_current_news_final_with_stage_budgets.json`.
- [x] Add a fail-closed language-consistency gate to `MotherResearchIntegration`; a mismatched verified answer is not returned as a successful result. It returns localized insufficient-evidence text with `verification_status=LANGUAGE_MISMATCH` and diagnostics. Evidence: `tests/unit/test_mother_research_answer_integrity.py`.
- [x] Fix numeric conflict persistence compatibility: `KnowledgeConflictRecord` now accepts `NUMERIC_CONTRADICTION`, so conflict assessments can be durably stored rather than forcing `CONFLICT_PERSISTENCE_FAILED`. Evidence: `tests/unit/test_knowledge_conflict_persistence.py`, `logs/p2_numeric_conflict_fix_targeted_20261017.log`.
- [x] Strengthen stable-fact paraphrase linking with a narrow query-conditioned rule requiring shared query terms and named entities, while preserving numeric/negation checks; ignore geographic coordinate tokens as irrelevant numeric metadata. The linker only joins evidence and never marks claims verified. Evidence: `tests/unit/test_research_answer_pipeline.py`, `logs/p2_post_fix_targeted_20261017.log`.
- [x] Prevent query-conditioned claim linking from treating `test_fixture` or `discovery_only` sources as corroborating evidence. A broad regression caught and fixed this boundary; focused acceptance now passes. Evidence: `tests/unit/test_task37_main_brain_end_to_end_acceptance.py`, `logs/p2_final_targeted_20261017.log`.
- [x] Real MainBrain task execution: user request -> intent/context -> plan -> permission gateway -> actual registered read-only tool -> real content -> independent verification -> authenticated audit -> observation/completion. Final evidence: `scripts/p2_task_execution_acceptance.py`, `logs/p2_task_execution_acceptance_final_20261017.json`.
- [x] Focused research/execution regression: 88 passed; language/integration regression: 89 passed; edge-case regression: 72 passed; final focused regression: 63 passed. Evidence: `logs/p2_targeted_precheck_20261017.log`, `logs/p2_language_gate_targeted_20261017.log`, `logs/p2_edge_case_regression_20261017.log`, `logs/p2_final_targeted_20261017.log`.
- [x] Final code regression after P2 fixes: **1,905 passed in 177.26s**; `compileall` PASS; `git diff --check` PASS; real MainBrain task execution acceptance PASS; English/Hindi/stable-fact live-source acceptance PASS. Evidence: `logs/p2_full_regression_final_2_20261017.log`, `logs/p2_task_execution_acceptance_final_20261017.json`, `logs/p2_matrix_20261017/english_current_news_final_with_stage_budgets.json`.
- [x] Live stable-fact acceptance PASS with two publisher domains and accepted arbitration. Evidence: `logs/p2_matrix_20261017/stable_fact_capital_india_final_with_stage_budgets.json`.
- [x] Add an opt-in English-to-Hindi translation adapter; post-translation language/number/URL checks pass and original traceability remains unchanged. Provider configuration is explicit for privacy.
- [x] Bounded live matrix PASS: English current news, Hindi current news with explicit translation opt-in, stable fact, substantive HTML, HTTP 404, short/stub response, and timeout. Conflict/stale/duplicate/empty-result cases pass deterministic integration tests.
- [x] Live acceptance records per-stage timings and checks stage, total-time, and publisher-page budgets. Retry/timeout and empty-result behavior have regression coverage.
- [x] Final repository regression recheck: **1,905 passed in 162.74s** (`logs/p2_full_regression_final_recheck_20261017.log`); compileall and git diff checks PASS (`logs/p2_compileall_final_recheck_20261017.log`, `logs/p2_diff_check_final_recheck_20261017.log`). Do not relax confidence thresholds just to turn tests green.

### P3 — Memory, learning and production persistence
Status: PARTIAL — final safe recheck 2026-10-21: read-only production snapshot and restore/hash comparison across 26 tables PASS; disposable abrupt-process recovery PASS; targeted regression 18 passed; compileall/diff check PASS. Added a real two-process MasterBrain persistence cycle against a temporary data directory: process 1 saved a memory and exited; a fresh process 2 reconstructed MasterBrain and retrieved the exact record and timestamp metadata. Added app-level restore read-back: production DB was opened read-only and backed up into a temporary restore; a fresh MasterBrain loaded that restored copy and successfully read a memory record with matching content SHA-256, metadata, and timestamps; all 10,592 memory rows were retained and SQLite integrity returned `ok`. Evidence: `logs/p3_acceptance_final_attempt_20261021.log`, `logs/p3_targeted_final_attempt_20261021.log`, `logs/p3_masterbrain_disposable_service_cycle_20261021.json`, `logs/p3_application_restore_readback_20261021.json`, `logs/p3_compileall_final_attempt_20261021.log`, `logs/p3_diff_check_final_attempt_20261021.log`. ADB reports no attached devices (`logs/p3_device_access_check_20261021.log`). Pre-reboot safety: verified backup PASS (logs/p3_pre_reboot_backup_20261021.json); reboot not attempted because no ADB device, no root capability, and no Termux:Boot recovery setup (logs/p3_physical_reboot_precheck_20261021.json). Still open: physical Android power-loss drill and authorized staging/production maintenance-window restore with application-level read-back; those require physical device access and an approved maintenance window.
- [x] Use real production storage safely; open the production DB read-only and create an SQLite online snapshot without modifying it. Evidence: `scripts/p3_production_persistence_acceptance.py`, `logs/p3_production_persistence_acceptance_20261021.json`.
- [x] Verify backup restore into a separate temporary location; `quick_check` and `integrity_check` both `ok`; all 26 table row counts and per-table content hashes match. Evidence: `logs/p3_production_persistence_acceptance_20261021.md`.
- [x] Simulate abrupt process exit against a disposable WAL DB: committed row survives, uncommitted row rolls back, reopened DB passes integrity check.
- [x] Production-like copy tests for source/document/finding/evidence provenance, deduplication, restart persistence, and explicit verification promotion. Evidence: `logs/p3_production_like_roundtrip_20261020.json`.
- [x] P3 targeted regression: **35 passed, 0 failed**, exit 0. Evidence: `logs/p3_targeted_regression_20261021.log`.
- [ ] Physical Android power-loss drill on disposable data; ADB check found no attached device; no root capability or Termux boot recovery was available, so reboot was safely not attempted after the verified pre-reboot backup (`logs/p3_device_access_check_20261021.log`). Never run destructive tests on the live DB.
- [x] Disposable MasterBrain two-process restart cycle: process 1 persisted a memory record and exited; process 2 reconstructed MasterBrain and retrieved the record plus timestamp metadata from the same temporary DB. Evidence: `scripts/p3_masterbrain_disposable_service_cycle.py`, `logs/p3_masterbrain_disposable_service_cycle_20261021.json`. This is an isolated application-process restart test, not physical power-loss or a production service outage drill.
- [ ] Physical service/device power-loss drill and broader application-level read-back for conflict/expiry/untrusted-candidate isolation on an approved disposable/staging environment; do not use destructive tests against live DB.
- [x] Temporary-copy application-level restore read-back: a real MasterBrain loaded the restored copy and retrieved a memory record; content hash, metadata and timestamps matched, and SQLite integrity was `ok`. Evidence: `scripts/p3_application_restore_readback.py`, `logs/p3_application_restore_readback_20261021.json`. This does not write to or prove restore of the live DB.
- [ ] Restore into the designated staging/production target during an explicitly authorized maintenance window and perform application-level read-back. Do not touch the live DB or interrupt service without authorization.

### P4 — Commander Brain, worker brains and specialist child
Status: PASS for the defined acceptance scope (2026-10-21). `MasterBrain.run_managed_worker` and configured `dispatch_worker_team` use isolated processes with Mother + human approval, task DB, hard timeout, Emergency Stop and no inline fallback after managed execution errors. Child lifecycle/capability gates and parent performance/load accounting remain active. P4 focused verification after launcher change: **37 passed**, exit 0; `compileall`, `bash -n`, and `git diff --check` PASS. Live local-model dual-worker run VERIFIED both independent answers and completed both ledger tasks (`logs/p4_live_model_worker_acceptance_20261021.log`). Disposable restart-recovery drill correctly marks interrupted work failed (`logs/p4_restart_recovery_drill_20261021.log`). The actual `scripts/start_sahibex_live.sh` launcher now defaults `SAHIBEX_MANAGED_WORKER_DB` to `data/runtime/managed_worker_tasks.sqlite3` while preserving caller overrides; actual app launch and relaunch were observed, and both app processes used the configured path (`logs/p4_live_launcher_restart_acceptance_20261021.log`). Both workers use the same local model endpoint; separate model backends were not tested and are a documented non-blocking scope limit.
- [x] Real MainBrain dual-worker dispatch: distinct Army/Labour handlers, joint result verification, approval gate, and authority boundaries. Evidence: `scripts/p4_child_worker_acceptance.py`, `logs/p4_child_worker_acceptance_live_20261021.log`.
- [x] Persistent child identity and child-scoped memory survive manager restart; restored children are PAUSED + UNVERIFIED and require fresh approval/verification and handler rebinding. Evidence: `logs/p4_child_worker_acceptance_20261021.md`.
- [x] Lifecycle and security checks: registry hash-chain integrity, memory isolation, suspension blocks dispatch, resume requires fresh verification, retirement terminal, child cannot grant authority/override Mother/modify Constitution.
- [x] Focused regression: **29 passed, 0 failed**, exit 0. Evidence: `logs/p4_child_worker_acceptance_20261021.log`.
- [x] Add a bounded process-isolated worker runtime with SQLite task metadata, hard timeout, cancellation, bounded capacity, restart recovery, input/output size limits, and no automatic retries without an idempotency contract. Tests: `tests/unit/test_managed_worker_runtime.py`; combined worker/P8/P9 recheck: 34 passed.
- [x] Add an opt-in MainBrain managed-process entry point with explicit dual approval, Emergency Stop enforcement, bounded execution and durable metadata ledger. Evidence: `tests/unit/test_master_brain.py`; `logs/p4_managed_worker_mainbrain_integration_20261021.log`.
- [x] Route registered `dispatch_worker_team` child handlers through the managed runtime when `SAHIBEX_MANAGED_WORKER_DB` is configured; keep parent-side load/performance tracking and fail closed on serialization/execution errors. Evidence: `tests/unit/test_master_brain.py`; `logs/p4_full_targeted_verification_20261021.log`.
- [x] Verify two isolated live-model worker processes through MainBrain: both local-model responses returned `4`, joint verifier passed, both ledger tasks completed. Evidence: `logs/p4_live_model_worker_acceptance_20261021.log`.
- [x] Verify interrupted-task restart recovery on a disposable task DB; a previously running task is marked failed and is not resumed/claimed complete. Evidence: `logs/p4_restart_recovery_drill_20261021.log`.
- [x] Deploy/verify `SAHIBEX_MANAGED_WORKER_DB` in the actual `app.main` launch path and exercise launch/relaunch; the persistent ledger path is configured and remains present across relaunch. Evidence: `logs/p4_live_launcher_restart_acceptance_20261021.log`. The ledger intentionally stores task metadata only and never auto-resumes task execution.
- [x] Verify multi-step orchestration with two isolated live-model worker processes, not only deterministic test handlers; both answers jointly verified. Evidence: `logs/p4_live_model_worker_acceptance_20261021.log`. Separate model backends remain untested.

### P5 — Controlled self-improvement
Status: PASS for bounded metadata-only skill lifecycle on 2026-10-21; no unrestricted code execution or Constitution mutation is permitted.
- [x] Proposal -> security/regression/verification tests -> Mother + human approval -> version activation -> rollback to prior version. Evidence: `logs/p5_self_improvement_acceptance_20261021.md`.
- [x] Restart recovery: active version and proposals survive process restart; rollback survives a second restart.
- [x] Fail-closed cases: missing human approval, failed regression, injected state/audit commit failure, tampered audit chain and invalid persisted state prevent unsafe activation; audit chain remains verifiable where expected.
- [x] Fresh targeted acceptance: **115 passed, 0 failed**, exit 0. Evidence: `logs/p5_self_improvement_acceptance_20261021.log`.
- [x] Constitution/authority mutation flags remain false; MainBrain uses configured persistent audit/state stores.
- [ ] Do not claim arbitrary code-change self-improvement: executable code mutation is outside this metadata-only gate and remains disabled.

### P6 — Phone voice input/output
Status: PARTIAL — voice/bridge tests pass and a debug APK now builds/signature-verifies using Gradle 8.13 plus Termux-native AAPT2; physical phone round-trip remains pending.
- [x] Voice input/output, speech-text integration, bridge protocol, media runtime and real-runtime probe tests: **20 passed, 0 failed**. Evidence: `logs/p6_voice_bridge_acceptance_20261021.log`.
- [x] Add Gradle 8.13 wrapper scripts/properties and use a compatible Termux-native AAPT2 toolchain. Fresh `assembleDebug` and APK signature verification PASS; see `logs/p6_android_build_20261021.log` and `logs/p6_voice_acceptance_20261021.md`.
- [ ] Attach/install on the physical Android device; `adb devices -l` returned no attached/debug-authorized device.
- [ ] Test microphone speech -> authenticated relay -> real MainBrain -> visible response -> audible Android TTS, including Hindi/English, silence, cancellation, denied permission, bridge offline, timeout, and recovery.
- [ ] Do not claim always-listening/wake-word operation; this build is consent-initiated.

### P7 — Vision/OCR
Status: PARTIAL — Tesseract 5.5.3 with English/Hindi trained data, bounded OCR runtime, and provenance adapter are installed and smoke-tested; camera capture, representative OCR accuracy, and live image-understanding model remain pending.
- [x] Source audit confirms `core/brain/vision_reasoning.py` is a placeholder and camera capture is not connected to OCR. Evidence: `logs/p7_p8_device_capability_gate_20261021.md`.
- [x] Install Tesseract 5.5.3 with `eng` and `hin` language data; implement bounded OCR execution, capture-directory confinement, symlink rejection, image signature/extension matching, size/timeout limits, SHA-256 provenance, and untrusted-text marking. Evidence: `core/brain/ocr_runtime.py`, `core/brain/vision_ocr_integration.py`, `tests/unit/test_ocr_runtime.py`, `scripts/setup_ocr_termux.sh`.
- [ ] Connect consented camera/image acquisition and prove representative Hindi/English OCR accuracy; the current smoke test recognized only 3 characters and proves plumbing, not accuracy.
- [ ] Test Hindi/English text, blurry/rotated/blank/malformed images, uncertainty, and prompt injection embedded in images.
- [ ] Prove image -> OCR/vision -> evidence-grounded answer end-to-end. Do not send an image to a text-only model as if it can see it.

### P8 — Android Accessibility / computer control
Status: PARTIAL — software hardening, source-contract tests, Java compile, debug APK build, and signature verification PASS; physical device acceptance remains pending because no authorized ADB device is attached.
- [x] Device gate checked: `adb devices -l` returned no attached/debug-authorized device. Evidence: `logs/p7_p8_device_capability_gate_20261021.md`.
- [x] Build and signature-verify the debug APK; artifact: `~/storage/downloads/SAHIBEX-Android-Companion-P8-debug.apk`, SHA-256 `3588f7ae54e328d7f73795b73d0343083f395ab18833834e5b23051ac9427bff`. Evidence: `logs/p8_accessibility_acceptance_20261021.md`.
- [ ] Install APK on the phone and explicitly enable Accessibility service; then run the actual-device test.
- [ ] Run actual-device UI tree, tap, typing, key press, screenshot, emergency stop, permission-denial, and audit tests.
- [ ] Test stale coordinates, unexpected dialogs, app restart, and disconnected bridge.
- [ ] Keep each protected action behind explicit permission/confirmation.

### P9 — Integrated security and operational reliability
Status: **PASS for the defined bounded integrated acceptance scope (2026-10-21).** Overall SAHIBEX release remains blocked by other independent gates.
- [x] Fixed socket-connect DNS rebinding/SSRF gap in `core/research/web_provider.py`: connect-time resolution, reject private/reserved and mixed public/private answers, connect to the exact validated numeric sockaddr, disable environment proxies, and retain manual redirect validation.
- [x] Fixed a real HTTPS handler regression found by live smoke testing; pinned HTTPS fetch from `https://example.com/` returned HTTP 200 and content (`logs/p9_live_https_smoke_20261021.log`). TLS uses the original hostname for SNI/certificate validation.
- [x] Adversarial checks: private/loopback/link-local/reserved destinations, credentials in URLs, non-HTTP schemes, redirect controls, response-size limits, secret redaction, connect-time DNS rebinding, hostile document/prompt instructions, replay/freshness, corrupted/tampered evidence, path traversal, permission boundaries, Emergency Stop and rollback.
- [x] Bounded failure injection: simulated ENOSPC at the authenticated pre-execution audit prevented the protected write; simulated MemoryError worker task was marked failed rather than completed and a subsequent task succeeded. No production filesystem was filled and no device-wide memory exhaustion was induced.
- [x] Final focused security/replay/rollback batch: **108 passed** (`logs/p9_release_gate_final_targeted_20261021.log`); hostile-document, MemoryError, prompt-injection and recovery follow-up: **48 passed** (`logs/p9_integrated_adversarial_followup_20261021.log`); HTTPS regression batch: **33 passed** (`logs/p9_dns_tls_fix_targeted_20261021.log`).
- [x] Live services: local model ONLINE, web search ACTIVE, supervisor ONLINE, Android voice bridge HTTP HEALTHY. Loopback connection to ports 8080 and 38742 passed; connections to the device's non-loopback address were not reachable. Code config binds model and bridge to `127.0.0.1`. Evidence: `logs/p9_live_service_boundary_20261021.log`. Android restricts socket-table inspection in this Termux namespace, so no claim of continuous host-wide listener enumeration is made.
- [x] Full repository regression after final P9 code/tests: **2,030 passed in 180.42s**, exit 0 (`logs/p9_full_repository_regression_final_20261021.log`). Python compile check and `git diff --check` PASS.
- [x] Roadmap and acceptance report refreshed. Scope is bounded and non-destructive; this does not mean every possible hardware-level attack or destructive resource-exhaustion scenario was tested.

### P10 — Architecture requirement reconciliation
Status: NEEDS-RECONCILIATION.
- [ ] Exact historical 417-item source was not found in the local project/Git/known backups. Do not invent the original text or claim 417/417 completion.
- [ ] If the original cannot be recovered, prepare a clearly labelled reconstructed baseline from existing product intent/code/tests and obtain user approval before adopting it.
- [ ] Reconcile A–AC labels G/K/T/U/V/AC; map E01–E13; reconcile 6P-13..29 against official 6P-1..12.
- [ ] Map each item to implementation, tests, security evidence, live evidence, and status.

### P11 — Final Live Brain release gate
Status: PARTIAL / RELEASE BLOCKED — fresh regression and code gates pass, but P3/P6/P7/P8/P10 still have explicit remaining gates.
- [x] Full repository regression after P-series continuation: **2,015 passed in 186.71s**, exit 0. Evidence: `logs/p_series_final_full_pytest_20261021.log`.
- [x] `compileall`, shell syntax, and `git diff --check`: PASS. Evidence is recorded in the same final continuation tool run and can be rerun from Termux.
- [x] Current health: local model ONLINE, web search ACTIVE, supervisor ONLINE (PID 16652), Android voice bridge HTTP HEALTHY.
- [x] P1 live answer reliability smoke PASS; Task 37 fresh live MainBrain acceptance PASS with 3 publisher hosts, source traceability, protected-delete block and isolated insufficient-evidence fail-closed check.
- [x] P3/P4/P5 bounded acceptances recorded in `logs/p3_production_persistence_acceptance_20261021.md`, `logs/p4_child_worker_acceptance_20261021.md`, and `logs/p5_self_improvement_acceptance_20261021.md`.
- [x] P8 software acceptance: Accessibility service/bridge hardened, 13 P8 source-contract checks, Java compile PASS, debug APK assemble/signature verification PASS. Evidence: `logs/p8_accessibility_acceptance_20261021.md`; APK `~/storage/downloads/SAHIBEX-Android-Companion-P8-debug.apk`.
- [x] P3 bounded persistence/recovery gate closed on 2026-10-22: phone restart followed by live read-only DB quick_check=ok, 10,592 memory count and sample JSON/timestamp read-back; verified backup restored to isolated staging with 26-table integrity checks and real MasterBrain get_memory hash match; 18 focused tests passed. Evidence: logs/p3_staging_restore_drill_20261022.json and logs/p3_targeted_final_after_staging_restore_20261022.log. No production restore/write was performed.
- [ ] Remaining physical/specification gates: P6 physical voice round-trip; P7 OCR/vision; **P8 physical device acceptance** (install, enable service, UI tree/tap/type/screenshot, stop/restart); P10 original-source recovery or user-approved reconstructed baseline. P4 and P9 defined acceptance are closed; see the gate registry. P9 was accepted in a bounded, non-destructive scope.
- [ ] Publish a final status with separate columns for automated tests, current runtime, research quality, persistent memory, safe tools, worker/child brains, voice, vision, Accessibility, self-improvement, and historical specification coverage. Release must remain NOT LIVE until required gates pass.
Gate: no BLOCKED/PENDING core MVP item; optional modalities can remain explicitly PENDING if the initial release is text-first and user approves that scope.

## 5. Immediate next action — refreshed 2026-10-21
Latest evidence is consolidated in `logs/phase_p_series_reverification_20261021.md` plus `logs/p4_live_launcher_restart_acceptance_20261021.log`. Full repository regression is **2,015 passed in 186.71s**, focused P-series regression is **44 passed**, P1 live smoke, P2 live network edge acceptance, Task 37 live MainBrain E2E, P3 safe persistence, P4 defined worker/child acceptance, and P5 focused controlled self-improvement rechecks PASS. Remaining P3/P6/P7/P8/P10 gates are explicitly listed above; P9 bounded security/reliability acceptance is now PASS. The historical Phase 12 Brain Lifecycle suite is also reverified PASS at test scope; it is not a separate current P-series P12.
Completed bounded gates this continuation: P3 online backup/restore/hash, temporary-copy MasterBrain application-level restore read-back, and disposable abrupt-process recovery; P4 persistent child identity/memory, managed process dispatch, 37 focused tests, live two-worker model acceptance, interrupted-task recovery drill, and actual app launch/relaunch with managed-worker DB configured; P5 metadata-only self-improvement approval/rollback/restart acceptance; P8 Accessibility software hardening + buildable debug APK. Still open: P3 physical power-loss and authorized designated staging/production maintenance restore; P6 physical mic-to-TTS; P7 OCR/vision; **P8 physical phone acceptance**; P10 original 417-item specification recovery or user-approved reconstruction. P9 bounded integrated security/reliability gate is now PASS. Separate P4 model-backend orchestration was not tested and is a documented scope limit, not a blocker for the defined P4 acceptance. Overall SAHIBEX remains NOT LIVE-READY.

## 6. Non-negotiable operating rule
One canonical register: this file. Every completed step updates its checkbox, status, evidence log path, and timestamp. Never mark a whole phase PASS from a unit test. Never mark the product LIVE unless a real MainBrain request succeeds on the running device and the full text MVP acceptance passes. Keep device-only tasks visibly PENDING until the user performs the needed on-phone action.


## 7. Live smoke update — 2026-10-17 (after initial offline check)
- `scripts/start_local_model.sh`: PASS; model health became ONLINE at `127.0.0.1:8080`.
- Direct API completion with `chat_template_kwargs: {"enable_thinking": false}`: PASS, exact expected text returned. A deliberately short request without that option returned empty `content` and used the output budget on `reasoning_content`; production provider already sends the option.
- Real `MasterBrain.process()` Hindi explanation: first attempt `QUALITY_REJECTED` after ~32s; second attempt returned `STRUCTURALLY_VALID` after ~20s. The accepted text contained an obvious semantic error (“बैंड बनाने”).
- Root cause class identified: `core/brain/answer_quality.py` explicitly performs structural/lexical checks and says it cannot prove factual correctness; the general-response path does not corroborate this answer against trusted evidence. The fallback rejection message hides diagnostics, so debugging telemetry is also incomplete.
- Current health: local model ONLINE; search providers configured/active; background supervisor OFFLINE; Android voice bridge HTTP OFFLINE.
- Status change: runtime start is no longer currently OFFLINE, but overall Live Brain MVP remains BLOCKED by answer reliability and supervised-runtime/device gates. No source code was modified in this smoke-test step.


## 8. Final completion order — execute one gate at a time
This section is the execution queue; the 38-item checklist above is historical evidence and must not be rerun without a regression trigger.

1. **GATE A — Runtime stability (P0):** model starts reliably; supervisor owns the process; no duplicate/stale server; interactive MainBrain handles repeated requests; controlled stop/crash/port-conflict recovery is proven. Save health output and logs.
2. **GATE B — Truthful text answers (P1):** fix rejection diagnostics; separate structural quality from factual verification; factual answers use trusted evidence or clearly state uncertainty; Hindi/English golden cases pass; insufficient evidence fails closed.
3. **GATE C — Real task execution and authority (P1):** run the production entry point through intent, plan, permission, real harmless tool, independent result verification, final response and audit. Prove denied protected actions never execute.
4. **GATE D — Research matrix (P2):** current/stable facts, Hindi/English, independent publishers, conflict, stale/duplicate, inaccessible/short pages, empty search and timeouts. Each case has a saved result and source trace.
5. **GATE E — Durable trusted memory (P3):** production-like storage, provenance, restart recall, backup/restore and unverified-candidate isolation.
6. **GATE F — Commander/workers/child brain (P4):** real multi-step task, bounded worker lifecycle, persistent child identity and capability isolation across restart.
7. **GATE G — Controlled self-improvement (P5):** approved reversible change, sandbox/tests/review, audit, activation and rollback; denial/failure stops safely.
8. **GATE H — Security/operations (P9):** adversarial input, protected actions, secrets, path/network boundaries, cancellation, crash loops, low resources and emergency stop.
9. **GATE I — Phone capabilities (P6–P8):** APK build and Accessibility code checks are now PASS; voice round-trip, vision/OCR, and Accessibility runtime still require physical-device acceptance. These may remain pending only if the user explicitly approves a text-first initial release.
10. **GATE J — Specification reconciliation (P10):** recover the original 417-item list or label a reconstructed baseline and get user approval; map each requirement to code, tests and live evidence.
11. **GATE K — Final release decision (P11):** repeat full tests and all applicable live gates; publish a single evidence-backed report. Release status is NOT LIVE until core text MVP gates A–E and H pass; broader full-product completion also requires the remaining applicable gates.

### Per-gate reporting template
For every gate, record: date/time; exact command or user scenario; PASS/FAIL/BLOCKED; test count and exit code; log/report path; files changed; rollback/snapshot note; next blocker. A failed test is fixed and rerun before advancing. Never turn a missing device test into PASS.


## P1 final acceptance update — 2026-10-17

- Result: PASS for the defined P1 acceptance matrix. Overall SAHIBEX remains NOT LIVE-READY because P2–P11 and physical-device release gates remain.
- Safe rejection diagnostics now expose quality reasons, score, failure stage, and factual-verification boundary through MainBrain metadata.
- `STRUCTURALLY_VALID` is not treated as factual correctness. Curated local facts report `CURATED_KNOWLEDGE`; generated non-factual responses remain explicitly unverified.
- Factual questions use relevant verified knowledge with evidence. The operational knowledge retrieval path now falls back to meaningful query terms when exact phrase retrieval returns no match, while retaining the Knowledge Brain's verified-only/conflict lifecycle checks.
- Insufficient evidence returns `INSUFFICIENT_EVIDENCE`; detected contradictory polarity returns `CONFLICTING_EVIDENCE`. Neither path fabricates a factual claim.
- Live acceptance log: `logs/p1_live_answer_reliability_smoke_20261017.log` (local provider selected; real `MasterBrain.process()`; Hindi/English no-evidence and evidence-backed cases; conflicting claims; one non-factual local-model generation).
- Latest full regression log: `logs/p1_final_full_regression_20261017.log`; 1,887 passed in 156.16s; compileall PASS; `git diff --check` PASS.
- Focused coverage: `tests/unit/test_factual_answer_gate.py`, `tests/unit/test_main_brain_answer_reliability.py`.
- Protected execution acceptance: disposable sandbox write/read/delete verified actual bytes and final file state; explicit approval and authenticated intent/result traces passed; audit-storage failure blocks the protected side effect. Evidence: `tests/unit/test_main_brain_execution_audit_gate.py`, `tests/unit/test_tool_brain_runtime.py`.
- Live research / MainBrain E2E: Task 36 and Task 37 both PASS with `failed_checks: []`. Evidence: `logs/p1_task36_live_research_acceptance_20261017.log`, `logs/p1_task37_main_brain_e2e_acceptance_20261017.log`.
- Persistence/recovery: verified-memory restart/recall/provenance and cancellation/recovery tests passed in the full suite; cancellation prevents later research stages from executing. Evidence: `tests/unit/test_memory_brain_runtime.py`, `tests/unit/test_task34_persistence_restart_recovery.py`, `tests/unit/test_research_execution_manager.py`, `tests/unit/test_task35_failure_recovery.py`.
- Final P1 acceptance report: `logs/p1_final_acceptance_full_verification_20261017.md`.
- Scope limitation: this fixed matrix does not prove universal semantic truth for arbitrary generated text or broad live-news reliability. P2's broad live-source matrix, P3–P11 gates, and physical-phone voice/reboot acceptance remain. Overall product release remains NOT LIVE-READY.

### P2 final independent recheck — 2026-10-17
- Fresh live acceptance reruns: English PASS (`logs/p2_matrix_20261017/english_current_news_retest_20261017.json`), Hindi PASS with explicit MyMemory opt-in (`logs/p2_matrix_20261017/hindi_current_news_retest_20261017.json`), stable fact PASS (`logs/p2_matrix_20261017/stable_fact_retest_20261017.json`), HTTP edge matrix PASS 4/4 (`logs/p2_matrix_20261017/live_network_edge_acceptance_retest.stdout.json`).
- Fixed direct execution import path for `scripts/task36_live_research_acceptance.py`, `scripts/p2_live_network_edge_acceptance.py`, and `scripts/p2_translation_live_acceptance.py`.
- Final full repository regression after these script fixes: **1,905 passed in 161.24s** (`logs/p2_full_regression_final_3_20261017.log`); compileall PASS; `git diff --check` PASS.
- P2 bounded acceptance remains PASS; overall SAHIBEX remains NOT LIVE-READY pending later P3–P11 and physical-device gates.


### P2 user-requested final recheck — 2026-10-17
- User explicitly asked to finish P2. Re-ran English current-news, Hindi current-news (explicit MyMemory opt-in), and stable-fact live acceptance: all PASS with failed_checks: []. Evidence: logs/p2_matrix_20261017/english_current_news_user_recheck.json, logs/p2_matrix_20261017/hindi_current_news_user_recheck.json, logs/p2_matrix_20261017/stable_fact_user_recheck.json.
- Re-ran real HTTP edge matrix: 4/4 PASS; evidence: logs/p2_matrix_20261017/live_network_edge_acceptance_user_recheck.stdout.json.
- Focused P2 regression: 102 passed in 6.05s; full repository regression: 1,905 passed in 168.44s; compileall and git diff --check PASS. Logs: logs/p2_user_recheck_targeted_20261017.log, logs/p2_full_regression_user_recheck_20261017.log, logs/p2_user_recheck_compileall_20261017.log, logs/p2_user_recheck_diff_check_20261017.log.
- P2 bounded acceptance: PASS. Translation remains explicit opt-in; overall product release remains NOT LIVE-READY pending P3–P11 and physical-device gates.


## P6 final integration acceptance + controlled self-improvement — 2026-10-17
Status: **PASS for the defined bounded acceptance gate**. Full report: `docs/ROADMAP/P6_INTEGRATION_AND_SELF_IMPROVEMENT_ACCEPTANCE_2026-10-17.md`.

- Real English query through `MasterBrain.process()`: **PASS**. Four distinct publisher hosts; four fetched pages with trusted timestamps fresh within 24 hours; one corroborated claim; arbitration accepted; language matched; conflict status `NO_CONFLICT`.
- Real Hindi query through `MasterBrain.process()`: **PASS** with `SAHIBEX_TRANSLATION_PROVIDER=mymemory` explicitly set for that process only. Verified Hindi response, language diagnostics `MATCH`, numeric/URL tokens preserved, source answer retained for traceability, same four publisher hosts and freshness gate passed.
- Security: protected delete blocked before planning/execution; Constitution remained protected. Tests for unsupported claims, conflict handling, empty results, timeouts, inaccessible/partial sources and fail-closed recovery passed in regression suites.
- Controlled self-improvement through a real MasterBrain-owned lifecycle: metadata-only v1 and v2 each passed security/regression/verification tests and Mother + human approval; v2 activated; approved rollback restored v1. Persistent SQLite audit reopened with a valid hash chain and 12 lifecycle events.
- Failed-update recovery: injected activation-commit audit failure restores prior active version; failed regression, missing approval and tampered audit chain block activation.
- Focused suites: 309 passed and 84 passed (two separate batches; possible overlap). Full repository regression after the runner fix: **1935 passed in 161.07s; exit code 0**. Compileall, shell syntax and `git diff --check`: **PASS**.
- Scope remains bounded: metadata/skill-version update only; no executable-code self-update, no Constitution/authority changes. The audit journal is persistent but active skill-version registry remains in-memory; live answers did not automatically promote rows into the separate verified-knowledge table. Physical Android voice/vision/Accessibility gates remain separate. Overall product release is not thereby declared fully LIVE.


## P6 gap-closure update — 2026-10-17 (latest authoritative status)
- **P6 status: PASS for the bounded gate. Do not start P7 until the user asks.** Full evidence: `docs/ROADMAP/P6_INTEGRATION_AND_SELF_IMPROVEMENT_ACCEPTANCE_2026-10-17.md`.
- Persistent skill registry added and wired into live/supervisor/media-bridge startup using `SAHIBEX_SELF_IMPROVEMENT_STATE_DB`. Actual separate-process recovery verified: v1 activation, process restart, v2 activation/approved rollback, second process restart, v1 restoration, audit hash chain valid.
- Verified-knowledge promotion now runs only after final answer verification, accepted arbitration, complete supported/verified traceability, >=2 source IDs, evidence linkage, no unresolved conflict, and a persisted candidate with evidence. Verified-only retrieval still requires a persisted `VERIFIED` lifecycle event.
- Real MainBrain stable-fact acceptance passed in English and Hindi (Hindi translation explicitly opted in per process); each isolated test DB recorded one promoted verified knowledge row. Current-news attempts with insufficient independent corroboration were rejected safely and were not marked verified.
- Dedicated self-improvement restart suite: 7 passed. Post-change full repository regression: **1,942 passed in 160.30s**, exit 0. Compileall, py_compile, shell syntax and `git diff --check`: PASS.
- Scope remains explicit: no executable-code self-update, Constitution/authority changes, or bypass of human approval. Physical Android voice/vision/Accessibility remain separate release gates, not falsely marked complete by P6.


## P7 user-requested Memory/Learning + Android Voice acceptance — 2026-10-17

- This is a separate user-requested bundle (items 10–18 plus Android voice); it does **not** rename or overwrite the canonical roadmap's P7 Vision/OCR section.
- Software acceptance recheck: **1,953 passed in 185.01s**, exit code 0; compileall, shell syntax and `git diff --check` PASS. Full report: `docs/ROADMAP/P7_MEMORY_LEARNING_VOICE_ACCEPTANCE_2026-10-17.md`.
- Fixed natural-language retrieval relevance and limit ordering, Indic-script retrieval fallback, fail-closed scope matching for scoped user/task/child/namespace memories, corrupt DB initialization and transactional partial-write tests.
- Fixed ordinary prompt memory context so prior conversation answers do not reinforce themselves; added a language-matched deterministic greeting path and corrected Hindi greeting detection. Live authenticated text relay now returns a relevant English greeting and a Hindi greeting, each HTTP 200 / `success=true` with detected response language matching the query. Evidence: `logs/p7_20261017/voice_relay_english_final.json`, `logs/p7_20261017/voice_relay_hindi_final.json`.
- Android Companion debug APK built and copied to Android Downloads: `SAHIBEX-Android-Companion-P7-debug.apk`; SHA-256 `750a8abc72c8b53087447ade391376dbb4d062d6c8b130ae06b766d46204b8cb`. Voice language selection and answer-script TTS compile successfully.
- **Remaining blockers:** physical Android microphone → recognition → Main Brain → audible speaker acceptance is still PENDING because no ADB test device is connected. Universal multi-user memory isolation is not claimed for legacy unscoped records; those remain shared/global-compatible until they are migrated to explicit scopes and callers supply authenticated context. Overall product must not be marked fully LIVE.


## P-Series continuation update — 2026-10-21
- P4: added managed worker runtime with persistent task metadata, isolated process execution, hard timeout/cancel, bounded capacity, restart-fail semantics, and no automatic retries unless idempotency is proven. Unit acceptance: tests/unit/test_managed_worker_runtime.py.
- P6: Gradle 8.13 + Termux-native AAPT2 debug APK build and v2 signature verification pass; phone voice round-trip remains blocked by no attached/debug-authorized device.
- P7: Tesseract 5.5.3 with eng+hin data installed; OCR runtime, provenance bridge, setup script and real-engine smoke test added. Camera/visual-model and representative OCR accuracy gates remain.
- P8: APK build/signature remains PASS; physical UI tree/tap/type/screenshot/restart/emergency-stop acceptance remains pending without a connected device.
- P9: bounded integrated security/reliability acceptance PASS. Connect-time DNS pinning + live HTTPS smoke; hostile-document/prompt-injection, secret redaction/replay, emergency stop/rollback, ENOSPC/MemoryError fail-closed recovery, loopback service boundary and 2,030-test full regression verified. No destructive real disk-fill/device-wide memory-pressure test was performed.
- P10: original 417-item source still not recovered; do not substitute reconstructed baseline without user approval.
- New artifacts: logs/p_series_completion_status_20261021.md, logs/p_series_targeted_regression_20261021.log, logs/p_series_full_pytest_20261021.log.


### Post-restart follow-up (2026-10-22 00:03 +0530)
- User completed physical phone restart. Model health and Media Bridge health both returned healthy; supervisor/Main Brain processes were reported running in the prior post-restart check.
- Bounded read-only SQLite connect, schema query, and single-row `memories` read-back now PASS. No production DB writes were performed.
- Full live DB integrity/count and app-level retrieval after this physical restart remain NOT VERIFIED because earlier broad reads did not return promptly. Keep P3 PARTIAL; do not claim full restart recovery or release readiness. Evidence: `logs/p3_post_restart_recovery_20261021.json`.


### P3 live post-restart verification update (2026-10-22 00:05 +0530)
- Live production database opened strictly read-only. `PRAGMA quick_check` returned `ok` (23.18s); `SELECT COUNT(*) FROM memories` returned **10,592**; one memory row was read and its JSON plus datetime markers parsed successfully. Model health and Media Bridge health PASS. No production writes, restarts, or destructive operations performed.
- Evidence: `logs/p3_live_post_restart_quick_check_20261022.log`, `logs/p3_live_post_restart_memory_readback_20261022.log`, `logs/p3_post_restart_recovery_20261021.json`.
- P3 remains PARTIAL: the physical phone restart and post-restart live DB checks now pass, as do disposable service-cycle and temporary-copy application-level restore checks. A designated staging/authorized maintenance-window restore drill has not been run; do not mark P3 fully closed without it.



## P3 closure update — 2026-10-22
P3 is PASS for its defined bounded persistence/recovery scope. The verified pre-restart backup hash matched; after the user-performed phone restart, model and bridge health passed, live read-only SQLite quick_check returned ok, live memories count was 10,592, and a sample memory JSON/timestamp parsed. A separate staging restore from that verified backup passed quick/integrity checks across 26 tables and real MasterBrain get_memory content-hash read-back. The focused P3 regression set passed 18 tests; compileall and git diff --check passed. Production DB was not modified and no live service restart/restore was performed. Overall SAHIBEX remains NOT LIVE-READY because P6/P7/P8/P10 remain open.


---

## Authoritative status correction — 2026-10-23 (supersedes stale paragraphs above)

**Latest full repository regression: 2030 passed in 198.63s, exit 0.** Evidence: `logs/full_regression_20261023_145604.log`. Current validation also reports `compileall=PASS`, all `scripts/*.sh` shell syntax checks PASS, and `git diff --check=PASS`.

### Gate ledger — do not reopen without a trigger
- P1 PASS (bounded live answer reliability)
- P2 PASS (tested live research/network edge matrix)
- P3 PASS (bounded persistence/recovery; staging restore verified 26 tables and app-level memory hash; 18 focused tests passed). Evidence: `logs/p3_staging_restore_drill_20261022.json`, `logs/p3_targeted_final_after_staging_restore_20261022.log`.
- P4 PASS (bounded managed worker/child acceptance; 37 focused tests, live two-worker run, interrupted-task recovery and launcher/relaunch DB-path evidence).
- P5 PASS (bounded controlled self-improvement).
- P6 PARTIAL — actual phone microphone → recognition → Main Brain → audible TTS round-trip.
- P7 PARTIAL — representative Hindi/English OCR accuracy and integrated camera/image-understanding path.
- P8 PARTIAL — enable Android Accessibility, verify a real UI action, and complete emergency-stop drill.
- P9 PASS (bounded security/reliability acceptance; latest full regression is green).
- P10 BLOCKED — original historical 417-item source not recovered; reconstructed audit matrix is not the original. Need source recovery or explicit user approval to adopt a reconstructed baseline.
- P11 BLOCKED — final release gate remains closed until P6/P7/P8 device/vision criteria and P10 reconciliation are resolved.
- P12 PASS only for historical Brain Lifecycle test scope; not a current release gate.

### Fixed completion policy
Accepted gates remain PASS within their documented scope. Reopen only on a relevant code change, new approved requirement, or specific failing evidence. Run only the affected targeted tests plus the final release regression when needed. Never mark a passed gate PENDING because a different gate is incomplete. Update the registry and this master list together with evidence paths whenever a status changes.

### Next actions (only outstanding acceptance work)
1. P6: physical consented voice round-trip on the Android Companion.
2. P7: run a fixed representative Hindi/English image set, record OCR accuracy, and verify the image-understanding path.
3. P8: enable service on-device; verify one allowed UI action and Emergency Stop.
4. P10: recover the historical source, or ask user whether the clearly labelled reconstructed baseline may become the maintained specification.
5. P11: evaluate release readiness after items 1–4; no other accepted gate needs repeating unless a concrete regression trigger appears.


## P6/P7/P8/P10/P11/P12 checkpoint — 2026-10-23 (supersedes earlier statuses where newer evidence applies)

- Full repository regression after P7 OCR guard: **2031 passed in 165.91s, exit 0** — `logs/full_regression_20261023_p7_guard_163006.log`.
- Focused voice/OCR/accessibility/Emergency Stop/P12 tests: **34 passed in 2.09s**. `compileall`, all shell syntax checks, and `git diff --check` PASS.
- Fresh Android Companion build PASS; v2 signature verified; source/Downloads SHA-256 match `3588f7ae54e328d7f73795b73d0343083f395ab18833834e5b23051ac9427bff`. Build evidence: `logs/p6_p8_fresh_build_20261023.log`.
- P6 PARTIAL: software relay + build accepted; only remaining closure gate is actual phone microphone → speech recognition → Main Brain → audible TTS and consent/cancel/error cases. `adb devices -l` is empty.
- P7 PARTIAL: OCR code installed and language data `eng`/`hin` present. Fixed low-quality OCR fail-open by requiring >=3 meaningful characters and confidence >=35 before reasoning; regression test added. Existing sample still recognizes only `= P`; representative real-image accuracy and camera-to-live-vision-model integration remain. Do not claim vision complete.
- P8 PARTIAL: build and contract tests accepted; phone-side Accessibility enablement, a safe real UI action, and Emergency Stop after app/service restart remain. No authorized ADB device.
- P10 BLOCKED: original 417-item specification still not recovered according to the audited search history. The matrix is reconstructed, not the historical original. User must approve adoption of a clearly labelled reconstructed baseline or provide the original source.
- P11 BLOCKED: release gate depends only on the actual remaining P6/P7/P8 acceptance and P10 baseline decision; do not re-open P1/P2/P3/P4/P5/P9 without a specific trigger.
- P12 PASS for bounded Brain Lifecycle tests only; its focused test and full suite passed.
- Full record: `logs/p6_p7_p8_p10_p11_p12_checkpoint_20261023.md`.

### Only remaining user-side tasks
1. On the phone, open the Companion app and perform the consented mic-to-audible-TTS test; confirm audible response and test cancel/denied permission.
2. On the phone, enable Accessibility and perform one benign UI action plus Emergency Stop / local resume verification.
3. Supply the original 417-item source if available, or explicitly approve adopting a baseline labelled `RECONSTRUCTED — NOT THE HISTORICAL ORIGINAL`.

No other accepted gate needs repeating unless relevant implementation changes or a concrete regression failure appears.


## Additional feature — SAHIBEX Multi-Device Assistant (updated 2026-10-24)

Status: **IMPLEMENTED (secure software baseline); NOT COMPLETE until a separate computer is connected and end-to-end tests pass.**

- [x] Add cross-platform Python Desktop Agent inside this SAHIBEX repository.
- [x] Require HMAC-authenticated requests with a timestamp and replay-protected nonce.
- [x] Add unified `sahibex_control_bridge` routing for phone-local tasks and the configured desktop target.
- [x] Apply action-specific permission classification (READ_FILE, WRITE_FILE, RUN_COMMAND, NETWORK_ACCESS) through the canonical permission gateway.
- [x] Add desktop text-file read/write and bounded allowlisted argv program execution with local approval.
- [x] Keep listener loopback-only by default; refuse non-loopback binding unless TLS certificate and key are configured.
- [x] Support a bounded directory listing only under explicitly named roots; block traversal outside roots.
- [x] Keep unrestricted shell execution disabled. Workspace writes, allowlisted argv program launches and browser opening require approval on the desktop's own interactive console; no console means fail closed.
- [x] Add Main Brain tool registration conditional on a configured desktop endpoint and secret; preserve existing PermissionGateway and user confirmation.
- [x] Add targeted tests for signatures, replay/stale timestamps, wrong pairing secret, path traversal, HTTP transport restrictions and local integration.
- [x] Write setup and connection guide: `docs/multi_device/README.md`.
- [x] Targeted acceptance: **17 passed in 6.28s**, full repository regression **2048 passed in 173.90s**, compileall PASS, `git diff --check` PASS; action-specific permission routing and approved workspace read/write/command tests included. Evidence: `logs/multi_device_software_acceptance_20261024.md`.
- [ ] Run and test the agent on a real separate Windows/macOS/Linux computer.
- [ ] Verify phone-to-desktop TLS/CA trust and firewall reachability on the same trusted LAN.
- [ ] Verify approved and denied browser opening, disconnection/reconnect, and service restart on physical devices.
- [ ] Add any deeper UI interaction only through separately permission-gated, platform-specific adapters.

Run targeted acceptance: `PYTHONPATH=. .venv/bin/python -m pytest -q tests/unit/test_sahibex_device_fabric.py tests/unit/test_computer_control_tool_integration.py`. Update this status only with the saved current-turn test log and external-device evidence. This feature does not promote any P1–P12 status.

## Architecture visualization / source call-path audit — 2026-10-24 (documentation-only)

Status: **SOURCE CALL-PATH AUDIT PASS; ANDROID VISUAL REVIEW PENDING.** This is a documentation artifact, not a P1–P12 phase gate and not a product-release milestone.

- [x] Preserve prior architecture artifacts with a timestamped backup under `backups/architecture/` before editing.
- [x] Add `docs/architecture/SAHIBEX_EDGE_BY_EDGE_CALL_PATH_AUDIT_2026-10-24.md` with 19 individually classified edges, source file/line evidence, and explicit software-vs-physical acceptance boundaries.
- [x] Update `docs/architecture/SAHIBEX_3D_BRAIN_ARCHITECTURE.md` Mermaid source and checklist to distinguish `InternalBrainTeam.dispatch`, deterministic early exits, query-scoped memory retrieval, branch-specific result checks, and optional managed child workers.
- [x] Validate the SVG XML with Python `xml.etree.ElementTree`; SVG root and `viewBox` parse successfully.
- [x] Confirm Mermaid source block exists and all 19 edge entries are present in the audit document.
- [ ] Render and inspect the SVG visually on the target Android device; the current Termux environment has no installed SVG renderer, so this remains pending rather than being inferred from XML validity.
- [ ] Physical P6 voice, P7 camera/vision, and P8 Accessibility acceptance remain under their existing phase gates. This documentation work does not close those gates or change P1–P12 statuses.

Evidence: `docs/architecture/SAHIBEX_EDGE_BY_EDGE_CALL_PATH_AUDIT_2026-10-24.md`; `docs/architecture/SAHIBEX_3D_BRAIN_ARCHITECTURE.md`; `docs/architecture/SAHIBEX_3D_BRAIN_DATA_FLOW.svg`.

## P7 current-phone OCR quality probe — 2026-10-24

Status: **FAIL-CLOSED BEHAVIOUR PASS; OCR ACCURACY/INTEGRATION STILL PARTIAL.**
- [x] Run actual installed Tesseract 5.5.3 on a bounded synthetic English fixture and the existing `safe.png` fixture; record text, confidence and limitations.
- [x] Verify the pipeline rejects low-confidence synthetic OCR before creating a reasoning observation.
- [x] Focused OCR/vision contracts: **8 passed in 1.37s**; compileall and `git diff --check` PASS.
- [ ] Build/obtain a representative, consented Hindi/English image corpus and define a measured accuracy acceptance threshold.
- [ ] Connect consented camera/image acquisition to the OCR pipeline and an actual vision-capable reasoning endpoint; current local Qwen3 model is text-only.
- [ ] Keep P7 PARTIAL until the complete image → evidence/provenance → vision reasoning → grounded answer path is verified.

Evidence: `logs/p7_synthetic_ocr_probe_20261024.md`.


## Roadmap operating contract — user-confirmed, 2026-10-24

Purpose: keep one durable, detailed record of **everything accepted, everything newly added, and everything still open**, so completed work is not repeatedly redone.

### Required update after every work session or capability addition
- [ ] Record the exact feature/change and why it was added; identify its P-series gate or label it **separate capability** if it is outside P1–P12.
- [ ] Record status using only the defined vocabulary: PASS (bounded to named criteria), IMPLEMENTED, PARTIAL, PENDING, BLOCKED, or NEEDS-RECONCILIATION. Never turn unit-test PASS into physical-device/product COMPLETE.
- [ ] Record files/modules changed, any pre-change backup, test command, exact pass/fail counts and exit result, and durable evidence/log paths.
- [ ] List remaining work as specific acceptance steps, including dependency/blocker and what evidence will close each item.
- [ ] Update both this master list and the authoritative phase-gate registry in the same work session whenever a gate or its evidence changes. For a separate capability, maintain its own named status/evidence section here and in its dedicated record.
- [ ] Keep historic results for traceability; append a dated checkpoint rather than silently overwriting conflicting old evidence. Explicitly label superseded status statements.
- [ ] At the start of follow-up work, read the latest checkpoint/registry and work only on the next unresolved item. Reopen a PASS gate only for a relevant implementation change, a newly approved requirement, or credible failing evidence. Rerun only the affected tests unless a release checkpoint/cross-cutting change justifies the full suite.
- [ ] Preserve the phone workspace, uncommitted work, evidence, and backups. Never use reset/clean/delete as a shortcut. Physical phone, second-device, camera, microphone, Accessibility, network-pairing, or other external acceptance stays PENDING until actually observed and logged.

### Current checkpoint index — 2026-10-24
- **P1, P2, P3, P4, P5, P9:** PASS only within each gate's recorded bounded acceptance scope; do not repeat without a reopen trigger.
- **P6:** PARTIAL — physical microphone → recognition → Main Brain → audible TTS round-trip remains.
- **P7:** PARTIAL — low-quality OCR fail-closed probe PASS (8 focused tests); useful-image accuracy and integrated capture → OCR/provenance → vision reasoning → grounded answer remain.
- **P8:** PARTIAL — physical Accessibility enablement, benign UI action, and Emergency Stop drill remain.
- **P10:** BLOCKED — original 417-item specification not recovered; reconstructed baseline requires explicit user approval.
- **P11:** BLOCKED — release gate cannot pass while required gates above and specification reconciliation remain open.
- **P12:** historical lifecycle tests PASS in their recorded scope; do not treat as a substitute for a current release gate.
- **Separate capability — multi-device fabric:** software baseline IMPLEMENTED and its recorded tests PASS; external computer/second-phone pairing and real-network acceptance remain PENDING. User explicitly deferred second-phone pairing until current-phone gaps are addressed.
- **Architecture documentation:** source call-path audit PASS (19 edges/23 in-range source anchors); SVG XML validation PASS; Android visual rendering/review PENDING.
- **Do not count this roadmap-policy update as implementation progress or as a phase-gate PASS.**


## Current-phone P7/P8 software recheck — 2026-10-24 late checkpoint

- Read the authoritative roadmap/registry before testing; kept the second phone unpaired as requested.
- Focused command PYTHONPATH=. .venv/bin/python -m pytest -q tests/unit/test_p8_accessibility_contract.py tests/unit/test_android_companion_media_server.py tests/unit/test_p7_fail_closed_scope_retrieval.py tests/unit/test_ocr_runtime.py: **37 passed in 2.66s**, exit 0. Log: logs/current_phone_p7_p8_recheck_20261024.log.
- Android Companion rebuilt using the supported Termux script bash scripts/build_android_companion_termux.sh: **BUILD SUCCESSFUL**, exit 0; APK v2 signature PASS; source and Downloads SHA-256 match 3588f7ae54e328d7f73795b73d0343083f395ab18833834e5b23051ac9427bff. Log: logs/current_phone_companion_build_20261024.log. APK copied to ~/storage/downloads/SAHIBEX-Android-Companion-P8-debug.apk.
- PYTHONPATH=. .venv/bin/python -m compileall -q app core tools scripts: PASS; git diff --check: PASS. Evidence details: logs/current_phone_remaining_work_recheck_20261024.md.
- Build environment note: created local ignored android_companion/local.properties pointing to the existing SDK at /data/data/com.termux/files/home/android-sdk; the supported script applies Termux-native AAPT2. No application source was changed for this configuration fix.
- **No phase gate promoted to COMPLETE**: adb devices -l shows no attached device. P6 physical voice, P7 real-image/vision reasoning, and P8 Accessibility/UI/Emergency Stop acceptance remain PARTIAL. P10 original-spec reconciliation remains BLOCKED; P11 release remains BLOCKED.
- Status reconciliation note: the older P3 paragraph near the beginning of this file saying PARTIAL is superseded by the dated 2026-10-22 P3 closure update and the current registry's P3 PASS for its bounded scope. Preserve the old note as history; do not reopen P3 absent a trigger.

### 2026-10-25 checkpoint — P8 bridge integration
- [x] Route Python Android control provider through authenticated loopback Companion Accessibility bridge; add UI-tree request and fail-closed completion/token checks.
- [x] Add focused regression tests: 24 passed; compileall and `git diff --check` passed.
- [ ] Provision private Companion token locally to `data/android_companion_control_token` with mode 0600 (never send token in chat/logs).
- [ ] Verify live Main Brain → Companion UI-tree response and one harmless UI action on device.
- [ ] Verify Emergency Stop blocks actions across restart and Resume requires local confirmation.
- Gate stays P8 PARTIAL until all physical acceptance steps pass. Evidence: `logs/p8_mainbrain_accessibility_bridge_fix_20261025.md`.


## 2026-10-25 — P1 focused self-identity answer improvement

- **Problem reproduced:** in an isolated temporary database, the Main Brain refused the simple project-identity questions `SAHIBEX kya hai? Hindi mein 3 points.` and `What is SAHIBEX? Explain in 3 points.` as `INSUFFICIENT_EVIDENCE` despite the project definition being documented.
- **Implemented:** exact-match curated Hindi/Hinglish and English project-identity facts in `core/brain/factual_resolver.py`; added regression tests in `tests/unit/test_master_factual_fastpath.py`. The answer explains the chosen full form and Main Brain responsibilities and states that SAHIBEX remains under development.
- **Verification:** focused answer-reliability suite **46 passed in 6.98s**; additional local-provider/factual-gate subset **12 passed in 1.21s**; compileall and `git diff --check` PASS. Temporary-DB live `MasterBrain` probe now returns `CURATED_KNOWLEDGE` in about 0.01s for the exact Hindi and English identity questions. A compound question about the latest version remains `INSUFFICIENT_EVIDENCE`, so no version is fabricated.
- **Evidence:** `logs/p1_sahibex_identity_fastpath_20261025.md` and matching checkpoint in `docs/ROADMAP/SAHIBEX_PHASE_GATE_REGISTRY_2026-10-21.md`.
- **Scope limit:** this fixes one reproducible identity-knowledge gap only. It is not proof of autonomous/general intelligence and does not close the remaining P6/P7/P8 physical acceptance or P10/P11 release blockers. Preserve all other worktree changes and do not rerun accepted gates without a relevant trigger.

### 2026-10-25 checkpoint — Main Brain research/learning regression recheck
- Re-read the current roadmap/registry and rechecked the existing reasoning/research/verification/learning loop without reopening bounded PASS gates.
- Focused suite: `PYTHONPATH=. .venv/bin/python -m pytest -q tests/unit/test_research_learning_brain.py tests/unit/test_research_learning_brain_query_normalization.py tests/unit/test_mother_learning_integration.py tests/unit/test_mother_research_answer_integrity.py tests/unit/test_master_brain_research_flow.py tests/unit/test_research_answer_pipeline.py tests/unit/test_research_answer_final_gate.py tests/unit/test_research_findings_to_knowledge_linking.py tests/unit/test_learning_history_persistence.py tests/unit/test_p6_controlled_self_improvement_live_cycle.py tests/unit/test_p6_self_improvement_restart_recovery.py`: **120 passed in 16.86s**, exit 0. A narrower overlapping suite also passed: **54 passed in 4.23s**.
- Evidence: `logs/main_brain_reasoning_learning_recheck_20261025.md`.
- Assessment: the checked software paths currently enforce research query normalization, VERIFIED-only persistence claims, non-zero verified learning before reporting persistence, answer-final-gate integrity, knowledge linking, learning-history persistence, and gated self-improvement lifecycle. No new regression was reproduced, so no speculative code change was made.
- Scope limit: this does not establish general intelligence or live physical/device acceptance. P6/P7/P8 remain PARTIAL, P10 remains BLOCKED, and P11 remains BLOCKED. Continue from a concrete reproducible reasoning failure; do not repeat passed tests without a relevant trigger.

### 2026-10-25 checkpoint — reasoning verification fail-closed fix
- **Concrete bug fixed:** `ReasoningCoordinator.assess()` could set `verified=True` despite `missing_information=True` or `ambiguous=True` when the weighted uncertainty remained below 0.60. `verify()` could also promote an unverified candidate based only on unchanged confidence/uncertainty metadata without new evidence.
- **Change:** missing information and ambiguity now independently block verified status and force `needs_verification`; metadata-only reverification cannot promote an unverified candidate. Added three regression tests.
- **Backup before edit:** `core/brain/reasoning_coordinator.py.pre_safety_fix_20261025.bak`; `tests/unit/test_reasoning_coordinator.py.pre_safety_fix_20261025.bak`.
- **Verification:** focused reasoning suite **22 passed in 1.81s**, exit 0; wider reasoning/Main Brain integration suite **46 passed in 4.88s**, exit 0; compileall and `git diff --check` PASS.
- **Evidence:** `logs/reasoning_verification_missing_information_fix_20261025.md`.
- This is a bounded software safety fix, not a claim of general intelligence; no P-series status changes. P6/P7/P8 remain PARTIAL, P10 BLOCKED, and P11 BLOCKED.


## P6 local offline ASR implementation — 2026-10-25

- Android Companion now records PCM through `AudioRecord` rather than invoking `RecognizerIntent` / Android speech recognition. The authenticated loopback bridge sends audio to SAHIBEX's local `whisper.cpp` model; no remote ASR is called. Audio is capped at 20 seconds and deleted from temporary storage after transcription.
- Transcript correction review is explicit: the user can edit/cancel, and only confirmed text is routed to Main Brain. Dictionary coverage was expanded for common Hindi/Hinglish and voice-recognition terms while keeping uncertain spellings suggestion-only.
- Focused voice/recognition/Main Brain security/Accessibility/P-series contracts: **79 passed** on the prompt-enabled code. The local engine correctly transcribed a real English speech fixture. Android APK build + v2 signature verification pass; copy hash recorded in `logs/p6_offline_asr_implementation_20261025.md`.
- Live bridge/model acceptance: old media-bridge process safely restarted after proving it served old code; health HTTP 200, invalid-token route HTTP 401, authenticated local transcription HTTP 200 with correct fixture text, `audio_retained=false`, and `requires_user_confirmation=true`. This does not test Android microphone hardware.
- **P6 status remains PARTIAL**. The APK still needs physical installation/UI test; no real microphone-to-audible-TTS device round-trip or Hindi/Hinglish accuracy result is claimed. Output uses the device TTS engine until the user supplies the custom voice sample.

### 2026-10-25 voice-output engineering evidence
- Added offline Piper TTS adapter, authenticated `/synthesize` WAV endpoint, Android neural-first playback and visible compatibility fallback.
- Focused verification: 18 passed; Python compile + diff check passed; APK assembled and v2 signature verified.
- Still open: install/configure actual Piper executable and Hindi/English models; test real WAV generation and phone speaker playback; listen/accept Hindi/Hinglish/English pronunciation; custom voice sample later. This work does not change P6 from PARTIAL. Details: `logs/p6_neural_tts_integration_20261025.md`.

## 2026-10-25 P6 voice-output engineering update
- Local Sherpa-ONNX Supertonic-3 Hindi/English synthesis is now integrated and authenticated `/synthesize` was verified to return valid WAV for both languages. Focused voice suite: 28 passed; updated Companion APK built and signature-verified.
- P6 remains PARTIAL pending physical APK installation, audible speaker playback, mic/ASR/Main Brain end-to-end acceptance, and quality/latency review. Model terms OpenRAIL-M require review before distribution/commercial deployment. Evidence: `logs/p6_sherpa_supertonic_runtime_20261025.md`.
- P6 follow-up: persistent neural-engine cache + serialized inference gate + HTTP 429 busy response added and verified. Focused voice tests now 31 PASS; live authenticated Hindi/English synthesis rechecked. Full phone speaker and microphone end-to-end acceptance remain pending.
- Cross-layer regression recheck after P6 voice changes: 46 passed in 5.82s across TTS/media bridge/ASR/language perception/factual fastpath/reasoning/failure recovery/persistence recovery.

### 2026-10-25 — cognitive neural routing bilingual fix
- [x] Add English/Romanized Hindi/Hinglish/Devanagari multi-step markers to the advisory cognitive routing layer.
- [x] Preserve Devanagari matras during punctuation normalization; regression proves Hindi multi-step phrases route deliberatively.
- [x] Verify protected-action inhibition remains dominant; 31 focused integration tests PASS; compileall and diff-check PASS.
- [ ] Continue architecture review for explicit module contracts, observability, resource bounds, and safe fallback across perception/planning/verification/memory/tool execution. This is not a claim that all cognitive architecture work is complete.
- Evidence: `logs/cognitive_neural_bilingual_routing_20261025.md`. No P-series gate status changed.

### 2026-10-25 — P7 OCR evidence boundary hardening
- [x] Bound OCR text passed to reasoning to 16k characters and label truncation.
- [x] Sanitize control characters in embedded provenance metadata and reject malformed SHA-256 before creating a vision observation.
- [x] Regression: 17 focused P7/OCR tests PASS; compileall and diff-check PASS; source/test backups preserved.
- [ ] Real image corpus, camera capture/consent integration and actual visual model reasoning remain pending; this work does not complete P7.
- Evidence: `logs/p7_ocr_evidence_boundary_hardening_20261025.md`.

### 2026-10-26 — P7 OCR provenance file-write safety fix
- [x] Hardened provenance output against check/write races and symlink redirection; files are created exclusively with no-follow semantics where supported and POSIX mode 0600.
- [x] New overwrite/symlink/privacy tests pass; focused OCR/vision suite **19 passed**, wider P7/P8 bridge contract batch **45 passed**; compileall and diff-check PASS.
- Evidence: `logs/p7_atomic_private_provenance_write_20261026.md`; source/test backups preserved beside files.
- [ ] P7 remains PARTIAL: real Hindi/English image accuracy, consented capture, and actual visual reasoning integration still need acceptance. P6/P8 device gates and P10 specification decision are unchanged; P11 remains BLOCKED.


### 2026-10-26 implementation checkpoint — P8 fail-closed text-action reporting
- [x] If Android rejects Accessibility `ACTION_SET_TEXT`, report a failure via exception rather than a success-shaped response; add regression contract. Focused suite: 23 passed.
- [x] Record evidence and blocker: `logs/p8_text_action_fail_closed_20261026.md`.
- [ ] P8 physical acceptance remains open: Android app build/signature/install, Accessibility service enabled, benign UI action verified, Emergency Stop remains effective after app/service restart, and local resume verified.
- [ ] Build blocker: Maven AAPT2 Linux executable fails under Termux; retry using `scripts/build_android_companion_termux.sh` with Termux-native AAPT2 and verify APK/signature before install.

- [x] Follow-up: built P8 debug APK with Termux-native AAPT2; signature verified (v2, one signer), SHA-256 `f58948c08f4dca5477fec6cc40db3eca5556ae22c3a3867b7511e77ca60c73aa`; copied to Downloads. Extended focused tests: 44 passed; compileall/diff check passed.
- [ ] Physical device acceptance still pending; APK intentionally not installed by this automated step.
- [x] Full repository regression after P8 change: 2089 passed in 169.92s; exit code 0. Device acceptance remains open.


### 2026-10-26 — Next backend gap audit: real vision reasoning
- Confirmed `core/brain/vision_reasoning.py` is a contract/observation container and does not invoke a computer-vision model; `core/brain/vision_ocr_integration.py` forwards OCR text but is not actual image understanding.
- Local model inventory found only Sherpa Supertonic TTS ONNX weights; no vision-model weights or `transformers`, `torch`, `onnxruntime`, `Pillow`, or `llama_cpp` packages in `.venv`.
- Valid P7 contract/OCR regression: `PYTHONPATH=. .venv/bin/python -m pytest -q tests/unit/test_vision_reasoning_integration_contract.py tests/unit/test_vision_input_contract.py tests/unit/test_ocr_runtime.py tests/unit/test_p7_fail_closed_scope_retrieval.py` → **19 passed in 1.24s**, exit 0. Evidence: `logs/p7_real_vision_backend_gap_audit_20261026.md`.
- P7 remains PARTIAL. Next software step: implement a bounded local-only vision-provider adapter and integrate fail-closed. No image should be sent to an external endpoint implicitly; no actual visual reasoning is claimed until a compatible local vision model/server is configured and exercised.


### 2026-10-26 — Qwen3-VL Kaggle evaluation notebook prepared
- Added separate, non-destructive notebook: `cloud/SAHIBEX_Qwen3_VL_Kaggle_GPU.ipynb`. First benchmark candidate is `Qwen/Qwen3-VL-2B-Instruct`; it checks GPU, loads the model in the Kaggle session, and tests a synthetic image. Existing Qwen3-4B text-model notebook is unchanged.
- Notebook JSON and code-cell syntax validation: PASS; `git diff --check`: PASS. Evidence: `logs/p7_qwen3_vl_kaggle_notebook_20261026.md`.
- Not yet run in Kaggle. GPU/internet availability, model download, actual vision response, accuracy, latency, and phone-cloud integration remain UNVERIFIED. No model download, phone package installation, public endpoint, or tunnel was performed. **P7 remains PARTIAL**.


## 2026-10-28 — New Specialist Brain catalogue work (PARTIAL)

- Implemented a declarative catalogue of **60 specialist roles** in `core/brain/specialist_catalogue.py`; added `tests/unit/test_specialist_catalogue.py`.
- Focused verification: **23 passed** across catalogue, BrainRegistry, InternalBrainTeam and specialist dispatcher tests; compileall and `git diff --check` PASS.
- The catalogue is not a claim that 60 runtime handlers/models exist. Runtime coverage mapping and safe router integration remain the next unresolved gate. No existing P-series status changed; preserve all pre-existing worktree changes.


## 2026-10-28 — Runtime coverage mapping (PASS for status reporting only)

- `InternalBrainTeam.specialist_catalogue_coverage()` now reports coverage from live handler registrations, not from role names alone.
- Live status: 60 catalogue roles, 10 backed by handlers, 50 missing/unwired.
- Focused suite: 24 passed; broader MotherBrain/specialist integration suite: 71 passed. compileall and `git diff --check` PASS.
- No P1–P12 gate promoted. Next: add only bounded, real implementations with explicit contracts and tests; leave unavailable backends honestly marked missing.


## 2026-10-28 — Teaching Brain bounded handler integration (PASS for scoped handler only)

- Added a real `teaching` internal role and registered a deterministic, bounded lesson-outline handler in Mother Brain. It accepts a topic, normalizes level/language options, returns four teaching steps, and explicitly reports that no external research, tool execution, file writing, or factual verification occurred.
- It remains behind the existing explicit authorization and request-verification dispatch gates. This is an outline generator, not a claim that an LLM-generated lesson has been fact-checked.
- Initial coverage test correctly exposed stale expected counts (10/50); fixed the regression assertion to 11/49 after registering the new handler. Final focused tests and compile/diff checks are recorded below. No P1–P12 gate is promoted by this change.

- Final verification: `PYTHONPATH=. .venv/bin/python -m pytest -q tests/unit/test_internal_brain_team.py tests/unit/test_specialist_catalogue.py tests/unit/test_brain_registry_contract.py tests/unit/test_child_authority_boundary.py tests/unit/test_child_verification_trust_boundary.py tests/unit/test_operational_specialist_dispatch.py` → **25 passed in 3.66s**, exit 0. `compileall` PASS; `git diff --check` PASS. Live coverage is now **11 implemented / 49 missing** out of 60 catalogue profiles.
- Scope PASS: the bounded Teaching Brain outline handler and its safety/coverage regressions. Overall 60-role architecture remains PARTIAL; no P1–P12 gate promoted and no full-suite run claimed.


## 2026-10-28 — Document/File Brain bounded supplied-text handler (PASS for scoped handler only)

- Added a dedicated `document_file` internal role. It accepts only explicit `document_text`, extracts bounded source lines, and reports source-grounded extraction rather than a fact-verified summary. It never opens, writes, or deletes files and never executes document content.
- Existing authorization and request-verification gates remain in force. Tests/compile/diff checks are pending; no P1–P12 status is promoted.

- Final verification: focused internal-team/catalogue/registry/child-authority/child-verification/specialist-dispatch suite → **27 passed in 5.27s**, exit 0. `compileall` and `git diff --check` PASS. Runtime coverage now **12 implemented / 48 missing** out of 60 catalogue roles.
- Scope PASS: bounded supplied-text extraction handler and its safety/coverage regressions only. It does not provide arbitrary filesystem access or a fact-verified generated summary. Overall architecture remains PARTIAL; no P1–P12 gate promoted and full repository regression not claimed.


## 2026-10-28 — System Architecture Review Brain bounded handler (PASS for scoped handler only)

- Added a system_architecture role using only explicitly supplied architecture_text. It extracts lines that appear to identify components and dependency/data-flow relationships, reports gaps and truncation, and explicitly does not claim repository completeness or factual verification.
- It does not read/write files or execute code. Existing authorization and request-verification dispatch gates remain required. P1–P12 statuses are unchanged pending test results.

- Final verification: focused internal-team/catalogue/registry/child-authority/child-verification/specialist-dispatch suite → 29 passed, exit 0; changed-file compileall PASS; git diff --check PASS. Runtime coverage is now 13 implemented / 47 missing out of 60 catalogue profiles. No P1–P12 status promoted; full repository regression not run.


## 2026-10-28 — Performance/Resource Brain bounded metrics assessor (verification pending)

- Added a performance_resource role that evaluates only caller-supplied RAM/CPU/GPU percentage metrics against conservative thresholds. Invalid or out-of-range values are ignored with warnings. It does not inspect live system state, execute commands, unload models, or change runtime behavior.
- Existing authorization and request-verification gates remain required. No P1–P12 status is promoted pending tests.

- Final verification: focused internal-team/catalogue/registry/child-authority/child-verification/specialist-dispatch suite → **31 passed in 5.85s**, exit 0; changed-file compileall PASS; git diff --check PASS. Runtime coverage now **14 implemented / 46 missing** out of 60 catalogue profiles. No P1–P12 gate promoted; full repository regression not run.


## 2026-10-28 — Privacy/Data Governance Brain bounded scope assessor (PASS for scoped handler only)

- Added `privacy_data_governance` as a metadata-only policy assessor. Missing principal/owner or field-scope metadata fails closed; owner mismatch and cross-child mismatch are denied; requested fields outside the supplied allowlist are denied and permitted fields are reported separately. Duplicate requested fields are de-duplicated.
- This handler does not read/expose stored data, grant permissions, or enforce authorization in downstream storage/connectors. It is a decision-support check only; existing upstream authorization and verification gates remain required.
- Focused verification: internal team, specialist catalogue, registry contract, child-authority, child-verification and operational specialist dispatch tests; compileall and `git diff --check`. Coverage target after passing tests: 15 implemented / 45 missing out of 60. No P1–P12 gate promotion; full repository regression not run.


## 2026-10-29 — Human Handoff Brain bounded preparation handler (scoped verification PASS)

- Added a `human_handoff` handler that prepares a concise handoff from explicitly supplied summary, completed items, blockers, decisions needed and approval flag. Missing summary and malformed metadata fail closed; list content is bounded and deduplicated.
- It does not send messages, contact people/services, grant approval or execute actions. The output explicitly remains PREPARED_NOT_SENT. Existing authorization and request-verification gates remain required.
- Verification on 2026-10-29: focused internal-team/catalogue/registry/child-authority/child-verification/specialist-dispatch suite **44 passed in 13.63s**, exit 0; changed-file `compileall` PASS; `git diff --check` PASS. Live catalogue coverage **19/60 implemented, 41/60 missing**. A stale test expectation for 18 roles was corrected to 19 to match the current registry.
- Scope PASS only. Full repository regression and live handoff integration remain unverified; no P1–P12 gate promoted.

## 2026-10-29 — Evidence & Fact-Checking Brain bounded supplied-evidence assessor (PASS for scoped handler only)

- Added and registered `evidence_fact_checking`; validates supplied claim/evidence shapes and provenance, detects explicit support/contradiction/conflict mappings, and reports uncertainty. It never implies source authenticity or independent factual verification.
- Focused verification: **39 passed in 6.11s**; changed-file compileall and `git diff --check` PASS. Runtime catalogue coverage: **17/60 implemented, 43/60 missing**.
- Remaining: full repository regression and live research/source-quality integration are not verified by this scoped handler. No P1–P12 status promotion.


## 2026-10-29 — Backup & Continuity Brain bounded evidence assessor (PASS for scoped handler only)

- Added and registered `backup_continuity` to assess only caller-supplied backup metadata, manifest shape, integrity result and restore-test result. Missing or malformed evidence fails closed; a supplied PASS is never presented as independently verified.
- No filesystem reads/writes, backup creation, deletion, restore or runtime changes are performed. Actual backup integrity and restore testing remain separate operational gates.
- Focused internal-team/catalogue/registry/child-authority/child-verification/specialist-dispatch suite: **41 passed in 5.19s**, exit 0. Changed-file `compileall` PASS; `git diff --check` PASS. Runtime catalogue coverage: **18/60 implemented, 42/60 missing**.
- Scope PASS only. Full repository regression not run; P1–P12 gate statuses remain unchanged.

## 2026-10-29 — Uncertainty Brain bounded claim-metadata assessor (PASS for scoped handler only)

- Added and registered `uncertainty`; it evaluates only caller-supplied claim/evidence/source/conflict counts, flags missing evidence or unresolved conflicts, rejects malformed/out-of-range metadata, and caps each request at 50 claims.
- It does not create confidence scores, verify factual truth, perform research, modify claims, or bypass the existing authorization/request-verification gates.
- Verification: focused internal-team/catalogue/registry/child-authority/child-verification/specialist-dispatch suite **46 passed in 9.34s**, exit 0; changed-file `compileall` PASS; `git diff --check` PASS. Live coverage: **20/60 implemented, 40/60 missing**.
- Scope PASS only. Full repository regression and integrated live research verification remain pending; no P1–P12 gate promoted.


## 2026-10-29 — Next Specialist Brain accepted: Decision Analysis
- **Scoped PASS:** `decision_analysis` is now a real bounded internal handler. It ranks 2–10 options using 1–10 explicit caller-provided criteria, validates all weights/scores, and reports ties. It never invents scores or claims real-world verification.
- Verification evidence: `logs/decision_analysis_brain_20261029.md`; focused **48 passed**, broader integration **64 passed**, final focused rerun **48 passed**, compileall PASS, `git diff --check` PASS.
- Live specialist catalogue: **21 implemented / 39 missing or unwired out of 60**. Older appended entries contain historical counts from their own checkpoints; the latest live introspection is authoritative for current coverage.
- HISTORICAL NOTE — specialist wiring statement superseded on 2026-10-29 by `logs/specialist_catalogue_final_wiring_20261029.md`: all 60/60 catalogue roles now have registered handlers, but several remain bounded/proposal-only rather than production backends. No P1–P12 gate was promoted by catalogue wiring. P6/P7/P8 physical acceptance, P10 source reconciliation and P11 release gate remain open.


## 2026-10-29 — Debugging Brain bounded failure-report triage (scoped PASS)
- Added and registered `debugging`; it validates bounded caller-supplied failure reports, identifies missing reproduction evidence, and suggests conservative diagnostic steps without claiming an unproven root cause.
- Safety: no code execution, filesystem access, runtime change, tool invocation, or permission grant. Existing authorization and request-verification gates remain required.
- Verification: focused suite **50 passed in 8.09s**; broader Master Brain/dispatch suite **63 passed in 5.69s**; changed-file `compileall` PASS; `git diff --check` PASS. Pre-change copies are preserved in `backups/debugging_brain_20261029/`.
- Live catalogue coverage: **22/60 implemented, 38/60 unwired**. Scoped handler PASS only; no full repository regression or P1–P12 gate promotion. Overall architecture remains PARTIAL.


## 2026-10-29 — App Builder Brain bounded outline handler (scoped PASS)
- Added and registered `app_builder`; drafts proposed screens and high-level layers from explicit app requirements, de-duplicates feature labels, and flags missing target-user/acceptance criteria.
- Proposals require user review. No file writes, executable code generation, build, deployment, or independent requirements verification.
- Verification: focused suite **52 passed in 4.55s**; broader suite **65 passed in 5.63s**; changed-file `compileall` and `git diff --check` PASS. Pre-change copies: `backups/app_builder_brain_20261029/`.
- Live catalogue coverage: **23/60 implemented, 37/60 unwired**. Scoped PASS only; full regression/P1–P12 status unchanged.


## 2026-10-29 — Planning Brain dependency-graph validator (scoped PASS)
- Added and registered `planning`; validates up to 30 supplied tasks, checks dependency references and cycles, and returns a deterministic proposed topological order only for a valid graph.
- It does not execute tasks, create a schedule, grant permissions, or perform external actions.
- Verification: focused suite **54 passed in 4.60s**; broader suite **67 passed in 5.75s**; changed-file `compileall` and `git diff --check` PASS. Backups: `backups/planning_brain_20261029/`.
- Live catalogue coverage: **24/60 implemented, 36/60 unwired**. Scoped PASS only; no P1–P12 gate promotion.


## 2026-10-29 — Code Review Brain bounded heuristic diff scan (scoped PASS)
- Added and registered `code_review`; scans explicitly supplied diff text for selected risky patterns and reports review-required signals with line/excerpt evidence.
- Findings are not confirmed vulnerabilities; scan is bounded and explicitly non-exhaustive. No code execution or repository access.
- Verification: focused suite **56 passed in 4.69s**; broader suite **69 passed in 5.80s**; changed-file `compileall` and `git diff --check` PASS. Backups: `backups/code_review_brain_20261029/`.
- Live catalogue coverage: **25/60 implemented, 35/60 unwired**. Scoped PASS only; P1–P12 gates unchanged.


## 2026-10-29 — Data Analysis Brain descriptive-statistics handler (scoped PASS)
- Added and registered `data_analysis`; computes descriptive summaries from supplied tabular rows, reporting valid counts, mean/min/max, missing and invalid values.
- Bounded to 500 rows / 20 fields; no external data access, row mutation, significance testing or causal inference.
- Verification: focused suite **58 passed in 4.78s**; broader suite **71 passed in 5.98s**; changed-file `compileall` and `git diff --check` PASS. Backups: `backups/data_analysis_brain_20261029/`.
- Live catalogue coverage: **26/60 implemented, 34/60 unwired**. Scoped PASS only; P1–P12 gates unchanged.


## 2026-10-29 — Math Brain restricted arithmetic handler (scoped PASS)
- Added and registered `math`; delegates to the existing strict arithmetic resolver, never `eval`, and fails closed for unsupported/oversized expressions.
- Verification: focused suite **69 passed in 8.28s**; broader suite **82 passed in 6.24s**; changed-file `compileall` and `git diff --check` PASS. Backups: `backups/math_brain_20261029/`.
- Live catalogue coverage: **27/60 implemented, 33/60 unwired**. Scoped PASS only; no P1–P12 gate promotion.


## 2026-10-29 — Language Brain heuristic identification handler (scoped PASS)
- Added and registered `language`, backed by `UniversalLanguageBrain`; returns likely language/script/confidence/mixed-language assessment for supplied text.
- Explicitly does not claim translation or fluent generation; bounded input, existing authorization and verification gates retained.
- Verification: focused suite **77 passed in 5.82s**; broader suite **90 passed in 6.78s**; changed-file `compileall` and `git diff --check` PASS. Backups: `backups/language_brain_20261029/`.
- Live catalogue coverage: **28/60 implemented, 32/60 unwired**. Scoped PASS only; P1–P12 gate statuses unchanged.


## 2026-10-29 — Voice Brain local-component readiness handler (scoped PASS)
- Added and registered `voice`; checks local whisper.cpp ASR executable/model and Piper TTS executable/language-model configuration.
- No microphone capture, audio playback, network upload, or end-to-end voice success is claimed. Physical Android round-trip remains unverified.
- Verification: focused suite **80 passed in 5.35s**; broader suite **93 passed in 6.39s**; changed-file `compileall` and `git diff --check` PASS. Backups: `backups/voice_brain_20261029/`.
- Live catalogue coverage: **29/60 implemented, 31/60 unwired**. Scoped PASS only; P1–P12 gates unchanged.


## 2026-10-29 — Knowledge Brain trust-filtered retrieval handler (scoped PASS)
- Added and registered `knowledge`; delegates to existing persistent Knowledge Brain trust filters (verification lifecycle, conflict and freshness). Defaults to verified-only and validates query/confidence parameters.
- Verification: focused suite **91 passed in 8.82s**; broader suite **104 passed in 9.36s**; changed-file `compileall` and `git diff --check` PASS. Backups: `backups/knowledge_brain_20261029/`.
- Live catalogue coverage: **30/60 implemented, 30/60 unwired**. Scoped PASS only; P1–P12 gate statuses unchanged.


## 2026-10-29 — Vision, Audio, and Web Tools specialists (scoped PASS)
- `vision`: configured local Tesseract OCR on explicit private-capture images, with path/format bounds, source hash and untrusted-text notice. This is OCR extraction, not full semantic vision.
- `audio`: local offline whisper.cpp transcription of bounded PCM WAV inside the configured private capture directory; no microphone capture or network upload.
- `web_tools`: read-only registered Tool Brain candidate discovery; no tool execution or permission grants.
- Verification: combined specialist/security/dispatch suite **99 passed**; changed-file `compileall` and `git diff --check` PASS. Backups: `backups/vision_brain_20261029/`, `backups/audio_brain_20261029/`, `backups/web_tools_brain_20261029/`.
- Live catalogue coverage: **33/60 implemented, 27/60 unwired**. Scoped PASS only; P1–P12 gates unchanged.

## 2026-10-29 — Automation, Health Monitor, and Audit specialists (scoped PASS)
- `automation`: validates up to 30 proposed steps, dependency references and cycles; returns a deterministic proposed order only. No steps are executed or scheduled, and no permissions are granted.
- `health_monitor`: reads the live lifecycle snapshot and emergency-stop latch; an engaged emergency stop reports `CRITICAL`. It does not wake/sleep or modify runtime state.
- `audit`: reads a bounded recent-event window and emits metadata only; request bodies and reason text are omitted. Audit read failures fail closed.
- Verification: focused Master Brain/catalogue/dispatch/security suite **90 passed in 5.77s**; changed-file `compileall` PASS; `git diff --check` PASS. Backups: `backups/automation_health_audit_brains_20261029/`.
- Live catalogue coverage: **36/60 handler-backed; 24/60 unwired**. Scoped specialist PASS only; full repository regression and P1–P12 gates remain unchanged.

## 2026-10-29 — Brain Creator and Evaluation specialists (scoped PASS)
- `brain_creator`: creates a bounded specialist-profile proposal only; detects existing IDs and never registers a role, creates a child, changes the constitution, or grants permissions.
- `evaluation`: evaluates up to 50 caller-supplied check records, reports failed checks and missing evidence, and never claims it executed tests or inspected external state.
- Verification: focused Master Brain/catalogue/dispatch/security suite **92 passed in 9.01s**; changed-file `compileall` PASS; `git diff --check` PASS after normalizing roadmap EOF whitespace. Backups: `backups/brain_creator_evaluation_brains_20261029/`.
- Live catalogue: **38/60 handler-backed; 22/60 unwired**. Scoped specialist PASS only; P1–P12 gate statuses unchanged.


## 2026-10-29 — Personal Assistant, Creative, and Collaboration specialists (scoped PASS)
- `personal_assistant`: validates and priority-sorts up to 25 caller-supplied tasks; no calendar writes, external contact, or task execution.
- `creative`: produces a bounded creative brief and three idea seeds from explicit topic/style/constraints; clearly does not claim to generate a final artifact.
- `collaboration`: aggregates up to 30 supplied specialist reports and flags differing conclusions for the same claim ID; does not silently resolve conflicts or claim truth verification.
- Verification: focused Master Brain/catalogue/dispatch/security suite **95 passed in 9.58s**; changed-file `compileall` PASS. `git diff --check` identified an extra trailing blank line in the roadmap after append; whitespace cleanup is pending before final acceptance.
- Live catalogue: **41/60 handler-backed; 19/60 unwired**. Scoped specialist PASS only; P1–P12 gate statuses unchanged.


## 2026-10-29 — Finance, Localization, Accessibility specialists (scoped PASS)
- `finance`: summarizes caller-supplied income/expense figures with finite/nonnegative bounds; no transactions, credit or investment recommendations.
- `localization`: checks translated-string coverage and `{placeholder}` consistency; does not claim translation quality or perform machine translation.
- `accessibility`: flags missing labels/alt text and unconfirmed keyboard/focus/contrast checks from supplied component metadata; not live UI inspection or WCAG certification.
- Verification: focused Master Brain/catalogue/dispatch/security suite **98 passed in 9.79s**; changed-file `compileall` and `git diff --check` are being finalized with roadmap whitespace cleanup.
- Live catalogue: **44/60 handler-backed; 16/60 unwired** at this checkpoint. P1–P12 gates unchanged.

## 2026-10-29 — Conversation, Policy, Personalization specialists (scoped PASS)
- `conversation`: extracts the latest explicit user turn from bounded supplied history; does not infer intent or persist history.
- `policy`: matches caller-supplied policy rules; unmatched cases default to review, and the handler never grants permission or executes actions.
- `personalization`: validates a small allowlist of explicit task-scoped preferences; no persistent profile write, cross-user sharing, or override of user authority.
- Verification: focused Master Brain/catalogue/dispatch/security suite **101 passed in 9.90s**.
- Live catalogue: **47/60 handler-backed; 13/60 unwired**. Scoped specialist PASS only; no P1–P12 gate promotion.

## 2026-10-29 — Final specialist catalogue wiring checkpoint (scoped PASS)
- Added and registered the final specialist handlers: `api_integration`, `devops_deployment`, `multimodal_coordination`, `notification_events`, `compliance`, and `experiment_benchmark`. Each is a bounded proposal/metadata-analysis path only; no network requests, credentials, deployments, notification delivery, legal certification, or experiment execution occur.
- The preceding checkpoints in this session also registered `recovery`, `knowledge_graph`, `database`, `scheduling`, `ui_ux_design`, `scientific_research`, and `simulation`.
- Verification: focused Master Brain/catalogue/dispatch/security regression **114 passed in 10.61s**; final changed-file compile and diff checks run after this roadmap update.
- Live catalogue: **60/60 catalogue roles have registered handlers; 0 unwired catalogue roles**. `reasoning` remains an explicit alias for catalogue role `thinking`; the live internal registry has 60 role entries.
- Scope caveat: this is handler-wiring coverage, not proof that every specialist has a production-grade backend. Several handlers intentionally perform bounded supplied-data review/proposal only. Full repository regression, physical Android voice round-trip, and P1–P12 phase gates remain separate and are NOT marked PASS by this checkpoint.

## 2026-10-29 — Full software regression and pytest discovery fix
- First unscoped `pytest -q` exposed collection errors because preserved `backups/` directories contained duplicate test module basenames. No backup was deleted.
- Added root `pytest.ini` with `testpaths = tests` and `norecursedirs = backups .git .venv` so backups and the virtual environment are not treated as active test suites.
- Full repository test suite: `.venv/bin/python -m pytest -q tests/` — **2169 passed in 221.05s**.
- Default pytest collection after config: **2169 tests collected in 4.02s**, exit 0; no backup import mismatch.
- `compileall` for `core` and `tests`: PASS. `git diff --check`: PASS.
- Live Specialist Catalogue: 60 total, 60 handler-backed, 0 unwired.
- This is a software regression PASS for the current test suite, not an automatic P1–P12 gate PASS. Physical Android voice round-trip and production-backend/end-to-end checks remain separate.

## 2026-10-29 — P7 live local OCR diagnostic (no gate promotion)
- Read-only probe of the existing `data/ocr_acceptance/` fixtures through installed Tesseract confirmed available languages `eng,hin`.
- Real OCR on `synthetic_english.png`: mean confidence 32.1; extracted text was noisy (`SHHIEEx EFAIM TEST HIMOL EMGLISH 1:XZ=45`); `VisionOCRPipeline` correctly rejected it below the 35 confidence threshold.
- Real OCR on `safe.png`: confidence 53.48 but only `= P`; the meaningful-character gate correctly rejected it. This demonstrates that confidence alone is insufficient and the fail-closed gate should not be weakened to force a PASS.
- `VisionOCRPipeline` remains an OCR/provenance adapter into a contract-only observation object; no semantic image model or actual camera capture path was found in `VisionReasoningIntegration`. P7 remains PARTIAL; representative Hindi/English corpus, image-understanding model integration and consented capture acceptance remain open.
- Evidence: `logs/p7_live_tesseract_quality_probe_20261029.md`. This is a diagnostic checkpoint only; no P-series gate status promoted.

## 2026-10-29 — P6 voice runtime availability probe (PENDING, no device gate promotion)
- Read-only health probes to loopback ports 38741 and 38742 returned HTTP 000 / connection refused; no media bridge process was present. `adb devices -l` returned an empty device list.
- No service was started, no pairing token was read, and no device permission was changed during this probe.
- P6 remains PARTIAL: existing software/ASR/TTS checks are distinct from a running authenticated bridge and the physical microphone → ASR → confirmed transcript → Main Brain → audible TTS flow. Next required evidence is a safe bridge start/health check, then user-authorized Companion pairing and physical acoustic acceptance when a device is available.
- Current environment memory snapshot: 1.8 GiB available, 3.3 GiB swap free; this is transient diagnostic data, not a capacity guarantee.


## 2026-10-29 — SAHIBEX Brain Frontend v0.3.0 (scoped build PASS; device acceptance pending)
- Preserved the pre-change `MainActivity.java`, theme, and Gradle file under `backups/frontend_redesign_20261029/`. No pre-existing backup or build directory was deleted.
- Redesigned the existing Android Companion screen with a dark SAHIBEX identity, animated lightweight neural-core visualization, chat transcript, multiline typing composer, Send action, and voice control next to typing.
- Added typed-message transport to the existing authenticated loopback `/voice` bridge; response and failure status render in chat. Existing pairing, emergency-stop, screenshot and full-device-test controls remain.
- Updated project version to versionCode 8 / versionName 0.3.0. Manual build was used instead of a legacy script that removes its existing `build-media` directory.
- Verification: javac, D8, AAPT2 compile/link, package metadata, APK v3 signature verification, frontend static checks and `git diff --check` all PASS. APK SHA-256: `35171396f1125e6f9d4727d1740e2ab74b803b490b62448314868378519875e8`. Evidence: `logs/sahibex_frontend_redesign_20261029.md`.
- Device acceptance remains PENDING: no device appeared in `adb devices -l`; bridge was not started; physical install, typing-to-brain E2E and audible reply were not verified. Camera preview, semantic vision, motion/gesture recognition, true 3D avatar and lip-sync are still not implemented. This is a scoped frontend build PASS only; no P6/P7 or other P-series gate is promoted.


## 2026-10-29 — SAHIBEX Frontend v0.3.1 follow-up (scoped build PASS; device acceptance pending)
- Extended v0.3.0 with a dedicated CameraConversationActivity, explicit runtime CAMERA permission, front-camera-preferred live preview and local low-resolution frame-difference motion meter. It detects generic frame changes only; it does not claim identity, body-pose or gesture recognition.
- Added the CAM control beside typing/voice and guarded camera startup against an uninitialized background thread. Updated version to code 9 / 0.3.1.
- Build checks: Java compilation (including camera activity), D8, AAPT2 compile/link, APK metadata and v3 signature verification PASS. `git diff --check` PASS. APK SHA-256: `52b9c7641a225ad7221fddbfd683b4f3d7c961f457c192369537b590384fe477`. Evidence: `logs/sahibex_frontend_redesign_20261029.md`.
- `adb devices -l` still reports no attached device. Live camera, permissions, typed chat to a running bridge and audible reply have not been physically verified. True 3D avatar, semantic vision relay, pose/gesture recognition and avatar lip-sync remain pending. P6/P7/P-series gates are not promoted. This supersedes the frontend scope notes in the preceding v0.3.0 checkpoint.


## 2026-10-29 — Frontend packaging polish (same v0.3.1 scope)
- Added the custom vector neural-core launcher icon and renamed the app label to `SAHIBEX — Master Brain`. Manifest/resource rebuild and APK signature verification PASS.
- Final artifact: `android_companion/manual-build/SAHIBEX-Frontend-v1.4-debug.apk`; SHA-256 `9e65787dea8e324b61cd29fbecca0407b0db8268c76b7acf5a1e6089d0f7e143`. Device E2E remains pending; no P-series gate promotion.


## 2026-10-29 — Frontend v0.3.2 camera OCR bridge (software PASS; live/device acceptance pending)
- Added authenticated `POST /vision/ocr` with strict base64 parsing, request/image bounds, language allow-list, private temporary image, existing OCR quality/provenance pipeline, and explicit untrusted OCR output. It is OCR-only, not semantic vision.
- Added a deliberate one-frame camera action to the non-exported CameraConversationActivity; sends a still only after user taps Analyze, with bearer auth, and renders OCR result/failure. No continuous frame upload.
- Focused tests 28 passed; full repository regression 2172 passed in 182.78s; compileall/static checks/git diff check PASS. APK v0.3.2 / code 10 signature verification PASS. Evidence: `logs/sahibex_frontend_redesign_20261029.md`. APK SHA-256 `c27a0a035d69837b7a641e83c7492d271e6ab87e85a6f56abc3ef7dd8c560b51`.
- No Android device attached; local media bridge was not started because explicit approval for service startup remains unconfirmed. Physical camera OCR and typing/voice end-to-end remain pending. Semantic vision, true 3D avatar, lip-sync and motion/gesture understanding remain incomplete. No P6/P7/P8/P-series gate promotion.


## 2026-10-29 — Local media bridge startup and security smoke test
- User explicitly approved startup. Ran `scripts/start_sahibex_media_bridge.sh`; result `SAHIBEX MEDIA BRIDGE: ONLINE`. `/health` returned HTTP 200 with service `sahibex-media-bridge`, host `127.0.0.1`, port `38742`.
- Unauthenticated POST checks to `/synthesize` and `/vision/ocr` both returned HTTP 401. No token value was displayed or copied into chat. Bridge binds to loopback only; protected actions remain separately permission-gated.
- Live typed-chat/audio and camera OCR round trips are not yet verified: Android ADB lists no attached device and app has not been paired on-device. User must enter the private token into the Companion pairing field from the Termux-local token file; do not paste it into this chat.

## 2026-10-29 voice quality correction checkpoint
- Completed software correction: normalized local neural WAV playback level (bounded 85% peak target, 8x maximum gain, silence and clipping guards); removed automatic Android TTS fallback to prevent unexpected voice/accent switching; Companion v0.3.3 APK built and signature-verified.
- Focused verification: 26 passed. Hindi and English local neural WAV smoke tests valid, 44.1 kHz, zero clipped samples; generated peak normalized to 27,852/32,767.
- **Still pending:** real physical phone listening acceptance, Hinglish pronunciation quality, and any custom voice identity based on a consented supplied sample. P6 remains PARTIAL; do not mark any P-series gate complete from this software-only evidence.


## 2026-10-29 — Feminine persona language consistency (scoped software checkpoint)
- Updated central model instructions and deterministic Hindi/Hinglish responses to use feminine first-person grammar for SAHIBEX; English persona is female-presenting without gender stereotypes. Added targeted regression coverage.
- Acoustic voice gender/style mapping and physical phone listening remain PENDING; this text/persona change does not certify the TTS speaker as female. No P-series gate promotion. Evidence: `logs/feminine_persona_language_fix_20261029.md`.


## 2026-10-29 deterministic identity fast-path checkpoint
- [x] Added deterministic female-persona identity response for direct “tum kaun ho / who are you” questions; no LLM required.
- [x] Focused tests 8/8 PASS; full regression 2180/2180 PASS; compileall and `git diff --check` PASS.
- [ ] Pending: reload the live SAHIBEX runtime and confirm the same prompt through the user-facing app. Local model was OFFLINE during diagnosis; this bounded identity fix does not verify general model availability or acoustic voice gender.



## 2026-10-29 — Frontend ↔ backend typed-chat connection audit (bounded PASS / E2E pending)
- Audited Android typed-chat code and bridge response contract: client posts JSON `text` to `http://127.0.0.1:38742/voice` with bearer pairing token; client reads `message` and `success`, matching the bridge response fields. Existing connect/read timeouts are 3s/180s.
- Restarted the stale bridge process after the identity fast-path source change. Live authenticated identity probe: HTTP 200, `success=true`, intent `explain`, `STRUCTURALLY_VALID`, feminine Hinglish response (4.716s). Pairing token not exposed.
- Focused tests: 22 passed in 3.77s; Python compile and `git diff --check` PASS.
- **Open defects/limits at initial audit:** local model health on port 8080 was OFFLINE; supervisor PID/lock pointed to dead PID 14393; bridge recovery had not yet been verified. The follow-up correction below resolves supervised bridge recovery without launching the low-RAM fallback. Physical Android UI result/audio and general model-dependent answers remain PENDING/BLOCKED. No P-series gate promotion.
- Evidence: `logs/identity_fastpath_fix_20261029.md`; pre-edit copies in `backups/frontend_bridge_audit_20261029_225353/`.

- **Follow-up recovery fix (2026-10-29):** Added opt-in `SAHIBEX_SUPERVISOR_MODEL_AUTOSTART=0` mode to keep bridge recovery active without silently launching Qwen3-1.7B. Started supervisor in this mode (PID in `logs/supervisor.pid`); controlled test stopped bridge PID 21055 and supervisor recovered bridge PID 4730; `/health` PASS. Model remains OFFLINE by design. Shell syntax and `git diff --check` PASS. Android screen E2E/audio still PENDING.


## 2026-10-30 — Text/Development Brain foundation (scoped software checkpoint)
- Added `core/brain/text_development_brain.py` and registered `text_development` as a new internal role (61 roles total). It creates size-bounded, SHA-256-fingerprinted candidate records under `data/development_lab/candidates/` only.
- The role requires existing upstream authorization + request verification. Mother integration returns a review status; Python candidates receive static review through Coding Brain. No candidate is auto-approved or promoted.
- Safety contract: no candidate execution, package installation, model download/training, credential access, network access, production source mutation, constitution modification, or self-authorized promotion. Static review PASS does not equal test/regression PASS.
- Added model/privacy/resource design register at `docs/architecture/SAHIBEX_MODEL_AND_TEXT_DEVELOPMENT_BRAIN_2026-10-30.md`. Qwen3-VL-8B remains NOT DOWNLOADED / NOT CONNECTED because current phone RAM and vision runtime compatibility have not been verified. Local language model remains OFFLINE by deliberate resource/quality guard; no guard bypassed.
- Scope gate is not P1–P12 promotion. Pending: focused + full regression, candidate tamper/size/path checks, persistent review lifecycle, isolated staging promotion/atomic rollback implementation, live model feasibility, physical Android voice/vision acceptance.

### Final verification addendum — 2026-10-30 (Text/Development Brain foundation)
- [x] Pre-change backup created: `backups/user_learning_text_brain_20261030_001239/` (roadmap, supervisor, Master Brain, internal role registry, specialist catalogue and relevant tests preserved before their edits).
- [x] Added and wired `TextDevelopmentBrain` as internal role `text_development`; specialist catalogue now contains **61 roles**, **61 runtime handlers registered**, **61/61 catalogue roles implemented**, **0 missing/unwired**. This is handler coverage, not a claim that every worker is continuously executing or that every external capability is active.
- [x] Candidate queue uses bounded inputs, SHA-256 content fingerprints and atomic temp-file publication under `data/development_lab/candidates/`. Candidates start `PROPOSED_PENDING_MOTHER_REVIEW`; no candidate executes, installs packages, downloads/trains models, reads credentials, uses network, changes production files or changes Constitution.
- [x] Mother integration performs static Python review when the candidate type is Python. Live smoke with a valid Python candidate returned `STATIC_CHECK_PASSED`, while `promotion_allowed=false` and `production_changed=false` remained enforced. Static review alone is not security/test/regression approval.
- [x] Model registry and privacy/resource plan recorded in `data/development_lab/model_registry.json` and `docs/architecture/SAHIBEX_MODEL_AND_TEXT_DEVELOPMENT_BRAIN_2026-10-30.md`.
- [x] Focused final tests: **107 passed** after input-validation/atomic-write hardening; focused brain/catalogue/learning tests earlier passed 118/118 before the last hardening change.
- [x] Final full regression after all code changes: `.venv/bin/python -m pytest -q tests/` — **2183 passed in 216.46s**, exit 0.
- [x] `compileall core tests`, model-registry JSON validation, shell syntax checks for supervisor/model/background launchers, and `git diff --check`: PASS.
- [x] Live runtime checks: media bridge `/health` HTTP 200; Text/Development dispatch and Mother static review smoke PASS; role registry count assertion PASS.
- [ ] Local language model remains **OFFLINE** on port 8080 by design/resource guard. Snapshot showed ~2.4 GiB available RAM versus 3 GiB default start threshold. Do not bypass guard or auto-start the known weak 1.7B fallback.
- [ ] Qwen3-VL-8B is **NOT DOWNLOADED / NOT CONNECTED**. Vision runtime/projector compatibility, storage/RAM budget and image acceptance corpus remain pending. Speech physical mic-to-speaker E2E also remains pending.
- [ ] Automatic production promotion/rollback orchestrator is not implemented by the new Text Brain; the current module intentionally only queues candidates and blocks self-promotion. Next work must build and test isolated staging, security/regression gates, human approval for protected changes, atomic promotion, health acceptance and verified rollback before any live code replacement.
- [ ] Internet learning is not an unrestricted always-on code updater: research must remain source-verified and task/resource bounded. Worker roles are available on demand; continuous full-time execution of every worker is neither implemented nor safe on the phone's resource budget.
- **Gate decision:** scoped Text/Development Brain foundation = **PASS**. P1–P12 status is **unchanged**; no broader production, model, physical-device, or P-series gate is promoted by this checkpoint.


## 2026-10-30 — Development/Test/Library Brain bounded implementation checkpoint

- PASS: Test Brain added for non-executing candidate hash integrity and Python syntax checks; it cannot execute, test-run, or promote candidate code.
- PASS: Library Brain added for local allowlisted catalogue with source/licence/hash metadata; entries default to UNVERIFIED and `trusted_for_training=false`.
- PASS: Wired through existing `testing` and `knowledge` roles; internal role count remains 61 (no duplicate roles).
- PASS: focused integration suite 99 passed; learning/knowledge/model suite 122 passed; compileall and diff whitespace checks passed.
- BLOCKED: model server is offline; no `llama-server` executable found on PATH. Existing Qwen3-1.7B and Qwen3-4B files remain not autostarted; Qwen3-VL-8B not downloaded.
- PENDING: real Vision model/projector, physical voice round-trip, Native Model training, full regression and remaining P-series gates. No P-series gate promoted by this checkpoint.
- Log: `logs/development_library_brains_implementation_20261030_072504.md`. Backup: `backups/brain_expansion_20261030_072504/`.
