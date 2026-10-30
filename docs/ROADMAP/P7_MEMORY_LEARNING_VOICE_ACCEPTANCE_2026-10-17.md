# P7 Acceptance Report — Memory, Learning, Retrieval, Security, Android Voice

**Date:** 2026-10-18 (re-verification update)  
**Workspace:** `~/SAHIBEX` on the Android Termux device  
**Scope note:** This report records the user-requested P7 bundle (items 10–18 plus Android voice). The existing roadmap's canonical **P7 Vision/OCR** label is intentionally left unchanged; this is a separate acceptance bundle.

## Overall result

- **Software regression:** PASS — fresh full run after the 2026-10-18 fixes: **1,959 passed in 204.05s**, exit code 0.
- **Full P7 / physical voice acceptance:** **BLOCKED / PENDING** until a user-consented real Android microphone → recognition → Main Brain → audible speaker test is performed. Backend/unit tests are not an acoustic round trip.
- **Memory isolation:** exact scope matching now fails closed in both directions. Scoped records require complete matching user/task/child/namespace context; legacy unscoped records are available only to unscoped/global callers and are excluded from scoped retrieval. Legacy records are not automatically assigned to a particular user because ownership cannot be inferred safely.

## Changes made

1. `core/research/storage.py`
   - Natural-language English knowledge queries now use significant-token overlap after the FTS candidate prefilter, instead of requiring only an exact phrase.
   - Indic-script queries use a full candidate scan followed by the same strict relevance filter because SQLite FTS tokenization may split/miss Indic combining marks on device builds.
   - Result limits are applied after relevance filtering so a high-confidence but irrelevant FTS hit cannot crowd out a relevant result.
   - Retrieval enforces exact `user_id`, `task_id`, `child_brain_id`/`child_id`, and `memory_namespace` matches in both directions. A scoped record is excluded if the caller omits any scope dimension; an unscoped legacy record is excluded from scoped retrieval. Malformed scope context fails closed.
   - Corrupt database initialization closes the failed connection and propagates the database error; it does not silently replace corrupt state with an empty store.
   - Canonical knowledge writes and derived search-index writes remain within one transaction.
2. `core/brain/mother_operational_integration.py`
   - Ordinary answers no longer receive old `conversation` memories as prompt context; explicit previous-conversation recall can still use them. This stops repeated assistant answers from reinforcing themselves as facts.
   - Narrow English, Hindi, and Hinglish greeting requests use a deterministic, language-matched response rather than letting a weak local model produce an unrelated response.
3. `core/brain/universal_language_brain.py`
   - `नमस्ते` is treated as a common Hindi marker, not a Sanskrit-only marker, so Hindi fallback selection is correct for ordinary Hindi greetings.
4. `android_companion/app/src/main/java/com/sahibex/companion/MainActivity.java`
   - The user chooses Hindi/Hinglish (`hi-IN`) or English (`en-IN`) before Android speech recognition opens; Cancel sends nothing.
   - TTS chooses Hindi or English based on the response script. A response is spoken only when HTTP is 200, `success=true`, and that TTS language is supported.
5. Tests added/extended:
   - `tests/unit/test_knowledge_retrieval.py`
   - `tests/unit/test_p7_fail_closed_scope_retrieval.py` (added legacy-unscoped and partial-scope fail-closed cases)
   - `tests/unit/test_conversation_memory_context_filter.py`
   - `tests/unit/test_hindi_intent_routing.py` (added Hindi greeting-plus-language-instruction and substantive-question guard cases)
   - `core/brain/conversation_resolver.py` now recognizes a narrow greeting + answer-style instruction without swallowing greetings that contain a substantive question.

## Verification evidence

- **Fresh full repository regression after the 2026-10-18 code changes:** **1,959 passed in 204.05s**, exit code 0 (direct terminal output from the current workspace; the older 1,953-test log remains historical).
- `python -m compileall -q core tools app tests`: PASS after the changes.
- `git diff --check`: PASS after the changes.
- Focused scope/memory and Hindi intent/greeting suite: **29 passed in 0.58s**.
- Earlier focused language/retrieval/memory suite: 38 passed; focused relevance/scope suite: 47 passed; focused corruption/partial-write suite: 59 passed (separate historical runs).
- Corruption and partial-write tests prove: invalid SQLite bytes raise a database error without replacing the file; an injected transactional failure leaves no canonical knowledge row or search result; a later healthy write/retrieval succeeds.
- Memory isolation tests prove exact user/task/child/namespace matching for explicitly scoped records, malformed scopes fail closed, and ordinary greeting queries do not reuse old conversation answers as prompt context.
- Android build: **BUILD SUCCESSFUL** with Gradle 8.13 and the device-compatible SDK `aapt2` override. The Gradle 9.8/Android Gradle Plugin 8.13 incompatibility was handled as a build-environment setting; project build configuration was not changed to hide it.
- APK: `android_companion/manual-build/SAHIBEX-Android-Companion-P7-debug.apk`; copied to Android Downloads as `SAHIBEX-Android-Companion-P7-debug.apk`. Package `com.sahibex.companion`, version `0.2.2`, versionCode `6`. SHA-256: `750a8abc72c8b53087447ade391376dbb4d062d6c8b130ae06b766d46204b8cb`. Its signing certificate SHA-256 matches the prior debug APK, so the signing identity is consistent.
- Live authenticated relay after restarting the stale bridge process:
  - English: HTTP 200, `success=true`, `STRUCTURALLY_VALID`, response `Hello! How can I help you?`, detected response language `en`.
  - Hindi: HTTP 200, `success=true`, `STRUCTURALLY_VALID`, response `नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ?`, detected response language `hi`.
  - Evidence: `logs/p7_20261017/voice_relay_english_final.json`, `logs/p7_20261017/voice_relay_hindi_final.json` (historical 2026-10-17 run).
