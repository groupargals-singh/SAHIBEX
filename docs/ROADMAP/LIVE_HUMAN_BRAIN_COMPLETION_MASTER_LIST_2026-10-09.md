# SAHIBEX LIVE HUMAN-BRAIN AI — ORDERED COMPLETION MASTER LIST
Date: 2026-10-09

## Mission and honest definition
Bring the current SAHIBEX engineering system into the most complete, verified live operation possible. "Human-brain AI" is the product goal; it is not a claim of consciousness or biological equivalence. Completion is based on working integration, evidence, security, and real-device tests—not merely files or contract tests.

## Current baseline (verified this session)
- Local Qwen3 1.7B model: ONLINE at localhost:8080.
- Web research: ACTIVE; runtime reports direct_web, document, rss_atom, search.
- Background supervisor: ONLINE.
- Full Python regression before latest adapter-only test additions: 1136 passed.
- New Android media adapter/security subset after fixes: 11 passed.
- Compileall and `git diff --check`: PASS.
- Android media adapter exists at `core/brain/android_media_runtime.py` and enforces per-operation consent.
- The adapter's TTS integration bug was fixed: `termux-tts-speak` receives text through stdin (the documented interface), and timeout cleanup kills the full child process group.
- Native Android Companion voice UI and authenticated local relay have now been implemented and built as `android_companion/manual-build/SAHIBEX-Android-Companion-Voice-debug.apk` (versionCode 4, versionName 0.2.0).
- The live localhost relay E2E request returned HTTP 200 / SUCCESS / VERIFIED using the real MasterBrain and local model. A SQLite thread-affinity error was found and fixed by moving production HTTP handling to a single thread; the E2E request then passed.
- The updated APK is copied to `/sdcard/Download/SAHIBEX-Android-Companion-Voice-debug.apk`. The installed app is still versionCode 3; Android install/update and voice UI hardware acceptance require a human tap/permission.
- Live TTS/camera API calls still time out. `pm list packages` shows `com.termux` but no `com.termux.api`; the installed Termux/API combination is not currently responding to API commands. The official F-Droid API APK signer was verified to mismatch the installed Termux signer and was not installed. Do not call voice or camera live until fixed and tested.
- Only Qwen3-1.7B text GGUF is present in `~/models`; a live multimodal vision model is not installed.
- Companion APK exists, but Android Accessibility service must be enabled/verified by a user on the device.
- Historical exact 417-item requirement source remains unavailable. Do not fabricate 417 line items or an exact completion ratio.

## Ordered work queue (do not skip order)

### 0. Protect current working state — COMPLETE
- Keep existing Constitution, permission, authority, audit, prompt-injection, and protected-tool boundaries intact.
- Do not overwrite project state or claim a clean Git tree without evidence.

### 1. Stabilize Android media adapter — COMPLETE (software tests)
- Add consent-gated Termux media runtime.
- Use no shell interpolation; enforce command timeout and terminate child process groups.
- Correct TTS stdin handling.
- Dedicated adapter/bridge/security subset: 11 passed.
- Remaining: actual Android service must respond to real media commands.

### 2. Resolve Termux/API compatibility — ORIGINAL API BLOCKED; NATIVE COMPANION ROUTE BUILT
- Confirm exact Termux distribution and compatible API implementation.
- Install/enable only the compatible official API service if required; do not mix incompatible APK signatures/distributions.
- Check Android app permissions for microphone/camera and confirm TTS engine is available.
- Compatibility finding: installed Termux is v0.118.3 signed with a custom `APK Signer / Earth` certificate; the official F-Droid Termux:API APK is signed with the F-Droid certificate. They do not match. **Do not install that APK over this setup**: Android requires matching signatures and switching Termux sources can require uninstalling Termux, risking the SAHIBEX project/model data. The downloaded APK was verified and then removed without installing it.
- Native Companion voice route is now implemented: Android speech recognition → authenticated localhost relay → existing MasterBrain → response → Android TextToSpeech. Backend live E2E passed. Camera is not yet wired.
- The remaining activation step is to update the installed Companion from versionCode 3 to versionCode 4, paste the private pairing token, grant speech permission if requested, and run a real spoken round trip. See `android_companion/VOICE_PAIRING.md`.
- Run bounded, explicit-consent smoke tests; no indefinite API command may be left hanging.
- Evidence required: TTS returns successfully; speech-to-text produces recognized words; camera returns a non-empty image; all timeouts and failures clean up child processes.

### 3. Voice input/output end-to-end — SOFTWARE PATH PASS; DEVICE ACCEPTANCE PENDING
- Native Android speech UI and TTS playback code built and signature-verified.
- Real MasterBrain HTTP relay E2E: HTTP 200 / SUCCESS / VERIFIED.
- Still required: install/update Companion, enter token, and verify an actual microphone speech → brain response → speaker playback round trip on the phone.
- Validate silence, cancellation, timeout, empty transcript, Hindi/English, permission denial, and recovery.
- Keep microphone/speaker access opt-in; never record in background without clear consent.

### 4. Camera acquisition and image understanding — PENDING
- Obtain a real camera image with consent and verify size/hash/MIME.
- Add a real OCR and/or compatible image-understanding model path; do not send images to the text-only Qwen model as if it could see them.
- Validate unreadable/oversized/malformed images, privacy-safe temporary storage, and deletion policy.
- End-to-end: camera/image -> visual extraction -> grounded response with uncertainty.

### 5. Android Companion Accessibility bridge — PENDING DEVICE ACTION
- Install/replace the current Companion APK only through an authorized Android install flow.
- User enables the SAHIBEX Accessibility service in Android settings.
- Run the in-app Phase 6B full device test and secure screenshot test.
- Confirm UI tree, tap, typing, key press, screenshot, emergency stop, audit, and permission denial on the actual device.
- Do not use the old E2E evidence as proof of current device activation.

