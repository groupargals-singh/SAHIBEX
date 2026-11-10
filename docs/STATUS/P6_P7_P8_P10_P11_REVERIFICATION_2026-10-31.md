# SAHIBEX P6 / P7 / P8 / P10 / P11 re-verification — 2026-10-31

## Scope
Continued from the existing 2,251-test software baseline. No reset, cleanup, user-data deletion, credential disclosure, permission grant, database migration, or P-series promotion was performed.

## P6 — Voice / media bridge
- Found a real lifecycle bug: the media-bridge PID file pointed to an unrelated live Desktop Commander PID, while the active bridge was running under Termux system Python. The old start script trusted `/health` alone and returned success even when the authenticated TTS route returned HTTP 503.
- Preserved original start/stop scripts in `backups/media_bridge_lifecycle_guard_20261031/`.
- Reworked `scripts/start_sahibex_media_bridge.sh` to verify process command + project working directory, launch the exact project `.venv/bin/python`, check authenticated `/session`, and perform a real local TTS/WAV smoke test before declaring ONLINE.
- Reworked `scripts/stop_sahibex_media_bridge.sh` to verify the PID's exact module command and project working directory before sending TERM. It refuses unrelated/reused PIDs and no longer deletes the PID file.
- Safety test: the stop script refused PID 17084 because it belonged to the Desktop Commander Node process; that process remained alive. The verified old media bridge process was stopped, and the correct project-`.venv` bridge was started as PID 25502.
- New bridge startup: authenticated TTS smoke PASS. `/health` HTTP 200; `/session` HTTP 200; English and Hindi `/synthesize` HTTP 200 with valid WAV; English and Hindi `/transcribe` HTTP 200, `audio_retained=false`, `requires_user_confirmation=true`.
- Live `/voice` text-route: curated SAHIBEX identity response PASS; unresolved Hinglish “is topic par” request asks “आप किस विषय पर जानकारी चाहते हैं?” and creates no plan/action.
- Added the observed Whisper spelling variant `sahibaqs` to the closed SAHIBEX-name alias dictionary. Focused language/media tests: 43 passed.
- Synthetic speech loop still exposes an accuracy limitation: Hindi output was transcribed as Romanized text with errors (e.g. “Sahibaqs” / “Parikshar”). A closed alias now corrects the project name, but this is not a real-speaker accuracy evaluation.
- Physical microphone capture, Android transcript confirmation, Main Brain reply from actual captured speech, and audible Companion speaker playback remain **PENDING**. The installed local ASR artifact is `ggml-tiny-q5_1.bin`; no larger ASR model was present.

## P7 — Vision
- OCR/vision contract tests remain green. The local artifact inventory contains the Supertonic TTS ONNX files but no semantic image-understanding model.
- The current vision path is OCR-only and explicitly reports `semantic_image_understanding=false`.
- Semantic vision model, representative evaluation dataset, and camera/image-to-grounded-answer acceptance remain **BLOCKED**. No remote vision provider was enabled and no model was downloaded.

## P8 — Accessibility
- Port 38741 is reachable and responds with the expected bridge authentication behavior: an unauthenticated protocol request returns HTTP 401.
- A signed read-only `emergency_stop_status` request using the Termux media token also returned HTTP 401, showing the Companion's saved token is not paired/matching the Termux token. No action was executed.
- Accessibility bridge authentication gate and Emergency Stop contracts remain covered by tests. Actual Companion pairing, authenticated status/action, UI-tree/tap/type acceptance, persistent Emergency Stop, and local-only resume remain **PENDING**.

## Knowledge audit
- Added read-only `scripts/audit_knowledge_provenance.py` and test `tests/unit/test_knowledge_provenance_audit_script.py`.
- Audit result: 83,904 candidates; 80,198 legacy `verified=1`; 3,626 lifecycle events, all UNVERIFIED; 80,278 candidates have no lifecycle event; zero candidates have a latest VERIFIED event.
- All 83,904 candidate evidence/finding/source references are valid, but each candidate links to exactly one distinct source record. Current metadata reports one supporting/independent source for 3,471 and zero for 159 of the 3,630 candidates with verification metadata. The existing policy requires at least two independent supporting source groups.
- Database was opened read-only. No flags or records were changed. Detailed evidence: `docs/STATUS/KNOWLEDGE_PROVENANCE_AUDIT_2026-10-31.md` and `logs/knowledge_provenance_audit_20261031.json`.
- Audit execution: **PASS**. Legacy data remediation remains **BLOCKED** pending independent corroboration and explicit approval for a backed-up migration.