- During the 2026-10-18 recheck, a Hindi greeting that also requested a short Hindi answer timed out on the live relay before the deterministic greeting matcher was extended. The matcher fix and a regression test now PASS, but the same live relay request has **not** been successfully re-run after that fix; this remains a software-level live-relay verification item.
- Current bridge health returned HTTP 200. A deliberately invalid bearer token was rejected with HTTP 401. The local model health was OFFLINE at the beginning of this session and later returned healthy; this was not treated as proof of a successful Hindi answer.
- The Android ADB session reports no connected test device. Therefore microphone capture, actual speech recognition UI, audible TTS, cancellation recovery, and speaker output remain untested on the physical device.

## Requested P7 checklist

| Item | Status | Evidence / boundary |
|---|---|---|
| 10. Corruption / partial-write recovery | PASS | Fail-closed corrupt DB and transactional rollback tests |
| 11. Retrieval relevance + provenance | PASS (bounded) | English/Hindi relevance tests; verified-only lifecycle/provenance regression |
| 12. Hindi and English retrieval | PASS (software/text relay) | Hindi/English retrieval tests and live text relay responses; not a microphone test |
| 13. Memory isolation | PASS for complete scoped requests; BLOCKED for universal legacy ownership | Scoped requests require exact complete scope; legacy unscoped data is excluded from scoped retrieval but is not auto-assigned to a user |
| 14. Permission/security audit | PASS | Protected action and security regression tests; voice relay cannot approve protected actions |
| 15. Research → verification → promotion → retrieval | PASS (bounded) | Existing live MainBrain research acceptance plus verified-only promotion/retrieval integration tests |
| 16. Timeout/empty source/DB failure/conflict recovery | PASS (bounded) | Failure-injection, conflict, recovery and full regression tests |
| 17. Promotion/update/reject/rollback audit trail | PASS (bounded) | Persistent lifecycle/audit and restart/rollback regression tests |
| 18. Regression/final acceptance | PASS for software suite | Fresh 1,959-test run after 2026-10-18 fixes; compileall and diff check PASS; physical voice remains a separate blocked release gate |
| Android voice physical round trip | BLOCKED / PENDING | Real mic → recognition → Main Brain → audible speaker still requires user interaction on the phone |

## Remaining acceptance action

1. Open Android **Downloads** and install/update `SAHIBEX-Android-Companion-P7-debug.apk`.
2. Open SAHIBEX Android Companion and ensure it is paired with the local token (keep the token private). Confirm `curl -fsS http://127.0.0.1:38742/health` returns healthy.
3. Tap **Speak to SAHIBEX**, select Hindi/Hinglish, speak a harmless greeting, confirm the transcript, send it, and verify the Hindi answer is audible. Repeat in English.
4. Test Cancel and bridge-stopped recovery. Report what was heard and whether each language worked.

Until the physical voice acceptance and the universal scope/migration limitation are resolved, **do not mark full P7 or the overall product as fully LIVE**.

## Verification refresh — 2026-10-19

- Focused P7 regression selection: **76 passed in 7.34s**, exit code 0. Included fail-closed scope/retrieval, knowledge retrieval, conversation-memory filtering, Hindi intent routing, learning-history persistence, knowledge verification lifecycle, task 34 persistence/restart recovery, task 35 failure recovery, task 29 permission/security boundaries, and Android companion media-server tests.
- Fresh full repository regression: **1,965 passed in 176.51s**, exit code 0.
- `python -m compileall -q core tools app tests`: PASS (exit code 0).
- `git diff --check`: PASS (exit code 0).
- Live recheck at refresh time: bridge health `127.0.0.1:38742/health` **OFFLINE**; local model health `127.0.0.1:8080/health` **OFFLINE**. Android ADB reports no connected test device.
- Acceptance boundary: software regression is freshly PASS; the live Hindi-after-fix relay retest is not currently possible while the bridge/model endpoints are offline. Physical Android microphone → recognition → Main Brain → audible speaker acceptance remains BLOCKED pending a connected phone and user-consented test. Do not mark full P7 LIVE until this gate passes.