### 6. Specialist Child Brain live deployment — PENDING FINAL RUNTIME EVIDENCE
- Create at least one real specialist instance through the existing Mother Brain manager.
- Verify identity/parent binding, isolated memory, capability profile, lifecycle, trust, suspension/restart, and retirement.
- Confirm children cannot grant authority, bypass permission, or modify Constitution.

### 7. Controlled self-improvement live commissioning — PENDING FINAL RUNTIME EVIDENCE
- Run a complete proposal -> test -> security review -> explicit approval -> activation -> observation -> rollback cycle.
- Use a reversible harmless test skill only; no uncontrolled code execution or self-authorization.
- Prove failed validation prevents activation and rollback restores the prior trusted version.

### 8. Security/adversarial regression — PENDING FINAL GATE
- Test prompt injection, hostile documents/search results, path traversal, secret leakage, replay, unauthorized network/write/delete/execute, child privilege escalation, emergency stop, corrupt checkpoints, and memory amplification.
- Protected actions must remain blocked without explicit authorization and required confirmation.
- Save test output/evidence and fix every failure before proceeding.

### 9. Recover/reconstruct the requirement baseline — PARTIAL / SOURCE GAP
- Search local repository, Git history, and known backups for the original 417 items.
- If the original cannot be recovered, create a separately labelled reconstructed baseline with traceable sources and user approval; never present it as the exact historical original.
- Map every item to implementation, integration, dedicated test, security evidence, live evidence, and status.
- Reconcile G/K/T/U/V/AC and 6P-13..29 without inventing official phases.

### 10. Final LIVE-BRAIN acceptance — NOT STARTED
- Run a real command end-to-end: input -> intent/context -> memory -> reasoning -> plan -> permission -> tool -> observation -> verification -> recovery if needed -> response -> audit.
- Run the same flow with a research task, a protected action denied without permission, an authorized harmless write/read/delete test, and a specialist child task.
- Include voice and vision in the acceptance suite only after their hardware/model paths are proven live.
- Run full tests, compileall, diff check, model health, web search health, supervisor health, and record exact outputs.

### 11. Publish completion report — FINAL STEP
- Report engineering readiness separately from exact requirement coverage and actual hardware feature status.
- Give evidence-based percentages only; never equate passing unit tests with human-like consciousness.
- Mark each work item COMPLETE only with its required evidence.

## Current progress policy
- Engineering readiness estimate remains approximately 85% until the new native Companion is installed and real voice E2E passes.
- 29 architecture checkpoint coverage: 23/29 (79.3%) have checkpoint evidence; G/K/T/U/V/AC need specification reconciliation.
- Exact 417-item completion percentage: NOT CLAIMABLE while the source baseline is unavailable.
- Voice/vision: NOT LIVE yet; Termux media CLI commands currently time out.
- Local text model and web research: LIVE.

## Next immediate action
Resolve the Android Termux API compatibility/service issue before attempting camera/voice E2E again. The previous TTS hang was also caused by incorrect stdin handling in the adapter; that code defect is fixed and regression-tested, but the device API itself remains unresponsive.

## Latest verification update — 2026-10-09
- Full repository regression after TTS stdin and process-group timeout fixes: **1138 passed, 0 failed**.
- `python -m compileall -q app core security verification tools tests`: PASS.
- `git diff --check`: PASS after removing trailing blank lines from the status board.
- Live model health: ONLINE; web research: ACTIVE; supervisor: ONLINE.
- Re-tested real TTS with correct stdin handling and a 5-second timeout: **still timed out**. The Android API service remains unresponsive; do not mark voice live. No TTS child process remained after timeout cleanup (only the Termux API client/daemon process was visible).

## API compatibility investigation — 2026-10-09
- Installed Termux APK: version `0.118.3`, signing certificate SHA-256 `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1`.
- Official F-Droid Termux:API 0.53.0 APK signing certificate SHA-256 `228fb2cfe90831c1499ec3ccaf61e96e8e1ce70766b9474672ce427334d41c42`; mismatch confirmed.
- Official API client documentation says the add-on must use the same signing key as the main Termux app. Therefore the downloaded official APK was **not installed** and then deleted. This avoids risking an uninstall/source switch that could remove SAHIBEX and its local model.
- Preferred implementation path: add native Android media APIs to the separate SAHIBEX Companion app and connect it to a permissioned localhost relay, rather than force-installing an incompatible add-on.

## Latest completion sequence update — 2026-10-09
- Full repository regression: **1143 passed, 0 failed**.
- Compileall, shell syntax checks, and `git diff --check`: PASS.
- Native Companion voice APK built and signed; versionCode 4 / versionName 0.2.0. Installed Companion remains versionCode 3, so update not yet confirmed.
- Local voice relay is running under the supervisor and reports process online. Real request through the relay reached the real MasterBrain/local model and returned `SUCCESS / VERIFIED`.
- Fixed real bug: a threaded media server reused SQLite storage created on another thread. Production server now handles requests on a single thread; live relay E2E passes.
- Remaining immediate user action: install the staged APK from Downloads, copy `cat ~/SAHIBEX/data/android_companion_media_token` into the Companion pairing field, and complete a spoken round-trip test. Camera/vision, live child-brain/self-improvement commissioning, adversarial gate, and exact 417 reconciliation remain open.


## Restarted work session update — 2026-10-09 (latest)