## P10 — 417 requirements source
- Recovered from the user's Library: `SAHIBEX_MASTER_ARCHITECTURE_v2_0.docx` (9 pages), which lists the 29 A–AC phases, item ranges 1–417, and named core items.
- Also found `SAHIBEX_MASTER_ARCHITECTURE_v2_1_CORRECTED.docx`; it explicitly says the exact original Master List v1.0 item-by-item source is unavailable and calls for a line-by-line diff against that original.
- Therefore the v2.0 integrated 417-item reference is now recoverable, but it is not proven to be the exact historical v1.0 source. P10 is **PARTIAL**, not falsely marked complete. Adopting v2.0 as a reconstructed working baseline requires explicit user approval.

## P11 — Release
- Release remains **BLOCKED** by P6 physical voice acceptance, P7 semantic vision, P8 authenticated Companion/device acceptance, Knowledge lifecycle remediation, and P10 historical-source reconciliation.

## Verification performed in this follow-up
- P6/P7/P8/Knowledge focused suite: **87 passed**.
- Language/perception/media follow-up suite: **43 passed**.
- Read-only knowledge audit utility test: **1 passed**.
- Media bridge start/stop shell syntax: PASS.
- PID safety check: PASS (unrelated PID refused, unrelated process remained alive).
- Media bridge authenticated TTS startup smoke: PASS.
- Authenticated live TTS/ASR endpoints and text-to-Main-Brain route: PASS at software/API level; Hindi ASR accuracy remains PARTIAL.
- No P-series gate promoted. Full repository regression is to be recorded separately after this follow-up's final code/test changes.

## Additional knowledge retrieval safety fix — 2026-10-31
- Audit review found legacy candidate flags could pass low-level verified_only storage queries despite missing lifecycle history. This could make the 80,198 stale verified flags visible to callers that bypass KnowledgeBrain.
- Updated ResearchStorage.list_knowledge and retrieve_knowledge to require the latest lifecycle event to be VERIFIED, including the Indic-script fallback branch. Updated ResearchQueryEngine to require an explicit VERIFIED lifecycle event for persistent queries and explicit VERIFIED metadata for in-memory verified-only candidates.
- New regression tests prove legacy verified flags without history are excluded from English and Hindi retrieval; persistent test fixtures now record a VERIFIED event explicitly.
- Focused knowledge/lifecycle/provenance tests: 34 passed. No production database write was made; all records remain untouched. Since the live DB has zero VERIFIED lifecycle events, verified_only retrieval is expected to return zero until independent-source revalidation is approved and performed.


## Final verification — 2026-10-31 (knowledge lifecycle guard)
- Full repository regression after the retrieval guard: **2,255 passed in 190.03s** (exit 0).
- Read-only provenance audit completed against `data/sahibex_brain.db`: 83,908 candidates; 3,630 lifecycle events, all latest status UNVERIFIED; 80,278 candidates have no lifecycle event; 80,198 legacy verified flags have no latest VERIFIED event; zero candidates have a latest VERIFIED event.
- All 83,908 candidates have one valid evidence reference and one valid finding reference, but the audit found exactly one distinct source per candidate and zero multi-source candidates. Evidence reference validity is not the same as independent corroboration.
- The production database was opened with SQLite `mode=ro`; audit output confirms `read_only=true`, `database_write_attempted=false`. No candidate, evidence, source, or lifecycle rows were modified.
- Therefore the audit itself is COMPLETE, but trust revalidation / promotion remains BLOCKED pending independent source corroboration and an approved, backed-up evidence-based migration. Do not bulk-promote the legacy flags.
- No P-series gate was promoted. The remaining physical-device and historical-specification gates remain separately blocked/pending.
- Machine-readable aggregate report: `logs/knowledge_provenance_audit_20261031.json`; full regression log: `logs/full_regression_20261031_knowledge_lifecycle_guard.log`.