## Runtime recovery check — 2026-10-19 (follow-up)

- Started the configured primary Qwen3-4B model using the existing guarded script `scripts/start_local_model.sh`; it reported **ONLINE** on `127.0.0.1:8080`, PID 27246, context 1024. No 1.7B fallback was used.
- Started the existing media bridge using `scripts/start_sahibex_media_bridge.sh`; it reported **ONLINE** on `127.0.0.1:38742`, PID 27680.
- Follow-up health checks returned HTTP 200 for both bridge `/health` and model `/health`; `/v1/models` reported the expected Qwen3-4B GGUF model ID.
- A direct model completion request reached the model server and completed, but its returned message content was empty despite `finish_reason=length`; treat answer-quality acceptance as **FAIL/PENDING investigation**, not PASS.
- Authenticated English and Hindi `/voice` relay checks were initiated against the real bridge, but had not returned a result at the time of this report update. They are not counted as passing.
- Android ADB still reports no connected device, so physical microphone → recognition → Main Brain → audible speaker acceptance remains **BLOCKED**.
- Memory available after loading the 4B model was about 1.2 GiB. Keep the guarded startup policy; do not start the 1.7B fallback automatically or bypass RAM checks.

### Live relay results — 2026-10-19

- Authenticated English `/voice` request returned HTTP 200 but `success=false`, `verification_status=QUALITY_REJECTED`, with the safe refusal message “I could not produce a reliable answer…”. **English live answer-quality test: FAIL** (fail-closed behavior observed; expected basic arithmetic answer was not produced).
- Authenticated Hindi `/voice` request returned HTTP 200, detected input/answer language `hi`, but `verification_status=INSUFFICIENT_EVIDENCE` and declined to answer a basic arithmetic question. **Hindi live answer-quality test: FAIL** (language path works, answer quality does not meet acceptance).
- Both relay requests completed (English 30.8 s; Hindi 19.7 s). The bridge returns structured result metadata, but simple-question acceptance is not met. Do not count either as a language-answer PASS.
- Next fix target: trace why the local model/provider output and Main Brain factual fast path fail this deterministic arithmetic prompt, then add/verify focused tests and rerun the live bilingual relay. Do not weaken the verification gate to force a PASS.


## Verification refresh — 2026-10-19 (latest run)

- Fresh full repository regression: **1,969 passed in 175.35s**, exit code 0. The only failure in the preceding run was a stale assertion in `tests/unit/test_task31_main_brain_architecture_acceptance.py` that did not allow the intended English deterministic response `Answer: 4`; the test expectation was updated to accept `4`, `Answer: 4`, or `उत्तर: 4`. Focused verification of that file plus math resolver and Main Brain tests: **14 passed in 2.71s**.
- `.venv/bin/python -m compileall -q core tools app tests`: PASS.
- `git diff --check`: PASS.
- Local model configuration is `Qwen3-4B-Q4_K_M.gguf` through `llama.cpp`, default context 1024, single parallel slot, two threads. Startup guard remains enabled at 3 GiB available RAM; current model start is still not accepted while the guard blocks. Do not lower/bypass the safety guard without measured memory evidence.
- Media bridge / cloud GPU integration and current live Hindi/English inference were not freshly verified in this run. Previous live relay evidence in the section above records QUALITY_REJECTED / INSUFFICIENT_EVIDENCE for basic arithmetic; these remain unresolved and must not be marked PASS.
- Physical Android microphone → recognition → Main Brain → audible speaker acceptance remains BLOCKED because no ADB test device is connected.
- Final status: **software regression PASS; model runtime/live answer quality and physical voice acceptance BLOCKED/PENDING**. Full product/P7 must not be marked fully complete until those gates pass.

## Follow-up verification — 2026-10-19 (empty local model output fail-closed fix)

- Full repository regression after the fix: **1970 passed in 168.32s**, exit code 0.
- Focused local provider/model gateway tests: **3 passed**.
- compileall for the modified provider/test and git diff --check: PASS.
- Fix: core/model_gateway/local_llama_provider.py now treats whitespace-only model content as an inference failure (success=False) rather than success; regression test added in tests/unit/test_local_llama_provider.py.
- Startup guard retest: BLOCKED safely. MemAvailable observed at 3,066,316 kB, below the required 3,145,728 kB (3 GiB). No guard bypass or duplicate server start was attempted.
- Current model health check: OFFLINE on 127.0.0.1:8080. Existing llama-server log shows historical successful inference timings, but this is not current live acceptance.
- Physical voice test: BLOCKED; adb devices reports no connected device.
- Remaining acceptance blockers: free RAM / current model online; fresh Hindi and English live-answer quality checks; physical Android voice path; final report closure after these blockers are addressed.