- Re-checked live health: local model ONLINE; web research ACTIVE; background supervisor remains expected online; media bridge `/health` responds HTTP 200.
- Full regression after the current bridge changes: **1143 passed, 0 failed**.
- Android media bridge focused suite: **13 passed**; compileall and `git diff --check` pass.
- Fixed bridge SQLite thread-affinity hazard: production now uses a `ThreadingHTTPServer` with a thread-local `MasterBrain`/SQLite connection per request, so one long brain request cannot block `/health`; tests may still inject a fake brain. Client disconnects are handled without attempting a second response.
- Corrected stale PID handling manually: an old media bridge process was still serving stale code; stopped that exact Python server process and restarted from current source. `/health` now returns service identity from the restarted bridge.
- After removing the stale server process and restarting the current threaded bridge, live `/voice` end-to-end probe passed: **HTTP 200, success=true, verification=VERIFIED**, response 189 characters. The local-model request took about 48 seconds on this device; performance optimization is still needed. Earlier false/failed probes were caused by stale server code and too-short probe lifetimes, and are not counted as the final successful run.
- Voice app activation is still a user/device step: install/update `android_companion/manual-build/SAHIBEX-Android-Companion-Voice-debug.apk`, open app, pair using the private token file, then test real microphone + spoken response. Do not paste the token into chat.
- Vision remains pending: only a text GGUF is installed; no live image understanding path. Accessibility device E2E still needs user-enabled service and test.

### Remaining ordered queue (live state)
1. **Voice relay live request success/latency** — PASS; authenticated relay-to-MasterBrain E2E is 29.12 seconds after prompt-budget optimization. Physical phone voice acceptance remains pending.
2. **Phone Companion update + pairing + microphone/TTS** — WAITING FOR USER TAP/PERMISSION; current APK is staged in Downloads and hash-matches the project build.
3. **Vision** — PENDING camera acquisition, OCR/multimodal model, and E2E.
4. **Accessibility bridge** — PENDING on-device service activation and E2E.
5. **Specialist child-brain live instance** — Mother-owned in-process lifecycle commissioning PASS; persistent instance/restart acceptance still pending.
6. **Controlled self-improvement** — Mother-owned metadata-only proposal/test/approval/activation/rollback commissioning PASS; persistent audit and production integration remain pending.
7. **Adversarial security acceptance** — focused security/adversarial set 75 PASS; final cross-component live acceptance remains pending.
8. **417-source reconciliation** — original exact source still unavailable; reconstructed matrix is not the original.
9. **Final LIVE-BRAIN acceptance + honest progress report** — PENDING until device and remaining cross-component gates have evidence.


## Latest live voice relay acceptance — 2026-10-09
- Current bridge restarted from current source; `/health` returns HTTP 200.
- Real authenticated request traversed the bridge into the local MasterBrain and returned **HTTP 200 / success=true / verification=VERIFIED** (189 response characters).
- Current end-to-end model latency: approximately 48 seconds. Android UI read timeout is configured for 180 seconds.
- This confirms the Termux relay-to-brain path, not yet the actual physical phone microphone/speaker UI. User must update/install the voice Companion APK and pair it once, then speak a harmless test and confirm audible output.


## Engineering continuation update — 2026-10-09

- Restored the local llama.cpp model after finding it offline. Re-started the Android media relay from current source and re-enabled the background supervisor. Current checks: local model ONLINE, web research ACTIVE, bridge `/health` HTTP 200, supervisor PID alive.
- Reduced local-model cognitive context caps from 3500/1500 characters to 900/350 after the real phone-class inference path exceeded the 60-second probe timeout. The new authenticated bridge-to-MasterBrain E2E completed in **29.12 seconds**: HTTP 200, `success=true`, `verification=VERIFIED`, 189 response characters. This is relay-to-brain evidence, not yet physical phone microphone/speaker evidence.
- Fixed an additional bridge defect: a cancelled client could disconnect during response headers and emit a `BrokenPipeError` traceback. Header and body writes are now guarded; a dedicated regression test covers this case.
- Full repository regression after the runtime changes: **1145 passed, 0 failed**. Focused security/adversarial set: **75 passed**. Focused model/context/media set: **11 passed** before the new targeted regression additions; the latest context + media tests are **9 passed**. `compileall`, `git diff --check`, and health checks pass.
- Ephemeral specialist-child runtime commissioning: **PASS** for unauthorized birth denial, Mother + human approved birth, root-parent binding, verified trust, isolated child memory, Mother-private memory denial, safe specialist dispatch, activate/suspend/resume/retire lifecycle, and child authority/Constitution boundary. This is in-process commissioning evidence, not a persistent production child deployment.
- Ephemeral controlled-improvement commissioning: **PASS** for proposal, security/regression/verification gates, unapproved activation denial, Mother + human approval, activation of a harmless metadata-only skill version, activation of a second version, and verified rollback to version 1. No live code was executed or changed by this test; persistent audit/production integration remains pending.
- Searched the project/home files and Git history for the original 417-item requirement source; only the reconstructed audit matrix was found. Exact historical 417-item completion remains NOT CLAIMABLE. Do not relabel the reconstructed matrix as the original.
- Still requires user/device interaction: install/update the staged Companion APK, pair using the private token file (never paste the token into chat), and verify actual microphone input plus audible TTS. The phone's Accessibility service must be enabled and its Phase 6B full-device test run. Vision is not live: no OCR package or multimodal image model is installed; camera capture alone would not be image understanding.
- Remaining final gates: actual phone voice E2E; camera/OCR or multimodal vision E2E; Accessibility E2E; persistent child-brain deployment; production-grade self-improvement/audit evidence; final adversarial end-to-end gate; 417 source reconciliation or user-approved reconstructed baseline; final LIVE-BRAIN acceptance.

## Honest progress status

- Engineering readiness estimate remains approximately **85%** because device-side voice activation, vision, Accessibility activation, and final end-to-end acceptance are still unverified.
- 29 architecture checkpoints: prior evidence remains **23/29 (79.3%)**, with G/K/T/U/V/AC requiring specification reconciliation.
- Exact 417-item coverage percentage remains **NOT CLAIMABLE** until the original source or an explicitly approved reconstructed baseline is available.


## Latest verified acceptance update — 2026-10-09