## Live device probe — 2026-10-31 (after lifecycle fix)
- Companion package `com.sahibex.companion` is present in the installed-package list.
- Loopback port 38741 accepts the expected `POST /v1/action` route; a correctly signed request carrying a deliberately invalid, non-secret probe token returned HTTP 401 authentication failed. This verifies the bridge authentication gate rejects unauthorised requests; no device action was executed.
- GET `/health` on 38741 returns 404 because the bridge only exposes the POST action route; do not use GET /health as its health contract.
- Media Bridge `127.0.0.1:38742/health` returned HTTP 200.
- ADB reports no attached devices, and Termux could not read Android Accessibility Manager state through `dumpsys`/secure settings. Therefore enabled-service state, successful pairing with the real Companion token, UI-tree retrieval, permitted UI action, and persistent Emergency Stop remain NOT VERIFIED. Do not mark P8 complete.
- Local model API 8080 currently reports only text modality for Qwen3-1.7B; available RAM was about 1.48 GiB, below the 3 GiB Qwen3-4B guard. Semantic-model acceptance remains blocked; do not bypass the RAM guard.

## 2026-10-31 — Corrected latest read-only audit and device checks
- Re-ran the read-only audit against the live DB after retrieval hardening. Exact current counts: 83,908 candidates; 80,198 legacy verified flags without a latest VERIFIED lifecycle event; 3,630 lifecycle records and all are UNVERIFIED; 80,278 candidates have no lifecycle event; 83,908 candidates each have exactly one evidence, one finding, and one distinct source; zero candidates have multiple distinct sources; zero latest VERIFIED records.
- All 83,908 evidence/finding/source references resolve, but a single source is not sufficient independent corroboration. No bulk promotion or DB writes were performed. Verified-only eligible live records: 0.
- Qwen3-4B remains blocked by RAM: current available RAM fell to about 1.2 GiB after the existing Qwen3-1.7B low-RAM fallback was started by the guarded launcher; 4B guard requires 3 GiB. The 1.7B model is online but is not accepted for semantic quality. No guard bypass.
- Media Bridge 38742 health: HTTP 200. Accessibility bridge 38741 is listening; GET /health is not a supported route (404), and an unauthenticated POST /v1/action is correctly rejected with 401. Companion package is installed; signed Termux token probe still returns 401, so pairing/authentication is unresolved.
- Android media diagnostics: Termux speech/tts/camera CLI commands exist, but com.termux.api package was not found and termux-tts-engines timed out. No microphone/camera capture was initiated. Physical voice E2E remains pending.
- Semantic vision model/weights are absent; OCR-only capability remains. P10 remains PARTIAL (v2.0 417-item reference recovered, exact v1.0 provenance unresolved); P11 release remains BLOCKED. No gate promoted.

## Final verification checkpoint — 2026-10-31 (latest code state)
- Verified-only Knowledge retrieval now fails closed at all three paths: persistent SQL list/FTS/Indic fallback requires latest VERIFIED lifecycle event; ResearchQueryEngine persistent results require that lifecycle event; in-memory results require both metadata verification_status=VERIFIED and last_verified_at.
- Latest focused gate suite after the final in-memory rule: 31 passed in 4.22s. Python compileall, shell syntax checks, and git diff --check all PASS.
- Earlier full repository regression before the final in-memory metadata tightening: 2,255 passed in 171.71s. A new full regression was attempted after the final tightening but the pytest process disappeared at 60% without a completion summary or exit code while Qwen3-1.7B remained loaded and available RAM was about 1.2 GiB. Treat this latest full run as INCOMPLETE, not PASS or FAIL.
- Current local model: Qwen3-1.7B online (low-RAM fallback); semantic accuracy acceptance remains BLOCKED/PARTIAL. Qwen3-4B was not launched because the 3 GiB safety guard was not met.
- Live service checks: Media Bridge 38742 HTTP 200; Accessibility Bridge 38741 rejects unauthenticated action with HTTP 401. Authenticated pairing/token validation remains unresolved.
- No P-series promotion. Physical P6 microphone/speaker E2E, P7 semantic vision model/accuracy, P8 authenticated device-control/Emergency Stop acceptance, P10 exact v1.0 provenance reconciliation, and P11 release remain open.