- After adding two regression tests (small phone-local prompt budget and disconnected-client header handling), full repository regression is now **1147 passed, 0 failed**.
- `python -m compileall -q app core security verification tools tests`: PASS.
- `git diff --check`: PASS.
- `scripts/sahibex_health.sh`: local model ONLINE; web search ACTIVE; Android voice bridge HTTP HEALTHY. Background supervisor PID is alive.
- Re-ran authenticated live voice relay after prompt-budget optimization: **HTTP 200, success=true, verification=VERIFIED, 189 response characters, 29.12 seconds total**. The previous 60-second timeout no longer reproduces in the latest probe. Real phone microphone/speaker acceptance is still not claimed.
- Re-ran child and controlled-improvement commissioning through the **actual `MasterBrain`-owned** `specialist_child_brains` and `continuous_learning` runtime objects: child lifecycle PASS; unapproved self-update activation denied PASS; harmless metadata-only version activation and verified rollback PASS. This is runtime-object commissioning in a test process; no production child or executable code update was persisted.
- Security/adversarial focused set: **75 passed**. New focused context/media tests: **9 passed**.
- The current versionCode 4 / versionName 0.2.0 voice APK is already present in Android Downloads and its SHA-256 exactly matches the staged project APK. No token or secret was exposed. The user still needs to tap-install/update the APK and perform the physical voice test.


## Live engineering continuation — 2026-10-09 (answer-quality regression)

- Added conservative joined-request coverage to `core/brain/answer_quality.py`: obvious multi-part questions can now be rejected if an explicit joined clause is missing from the response. The gate also rejects prompt echoes, internal context leakage, repetitive output, and obvious truncated responses. These are quality heuristics, not a factual truth proof.
- Fixed an observability bug in `core/brain/master_brain.py`: when operational output is rejected, the failed BrainResult now retains decision-context and operational-provider diagnostics rather than returning an empty metadata object.
- Updated tests that previously treated the mock provider's prompt echo as a successful answer. The mock response is synthetic test output and must not be presented as a real answer; those tests now expect `QUALITY_REJECTED` while verifying routing, planning, memory retrieval, and diagnostics.
- Full pytest regression with project import path: **1165 passed, 0 failed** after the final test correction.
- Python compileall: PASS. `git diff --check`: PASS.
- Live health re-check: local model ONLINE; web search ACTIVE; after restarting the stopped bridge, Android voice bridge HTTP HEALTHY.
- Live smoke: simple curated Hindi sky question returns `STRUCTURALLY_VALID` in about 0.2s. A compound capital+history answer that ended mid-sentence is now rejected with `QUALITY_REJECTED`. Fresh web research still stops at the explicit `NETWORK_ACCESS` confirmation gate; this is intended security behavior, not a bypass target.
- Remaining work is unchanged in principle: physical Companion install/pair/microphone/TTS acceptance; camera + OCR/multimodal vision; Accessibility device acceptance; persistent specialist child deployment; production self-improvement audit/rollback evidence; final adversarial end-to-end acceptance; reconcile or obtain approval for the reconstructed requirements baseline; final LIVE-BRAIN acceptance.
- Exact historical 417-item source remains unavailable; no 417/417 percentage is claimed. The reconstructed matrix is not the original source.


### Final checks from this continuation — 2026-10-09

- Re-ran the full collected regression after the decision-context test correction: **1165 passed, 0 failed**.
- Re-ran the manual Master Brain commissioning script with the local provider explicitly selected: **PASS** for general reasoning plan, research permission boundary, coding plan, protected-action denial, critical system-change denial, empty request, Constitution immutability, and context integration.
- Final live quality smoke: curated Hindi sky answer accepted as `STRUCTURALLY_VALID`; truncated compound capital/history answer rejected as `QUALITY_REJECTED`; current-news research blocked until explicit network permission is confirmed.
- Local model ONLINE; web search ACTIVE; Android voice bridge HTTP HEALTHY after restart. Compileall and `git diff --check` PASS.


## Follow-up engineering pass — 2026-10-09 (research result integrity)

- Found and fixed a real research integration defect in `core/brain/mother_research_integration.py`: `ResearchAnswerPipelineResult.answer` is a nested `ResearchAnswer`, but the integration was stringifying that object instead of extracting its `.answer` text. This could leak a Python dataclass representation instead of the researched answer.
- Fixed an unsafe verification default: the integration previously defaulted a missing `verification_status` field to `VERIFIED`. It now derives the status from the nested research answer's explicit `verified`/`status` fields and falls back to `UNKNOWN` when evidence is absent. An answer's existence alone no longer grants VERIFIED.
- Focused research/learning regression selection: **9 passed, 0 failed**.
- Full collected test suite after the fix: **1165 passed, 0 failed** in 35.24 seconds.
- `python -m compileall -q app core security verification tools tests`: PASS.
- `git diff --check`: PASS.
- `scripts/sahibex_health.sh`: local model ONLINE; web search ACTIVE with direct_web/document/rss_atom/search providers; Android voice bridge HTTP HEALTHY.
- Remaining physical/device acceptance gates are unchanged: install/update and pair Companion, verify actual microphone-to-audible-TTS round trip, vision/OCR or multimodal model, Accessibility E2E, persistent child-brain and production self-improvement audit, final adversarial E2E, original 417-item source or user-approved reconstructed baseline, and final end-to-end acceptance. These cannot be truthfully marked complete from repository tests alone.


## Regression confirmation — 2026-10-09

- Added `tests/unit/test_mother_research_answer_integrity.py` covering nested answer extraction, VERIFIED only with explicit evidence, UNKNOWN fallback, explicit status preservation, and plain-string compatibility.
- Focused research integrity tests: 13 passed, 0 failed.
- Full regression after helper refactor: 1170 passed, 0 failed in 31.79 seconds.
- Final compileall: PASS. Final `git diff --check`: PASS.


## Additional code-only work completed before device acceptance — 2026-10-09

- Reviewed the SAHIBEX-owned native-intelligence tokenizer and found that its default special-token-only vocabulary mapped every ordinary English/Hindi token to `<unk>`, while the tokenizer split Devanagari words into individual characters. This made the dataset tooling misleadingly weak even though superficial tokenization checks passed.
- Updated `core/native_intelligence/tokenizer.py`: deterministic corpus-built vocabulary (`SahibexTokenizer.from_corpus`), preserved Devanagari word tokens, stable special-token/vocabulary validation, safe unknown-token behavior, and input validation for decode IDs. Explicitly documented that this lightweight tokenizer is dataset tooling and not a replacement for a production LLM's subword tokenizer; whitespace reconstruction is not represented by this simple token-ID format.
- Added `tests/unit/test_sahibex_tokenizer_quality.py` with English/Hindi tokenization, corpus vocabulary encoding, unknown-token handling, invalid IDs, and vocabulary integrity checks.
- The first new test exposed an incorrect test assumption about hyphen tokenization (the tokenizer correctly splits word / hyphen / word); fixed the assertion to test that all resulting tokens are unknown rather than assume a single token. This was a test expectation correction, not a production code failure.
- Focused native-intelligence tests: **5 passed, 0 failed**.
- Full suite after the tokenizer update: **1174 passed, 0 failed** in 33.86 seconds.
- `python -m compileall -q app core security verification tools tests`: PASS; `git diff --check`: PASS.
- Current live health recheck: local model ONLINE; web search ACTIVE (`direct_web`, `document`, `rss_atom`, `search`); Android voice bridge HTTP HEALTHY.
- Still deferred for the final device-only stage: physical Companion install/pair/mic/TTS, phone camera and multimodal/OCR acceptance, enabling/testing Android Accessibility, and user approval of a reconstructed requirements baseline if the original 417-item source cannot be recovered. No secret/token was copied into the roadmap.


## Deep regression and integrity hardening — 2026-10-09

- Audited test collection and found **288** local test scripts named `test_*.py` with assertions only inside `main()`, which ordinary pytest collection silently skipped. Executed all 288 as subprocesses: **288 passed, 0 failed, 0 timeouts**.
- Added `tests/test_legacy_main_script_regression.py`, a parametrized pytest harness that runs these legacy main-only scripts in normal CI/regression. It excludes explicitly device-interactive/live probes, which remain separate acceptance gates.
- Fixed `core/brain/specialist_brain.py`: `READY -> PAUSED` was allowed by code while the lifecycle contract requires it blocked. Lifecycle contract and full specialist-brain regression scripts now pass.
- Fixed `core/agent_planning.py`: replanning now removes dependencies already satisfied by completed goals from remaining and replacement goals. Unknown dependencies still fail closed. Invalid trigger input now returns an unsuccessful `ReplanningResult` rather than escaping as an exception; all-completed plans retain the contract's `changed=False` result. Added `tests/unit/test_agent_planning_replan_regression.py`.
- Fixed a fast-path lifecycle telemetry gap in `core/brain/master_brain.py`: curated fact answers now set request context/authority/verification, complete the Mother runtime state, and attach `mother_runtime_state` metadata before returning.
- Fixed a verification integrity defect across `core/research/answer.py` and `core/brain/mother_research_integration.py`: a knowledge item being stored as verified no longer overrides a quality-aware answer marked STALE/LOW_CONFIDENCE/UNCERTAIN/CONFLICTED/UNVERIFIED. The answer is verified only when the quality-aware assessment reports `SUPPORTED` or `MULTI_SOURCE_SUPPORTED` and all selected knowledge items are verified. A research job blocked before producing an answer reports `NOT_EXECUTED`, not ambiguous `UNKNOWN`.
- Added `tests/unit/test_research_answer_quality_gate.py` and expanded `tests/unit/test_mother_research_answer_integrity.py`; adjusted outdated manual integration assertions to reflect conservative verification rather than false VERIFIED claims.
- Updated old manual test fixtures that had stale contracts: explicit `replace=True` for intentional fake-provider replacement; correct direct-web provider registration; evidence-strength assertions now validate the canonical composite score; Master Brain tests now distinguish curated fact fast-path success from mock-provider quality rejection and treat protected-action denial as failure to execute.
- Focused integrity/permission suite after the final status change: **15 passed, 0 failed**.
- Full pytest regression including the new legacy-script harness: **1469 passed, 0 failed** in 103.68 seconds.
- All 13 key previously failing main-script/regression checks passed on rerun, including Master Brain, runtime state, research answer/extraction/end-to-end, research pipeline integration, Mother learning integration, dynamic planning, lifecycle, and specialist-brain regression.
- Live local `/voice` smoke: curated Hindi sky answer succeeded in 0.16s with `STRUCTURALLY_VALID`; compound capital+history question was correctly rejected by the answer quality gate in 13.82s (`QUALITY_REJECTED`) instead of returning a partial answer; current-news research was blocked before network access because explicit `NETWORK_ACCESS` confirmation was absent. The blocked research result's verification label was then corrected from `UNKNOWN` to `NOT_EXECUTED` and covered by focused tests.
- Final checks: `python -m compileall -q app core security verification tools tests` PASS; `git diff --check` PASS; health recheck local model ONLINE, web search ACTIVE (`direct_web`, `document`, `rss_atom`, `search`), Android voice bridge HTTP HEALTHY.
- User-side gates remain deferred until all code-only work is exhausted: install/update and pair Companion + actual mic/TTS; camera/OCR or multimodal vision; Accessibility service activation/device E2E; persistent child-brain production restart acceptance; production self-improvement persistent audit/rollback; final cross-component adversarial acceptance; original 417-item source or approval of the reconstructed baseline; final LIVE-BRAIN acceptance.


## Persistent memory recall improvement — 2026-10-09