- Additional low-memory verification attempt: split the 545 test files into 30-file batches while Qwen3-1.7B remained resident. The first batch process also disappeared at about 60% without a pytest summary/exit code; no full-suite PASS is claimed. The focused 31-test gate suite and compile/syntax/diff checks remain green. Do not stop the resident model automatically; obtain user approval before a temporary stop for another full regression attempt.


## 2026-10-31 — Final full-regression recovery after fixture compatibility fix
- Root cause of the six failures in the preceding full regression: three Research Answer Pipeline integration fixtures and three traceability integration checks constructed in-memory candidates with legacy `verified=True` + timestamp but omitted the newly required explicit `metadata.verification_status="VERIFIED"`. The production fail-closed rule was correct; the fixtures were stale.
- Updated only the two test helper/fixture files: `tests/unit/test_research_answer_pipeline.py` and `tests/unit/test_research_answer_traceability.py`. Before edits, both files were preserved in `backups/research_fixture_compat_20261031/`.
- Focused validation: **45 passed in 0.75s**.
- Full repository regression after the fixture correction: **2,257 passed in 185.85s**, explicit `FULL_REGRESSION_EXIT=0`. Log: `logs/full_regression_after_fixture_fix_20261031.log`.
- `python -m compileall -q core scripts tests` and `git diff --check`: PASS. No production database writes, no knowledge promotions, no destructive cleanup, no model shutdown, and no P-series gate promotion.
- This supersedes the immediately preceding incomplete/failed-regression notes for the current test state. The older log entries remain historical evidence and are not deleted.
- Remaining external/acceptance gaps are unchanged: P6 physical mic→ASR→confirmed transcript→Main Brain→speaker E2E; P7 semantic vision model + representative accuracy evaluation; P8 real Companion token pairing + authenticated UI/Emergency Stop acceptance; Knowledge legacy record independent-source revalidation (83,908 candidates, zero latest VERIFIED lifecycle events, one source per candidate); P10 exact historical v1.0 417-item provenance reconciliation / user decision on reconstructed v2.0 baseline; P11 release after dependent gates.

## 2026-10-31 — Understanding/voice follow-up; P6 remains partial
- Local ASR executable/model and local neural TTS runtime/model files are present; Media Bridge health remains HTTP 200.
- Hindi TTS→Whisper synthetic loopback was run. TTS synthesis passed, but ASR transcript was incomplete even after resampling to the recognizer's required 16 kHz mono PCM format.
- This does not count as phone microphone capture or speaker playback. Android Companion still requires transcript review/confirmation; physical mic→ASR→Main Brain→audible speaker acceptance remains pending.
- Qwen3-1.7B is online but did not return an accepted structured semantic-intent result in the live provider smoke; Qwen3-4B was not started because the 3 GiB RAM guard was not met.
- P6 remains PARTIAL. P7/P8/P10/P11 statuses unchanged. No P-series gate promoted.
- Full evidence: docs/STATUS/UNDERSTANDING_INTELLIGENCE_ACCEPTANCE_2026-10-31.md.

## Final runtime snapshot after regression — 2026-10-31
- The Qwen3-1.7B server was online during the live semantic-provider smoke, but the final post-regression probe found port 8080 offline and no llama-server process. The reason for its exit was not established; I did not restart it.
- Media Bridge 38742 remained healthy (HTTP 200).
- Available RAM was approximately 2.3 GiB; the Qwen3-4B 3 GiB guard remains unmet. No guard was bypassed and no model was downloaded.
- Treat the semantic model as currently OFFLINE at the final snapshot. The earlier 24.73s None result remains evidence that it did not pass semantic acceptance while online.