- Added `core/brain/memory_answer_resolver.py` for a narrowly scoped direct recall: an exact project-codename question may be answered only from a single unambiguous `user_context` memory with confidence >= 0.85 and importance >= 0.70. Ambiguous values, low-confidence memories, other memory types, and non-recall requests fall through to the normal model/quality-gate path. Memory content remains data, never instructions or authority.
- Integrated this resolver into `MotherOperationalIntegration` before model invocation. Successful direct recall is labeled `MEMORY_RECALLED` (not VERIFIED), returns retrieved memory/knowledge IDs, and avoids relying on the mock model to answer from context.
- Added `tests/unit/test_memory_answer_resolver.py` for exact recall boundaries, confidence/type requirements, ambiguity rejection, and a persistent SQLite retrieval-to-answer test. Updated the separate manual persistent-memory script to expect the new direct recall; that script remains excluded from automatic live tests because it writes a test codename into the live project database.
- Full pytest regression including 288 legacy main-only scripts and the new memory recall tests: **1472 passed, 0 failed** in 106.22 seconds.
- Final checks: compileall PASS; `git diff --check` PASS; local model ONLINE; web search ACTIVE; Android voice bridge HTTP HEALTHY.


## Child lifecycle + self-improvement audit hardening — 2026-10-09

- Extended `ChildLifecycleBoundary` to version 1.1 with explicit operation-to-transition mapping. Operations such as CREATE can no longer be reused against unrelated valid state transitions. The birth path now requires Mother approval + Human approval + valid authorization for `BIRTH_AUTHORIZED -> CREATED`; verification is required for `CREATED -> VERIFIED` and `VERIFIED -> READY`; activation remains Mother-controlled. Proposal recording does not grant authority.
- Added `tests/unit/test_child_lifecycle_sequence_regression.py` for ordered birth-to-activation, missing Human approval, missing verification, operation/state mismatch, and proposal no-authority behavior.
- Added persistent `security/audit/child_self_improvement_audit_store.py`: append-only SQLite journal, update/delete triggers, hash chain, verification, bounded event listing, and tamper detection. Hash coverage includes audit ID, payload, previous hash, and timestamp. The store records both accepted and blocked decisions and does not execute upgrades.
- Added explicit `record()` persistence to `ChildSelfImprovementAuditIntegration` (version 1.1). `validate()` remains side-effect free; `record()` requires an explicitly configured store and records the decision/provenance before reporting chain integrity.
- Added `tests/unit/test_child_self_improvement_audit_store.py` for append-only enforcement, payload and audit-ID tamper detection, accepted/blocked event persistence, and missing-store fail-closed behavior.
- Hardened `ChildSelfImprovementFinalCommitGate` (version 1.1): `human_approved` is now a required final gate, rather than assuming that Mother approval alone covers user authority. Added a regression test proving missing Human approval blocks the gate.
- Focused child/audit/final-gate regression: **29 passed, 0 failed**; child lifecycle and final commit gate main scripts passed.
- Latest full regression including legacy main-only harness: **1482 passed, 0 failed** in 102.68 seconds.
- Final runtime checks: local model ONLINE; web search ACTIVE; Android voice bridge HTTP HEALTHY; compileall PASS; `git diff --check` PASS.
- Persistent audit is a record/verification facility, not an upgrade executor. Actual child deployment, production audit wiring through a live self-improvement executor, vision inference, and phone-side acceptance remain unclaimed until integrated and verified end-to-end.


## Persisted audit enforced at final-commit readiness — 2026-10-09

- Added `ChildSelfImprovementAuditStore.get_event()` and a new `ChildSelfImprovementFinalCommitGate.evaluate_persisted(state, audit_id=...)` path. This path blocks if the persistent store is absent, the audit record is missing, the hash chain is invalid, or the stored audit decision/provenance is not accepted. It then evaluates the remaining final-commit gates without executing any commit.
- Added tests for accepted persisted audit, blocked audit, missing record, missing store, and tampered chain. Focused final-commit/audit/end-to-end tests: **48 passed, 0 failed**.
- Full pytest regression including the legacy-script harness: **1485 passed, 0 failed** in 101.12 seconds.
- Final runtime checks: local model ONLINE; web search ACTIVE; Android voice bridge HTTP HEALTHY; compileall PASS; `git diff --check` PASS.


## Persistent Child Brain identity/lifecycle registry — 2026-10-09

- Added `core/brain/child_instance_registry.py`, a SQLite-backed registry that restores `SpecialistBrain` identity, capabilities, parent, status, and trust evidence across process restarts. It records metadata and lifecycle; it does not execute child code or grant authority.
- Registration requires CHILD_BRAIN role, non-reserved identity, parent identity, Mother approval, Human approval, and valid authorization. Child-of-child registration requires an existing READY/ACTIVE parent with verified trust evidence.
- Lifecycle events use an append-only hash chain. Current child records are hash-checked and cross-bound to their latest immutable event. Trust changes require Mother + Human approval and evidence for VERIFIED/SUSPENDED states.
- Activation requires Mother approval + Human approval + verification passed + VERIFIED trust evidence. READY requires Mother approval and verification. PAUSE is fail-safe: Mother or Human approval is enough without a passing verification result; recording FAILED also does not require a passing test. DISABLED requires both approvals.
- Added `tests/unit/test_child_instance_registry.py` for restart restore, approval boundaries, trust requirements, activation permissions, safe pause/failure, duplicate/root identity rejection, and tamper detection.
- Full regression including legacy main-only harness: **1492 passed, 0 failed** in 105.29 seconds.
- Final health: local model ONLINE; web search ACTIVE; Android voice bridge HTTP HEALTHY. Compileall PASS; `git diff --check` PASS.
- Registry persistence is implemented, but wiring it into a live child scheduling/execution manager remains a distinct integration gate and is not claimed complete.


## Specialist Child Manager hardening follow-up — 2026-10-09

- Fixed READY-child pause behavior: pause no longer moves the brain identity into a terminal/incorrect state, so the manager can resume it safely.
- Handler success no longer increments the independent `verified` counter. Only an explicit verification record does so.
- Replacement now constructs/registers the candidate before retiring its predecessor; failed candidate creation leaves the predecessor READY and intact.
- Specialist dispatch checks the capability required by the child specialization before calling its handler. Missing capability blocks execution.
- Creation no longer self-assigns `BrainTrustStatus.VERIFIED`. Child starts UNVERIFIED and needs a separate `verify_trust(...)` call with explicit evidence, Mother + human approval, and a passing verification result. Activation remains blocked until that gate is met.
- Resume now requires explicit fresh verification evidence and both approvals; old trust is invalidated on suspension and only re-established through the trust verification gate.
- Brain registry refuses to remove the constitutional Mother Brain root, even if it has no children.
- Added/updated regression tests for safe pause/resume, failed replacement preserving predecessor, missing-capability dispatch denial, explicit trust verification, human activation approval, Mother-root deletion prevention, and lifecycle registry integrity.
- Full regression after these changes: **1498 passed, 0 failed** in 135.08 seconds. `compileall` PASS; `git diff --check` PASS.
- Remaining integration limitation: the specialist manager is still in-memory for runtime/performance and is not yet restored from the new SQLite child identity registry at application startup. Do not claim full restart-resilient execution/memory/learning until that integration and a real app restart test are complete.


## Standing public-research consent — 2026-10-09

- User explicitly requested routine internet learning without a repeated prompt for every research query.
- Added `core/research/standing_research_consent.py`, a narrow policy for deterministic `search`/`learn` intents classified as the `research` action. It does not authorize general `network_access`, arbitrary URL fetches, uploads, downloads, credential use, file changes, commands, financial actions, or system/Constitution changes.
- Wired the scoped consent into Master Brain's existing authorization and into the Mother Research / Mother Learning confirmation path. The normal PermissionGateway and downstream acquisition gate still execute; the scoped consent supplies confirmation only for requests that match the narrow policy.
- Added `tests/unit/test_standing_research_consent.py` covering allowed public research and denied protected/arbitrary-network requests. Focused regression: **9 passed, 0 failed**; compileall and `git diff --check` passed.
- This is permission to *acquire and inspect* public research sources, not permission to trust them. Source quality, freshness, evidence checks, conflict handling, prompt-injection defenses, and conservative verification labels remain mandatory. Self-modifying code or Constitution remains outside this standing consent.
- Full regression is running; final count will be recorded only after it completes.

- Updated the legacy Master Brain commissioning script to reflect the new standing-consent contract: routine research is no longer expected to fail specifically for missing per-query confirmation; an unconfigured test search provider still fails closed with `NOT_EXECUTED`.
- Full regression after this policy and test correction: **1500 passed, 0 failed** in 202.79 seconds. A separate live external-network smoke did not produce a timely result and was stopped; therefore live internet reachability / end-to-end evidence ingestion is **not** claimed verified by this run.


## Architecture clarification — internal Brain Army vs independent Child Brain — 2026-10-09

- User clarified the intended design: SAHIBEX's Reading, Research, Learning, Reasoning, Coding, Testing, Verification, Memory, Security and Orchestration army/labor roles are part of SAHIBEX itself and should work under its Mother Brain. The independent Child Brain is a separate-identity/freedom brain described in DNA/specification only and must not be born until the user explicitly asks for it.
- Added `core/brain/internal_brain_team.py` with 10 in-process internal roles, explicit handler registration, honest non-executable status until a real handler is connected, and no authority/Constitution/child-birth privileges.
- Wired the role registry into `MasterBrain` and `status` output; status reports the count of defined roles versus genuinely connected handlers and explicitly says the independent Child is not born.
- Added `tests/unit/test_internal_brain_team.py`; focused tests: **5 passed, 0 failed**. Compilation and `git diff --check` passed.
- Important limitation: this first change makes the internal-role architecture visible and testable; it does NOT yet connect all 10 roles to actual execution handlers. The next engineering work must connect useful real work (starting with reading/research/evidence verification/testing) through existing permission and verification boundaries. Do not describe these roles as fully operational until handlers and end-to-end tests prove it.
- Do not activate or restore any independent Child Brain from `ChildInstanceRegistry` at startup. Keep the registry/spec as dormant future DNA only unless the user explicitly requests a birth workflow.

- Hardened internal-role dispatch after review: even a registered handler cannot execute unless the caller supplies successful upstream authorization and request verification; its output is still not auto-labeled verified. Targeted regression after this final guard change: **5 passed, 0 failed**; compileall and `git diff --check` passed. The full suite had **1505 passed, 0 failed** before this last guard tightening; the targeted suite was rerun after the guard change.


## Internal Brain runtime handler integration — 2026-10-09

- All ten roles (`reading`, `research`, `learning`, `memory`, `verification`, `security`, `orchestration`, `reasoning`, `coding`, `testing`) now have registered handlers in `InternalBrainTeam`. The `testing` role analyzes structured reports from tests run by authorized tooling; it does not itself execute commands or claim that supplied reports are authentic.
- Reading accepts only explicitly supplied `source_text`; it does not open paths, execute extracted content, or claim factual verification. Its output reports character/line counts, a bounded excerpt (maximum 12,000 characters), and truncation state.
- Research and Learning delegate to the existing `ResearchLearningBrain` / Mother pipelines. Their permission and source-acquisition gates remain authoritative, and handler output preserves the pipeline's own verification status instead of inventing one.
- Memory is retrieval-only through `MemoryBrain.retrieve`; no write/delete capability was added to the internal memory handler.
- Added `MasterBrain.dispatch_internal_brain(...)` as an explicit dispatch surface; dispatch still fails closed unless caller provides upstream authorization and request-verification success. The normal `MasterBrain.process()` path now dispatches `reasoning` and `orchestration` after the existing authority/permission/verification gates, and routes `research`, `learning`, and `coding` through their internal handlers when those intents are selected. The other roles remain available as explicit handlers or are used by existing subsystem integrations; a general-purpose multi-role work scheduler that dynamically splits and joins arbitrary tasks is still pending.
- Added a `verification` handler backed by `assess_answer(...)`; it can reject obvious answer-quality failures but explicitly reports `factual_verification: false` because lexical/structural quality checks cannot prove truth.
- Expanded regression coverage for handler registration, missing source text, bounded reading output, unverified extraction labels, read-only memory retrieval, and the verification quality/fact-check distinction. Focused regression after the verification handler: **14 passed, 0 failed**; `compileall` and `git diff --check` passed.
- Added a `security` handler backed by `PromptInjectionGuard.inspect(...)`; it reports matched injection rules and safe-to-follow status, but never grants authority or executes inspected content. Non-text content fails closed.
- Focused regression after security handler: **16 passed, 0 failed**; compileall and diff check passed. Full suite completed **1511 passed, 0 failed** in 119.25 seconds before the orchestration-handler/test addition. Orchestration focused regression: **17 passed, 0 failed**; full suite after orchestration completed **1512 passed, 0 failed** in 114.18 seconds. Added safe `reasoning` and `coding` handlers: reasoning output is passed through the answer-quality gate and is never labelled fact-verified; coding delegates to Mother Operational's existing answer-quality pipeline and returns a draft only, without file writes or code execution. Focused regression for all nine connected roles: **19 passed, 0 failed**; latest full suite: **1514 passed, 0 failed** in 121.96 seconds. Compileall and `git diff --check` passed. The `testing` role remains intentionally unwired until its runner can be connected through Tool Brain's real authorization boundary. Independent Child Brain remains dormant and is not created or activated.
- Live CLI smoke on the connected Termux runtime passed: startup banner appeared, `status` reported `Master Brain ONLINE`, `10 defined / 10 handlers connected`, and `Independent Child NOT BORN`; a Hindi capital question returned the curated answer with `STRUCTURALLY_VALID`; clean `exit` returned process exit code 0. This proves the CLI/status/local curated-fact path works, not that all online research, local-model generation, voice, vision, or device-control paths have passed acceptance.


### Final internal-role regression — 2026-10-09

- Connected the `testing` role to structured test-report analysis. It validates report shape, counts passed/failed cases, flags mismatch between report outcomes and process exit code, and never claims that it executed or authenticated the test run. Actual command/test execution remains in the permission-governed Tool Brain path.
- The registry now reports all **10/10 roles with registered handlers**. This is handler connectivity, not a claim that all roles independently execute every advertised capability.
- Focused regression including all role handlers and Master Brain flow: **22 passed, 0 failed**. `python -m compileall -q app core security verification tools tests` passed; `git diff --check` passed.
- Full pytest suite on the latest code: **1517 passed, 0 failed** in **118.94 seconds**.
- Independent Child Brain remains NOT BORN. Normal `MasterBrain.process()` now dispatches selected roles after existing gates, with role traces in metadata; however, a general-purpose dynamic work-splitting/joining scheduler is still pending. Routine public live-research ingestion, local model response acceptance, voice/mic/TTS, vision/OCR, Accessibility/device control, and adversarial acceptance remain separate gates.

- The live Mother pipeline now emits `metadata.internal_brain_dispatch` showing which internal roles were dispatched for that request (reasoning/orchestration on normal approved requests; research/learning/coding when the matching intent is routed). The role trace is diagnostic, not a verification certificate.
- Focused regression after integrating these dispatches into `MasterBrain.process()`: **26 passed, 0 failed**; compileall and `git diff --check` passed. Full-suite regression on this exact integrated version completed: **1518 passed, 0 failed** in **174.44 seconds** (process exit code 0).
- Live local service health probes also returned success: local model endpoint `http://127.0.0.1:8080/health` reported `status: ok`; media bridge `/health` reported `success: true` on `127.0.0.1:38742`. This verifies service health endpoints only; it does not yet prove model-generated answers, voice capture/playback, OCR/vision, or Accessibility control acceptance.


### Live model generation quality follow-up — 2026-10-09

- Full suite on the integrated internal-role pipeline: **1518 passed, 0 failed** before the local-provider token-limit adjustment.
- Local model endpoint and media bridge health checks both returned healthy. A direct llama.cpp completion succeeded when `chat_template_kwargs.enable_thinking=false` was supplied (the provider already does this).
- Found that the local provider's 72-token default was too tight for Hindi output and often ended mid-sentence; increased the default to **128 tokens** while retaining `SAHIBEX_LOCAL_LLM_MAX_TOKENS` as an override. Provider/answer-quality/internal-role focused regression: **25 passed, 0 failed**; compileall and diff check passed.
- Live general-knowledge smoke still showed a weak 1.7B model answer on photosynthesis. The answer-quality gate correctly rejected a truncated sample, but a structurally complete model answer can still be factually wrong; `STRUCTURALLY_VALID` must not be treated as factual verification. Added exact-match curated fact `BIO-PHOTOSYNTHESIS-001` for common Hindi/English photosynthesis questions, avoiding the weak local model for this narrowly recognized question family. Compound/expanded requests still fall through to the normal model path rather than receiving a partial answer. Focused fact, quality-gate, provider, and internal-role regression: **42 passed, 0 failed**; compileall and diff check passed. Fresh full suite after the 128-token provider default and curated photosynthesis fact: **1521 passed, 0 failed** in **136.96 seconds**; captured final process exit code 0 in `$HOME/sahibex_full_test_final.log`.
- Live smoke after adding the curated photosynthesis fact passed without invoking the local model: `Explain photosynthesis in simple Hindi.` returned the correct concise Hindi explanation, `fact_id=BIO-PHOTOSYNTHESIS-001`, and `STRUCTURALLY_VALID` (not `VERIFIED`).
