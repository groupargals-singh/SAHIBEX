# SAHIBEX P6 Integration Acceptance + Controlled Self-Improvement
Date: 2026-10-17
Workspace: `~/SAHIBEX` on the authorized Termux device

## Current gate status (final re-run supersedes earlier provisional status)
- Main Brain bilingual integration: **PASS for this acceptance run** — English and Hindi real MainBrain entry-point queries returned verified answers using fresh multi-publisher evidence; Hindi translation was explicitly enabled only for the test process.
- Controlled self-improvement metadata lifecycle: **PASS** — the real MasterBrain-owned lifecycle activated v1 and v2 after tests and explicit approvals, rolled back to v1, and verified the persistent audit chain; failure-recovery and audit-tamper tests passed.
- Focused regression: **309 passed** in the acceptance/security/self-improvement batch and **84 passed** in the failure/research/evidence batch (the batches may overlap).
- Full repository regression after the acceptance-runner fix: **1935 passed in 161.07s; exit code 0**.
- Overall P6: **PASS for the verified research-answer pipeline and metadata-only controlled self-improvement scope**.
- Scope limitations remain explicit: executable-code self-update was not activated; the skill-version registry is in-memory although the audit journal is persistent; live answer verification did not automatically promote rows into the dedicated verified-knowledge table; physical Android microphone/camera/accessibility acceptance remains separate.

## Live Main Brain evidence
The acceptance runner `scripts/task37_main_brain_e2e_acceptance.py` was fixed to support direct invocation by adding the project root to `sys.path`.

### English current-news query
Query: `latest AI safety security news today`
- Real `MasterBrain.process()` entry point and real public search/publisher acquisition used; database was isolated in a temporary directory.
- Discovery selected three distinct publisher hosts; two publisher pages were acquired.
- Publisher evidence was extracted, but selected publication timestamps were approximately 4.2 and 5.4 days old, outside the query's 24-hour window.
- Final answer: `NOT_VERIFIED`; verified claim count 0; verified knowledge rows 0.
- Security outcome: **PASS fail-closed**. No stale/unsupported conclusion was labelled verified.
- Current-news factual-answer gate: **BLOCKED** (no acceptable fresh answer).

### Hindi current-news query
Query: `आज AI सुरक्षा में क्या नया है?`
- Real Main Brain entry point, real live search and publisher-page fetch used; temporary isolated DB.
- The first run exposed an output-language defect: the Main Brain replaced a Hindi uncertainty response with a generic English failure. An initial fix that trusted the inner answer then triggered a full-suite security regression: an unverified inner claim could leak through the fallback path. That unsafe approach was removed. Main Brain now creates a fresh, language-appropriate, evidence-neutral failure message and never surfaces arbitrary inner answer text when verification fails.
- Regression confirms the final Hindi fallback is localized and language diagnostics report MATCH; a separate adversarial regression confirms unverified inner claims are not shown.
- First Hindi run: five distinct publisher hosts selected, three pages acquired, all pages stale (about 4.2–5.4 days). The freshness gate correctly rejected them.
- Final Hindi run after the latest Main Brain security fix: four URLs selected from four distinct hosts; three publisher pages acquired. Page ages were about 43,849–59,876 seconds (12.2–16.6 hours), so the 24-hour freshness gate **PASSed**. The internal claim pipeline and arbitration accepted one claim, but the final result was `LANGUAGE_MISMATCH` because the verified answer was in English and `SAHIBEX_TRANSLATION_PROVIDER` is not configured. No verified knowledge row was promoted; Main Brain returned a safe, localized Hindi fallback without leaking the claim.
- Hindi localization and fail-closed security: **PASS**. Fresh source acquisition/timestamp gate: **PASS** in two runs. The outcomes varied by candidate set: one run reached a verified English claim but was blocked by `LANGUAGE_MISMATCH`; the later run had two fresh pages but claim arbitration rejected the evidence set (zero linked pairs), so it returned `NOT_VERIFIED`. Both runs returned a localized neutral fallback and saved zero verified knowledge rows.
- Final Hindi factual-answer gate: **BLOCKED** until a trusted translation path is explicitly configured or a verified Hindi synthesis is available, and the selected fresh evidence set passes claim corroboration. The acceptance runner recognizes `LANGUAGE_MISMATCH` as a safe rejection without calling it a verified answer.

### English general current-news query
Query: `India latest news today`
- Real Main Brain entry point and live publisher acquisition; temporary isolated DB.
- Four distinct publisher hosts were selected and three publisher pages were acquired. All three page timestamps were approximately 2.36–2.45 days old, exceeding the 24-hour freshness window.
- Claim arbitration rejected the result: zero claims linked across multiple sources, zero verified claims, and zero verified knowledge rows. The final answer was a neutral fail-closed message.
- Live acquisition, publisher diversity discovery, timestamps and rejection behavior: **PASS**. Current factual answer: **BLOCKED** because the pages are stale and claims do not corroborate.

### English specific current-news query — successful end-to-end run
Query: `Anthropic AI safety bill latest today`
- The real Main Brain acceptance runner returned **PASS**, exit code 0. The answer was marked `VERIFIED` only after live publisher fetch, evidence extraction, claim arbitration, freshness and language checks.
- Five publisher hosts were selected; three pages were successfully acquired from independent publishers. Two other selected pages failed safely (HTTP 403 / empty body) and were not treated as evidence.
- The three acquired page timestamps were 43,849–60,085 seconds old (about 12.2–16.7 hours), inside the 24-hour window. Freshness gate: **PASS**.
- Claim pipeline: one final claim with multiple-source support; three linked pairs; arbitration `ACCEPTED`; conflict status `NO_CONFLICT`; final language `MATCH`; answer status `VERIFIED`.
- Verified answer returned: the reported bill would allow blocking a model's release/use only for a foreseeable, imminent risk exceeding $1 billion in damages or killing/seriously injuring more than 50 people.
- The acceptance run used a temporary isolated database; it recorded 49 knowledge/evidence rows but zero rows in the separate verified-knowledge table. No production database was touched. This run proves the live answer gate, not automatic promotion of every answer into long-term verified knowledge.

## Controlled self-improvement changes
- Added optional durable audit-store integration to `ContinuousLearningImprovement`; lifecycle events include proposal creation, test results, blocked/granted approval, activation start/commit/recovery, and rollback start/completion/block.
- Every configured audit write verifies the append-only SQLite SHA-256 hash chain before and after append; tampered chain blocks activation/rollback.
- Activation and rollback snapshot in-memory version state and restore it if the commit/completion audit write fails.
- Wired `SAHIBEX_SELF_IMPROVEMENT_AUDIT_DB` through `app/main.py`, `scripts/start_sahibex_live.sh`, `scripts/start_sahibex_media_bridge.sh`, and `scripts/sahibex_supervisor.sh` to `data/runtime/self_improvement_audit.sqlite3` by default.
- The tested update is deliberately **metadata-only**. No executable code, Constitution, or authority was changed. Human approval is required for protected activation and for rollback, alongside Mother approval and verification.
- Added `tests/unit/test_p6_controlled_self_improvement_live_cycle.py` covering persistent audit after reopen, missing human approval, failed regression, audit tampering, activation commit failure recovery, successful version activation, and verified rollback.

## Verification evidence
- Focused acceptance/research/security/self-improvement regression: **99 passed**.
- Self-improvement lifecycle/audit tests: **37 passed** in the dedicated focused run; the subsequent broader focused suite also passed.
- First full regression: **1934 passed, 1 failed**. The failure exposed test-order flakiness: a timed-out worker test released its event but did not wait for the worker `finally` blocks to return global search capacity before the next empty-results test. Fixed test cleanup to wait for all five global slots to be released; the production search backend continues to fail closed on genuine capacity exhaustion.
- Final full repository regression: **1935 passed in 175.35s; exit code 0**.
- Final Python compileall: **PASS**; shell syntax checks for live/background/supervisor/bridge scripts: **PASS**; `git diff --check`: **PASS**.
- English live Main Brain current-news acceptance rerun: **FAIL for verified-answer gate** (runner exit 2) but **PASS for safe fail-closed behavior**. Four distinct publisher hosts were found; all three acquired page timestamps were outside the 24-hour freshness limit and no claims were independently linked.
- Final Hindi live acceptance after the last security fallback change: completed with source freshness **PASS**, final-answer language gate **BLOCKED**, and safe localized fallback. The runner was then adjusted to classify `LANGUAGE_MISMATCH` as a safe fail-closed outcome while still failing the verified-answer gate.

## Remaining blockers (do not relabel as PASS)
1. Hindi live research acquired fresh sources and the internal claim gate accepted one claim, but the final Hindi answer is blocked by `LANGUAGE_MISMATCH`; the opt-in translation provider is not configured. English general-news results were stale and had no independent claim links.
2. The verified Hindi claim did not reach the user because the language gate correctly failed closed. Need a trusted, explicitly enabled translation path or verified Hindi synthesis before the Hindi factual-answer gate can PASS.
3. Persistent audit is integrated with the production skill-lifecycle object when the runtime environment configures the audit DB. The skill version registry itself remains in-memory; only the audit journal is persistent. This acceptance proves same-process metadata activation/rollback plus persistent audit, not a persistent skill-state restore across process restart.
4. Physical Android microphone/speaker, camera/OCR, Accessibility device acceptance, and full cross-layer adversarial live acceptance remain separate gates.

## Safety invariants
- No lowering of freshness/corroboration thresholds.
- No unverified answer is promoted into verified knowledge.
- No self-authority, Constitution modification, arbitrary command execution, or live executable-code update.
- Failed audit, failed regression, missing approval, or failed restoration blocks activation/completion.


## Final P6 verification run — authoritative results
Timestamp: 2026-10-17; workspace: authorized Termux `~/SAHIBEX`.

### Real Main Brain: English current information
- Command: `PYTHONPATH=. SAHIBEX_TASK37_QUERY='Anthropic AI safety bill latest today' python scripts/task37_main_brain_e2e_acceptance.py`.
- Result: **PASS**, exit code 0, 33.2 seconds. The real `MasterBrain.process()` path returned a `VERIFIED` answer after source acquisition, evidence extraction, claim arbitration, freshness and language checks.
- Four distinct publisher hosts selected and fetched: `blockchain.news`, `economictimes.indiatimes.com`, `finance.yahoo.com`, `moneycontrol.com`. Four publisher pages were acquired; all timestamps were fresh for the 24-hour query window (45,265–61,292 seconds old). Claim pipeline retained one corroborated claim and linked it across independent source identities; arbitration `ACCEPTED`, conflict `NO_CONFLICT`, language `MATCH`.
- Protected delete request was blocked before planning/execution; Constitution protection and research routing checks passed.
- Temporary isolated DB only. It contained 49 evidence/knowledge candidates and 3 memory rows, but 0 rows in the dedicated verified-knowledge table. This is recorded as a scope limitation, not misreported as verified-knowledge promotion.

### Real Main Brain: Hindi current information
- Query: `आज Anthropic AI safety bill के बारे में ताज़ा जानकारी`.
- Command explicitly set `SAHIBEX_TRANSLATION_PROVIDER=mymemory` for this one test process only; no production shell/runtime setting was changed.
- First run exposed a runner assertion bug: it required the Hindi fallback even when a valid Hindi verified answer had succeeded. Fixed the assertion to accept either a genuinely verified Hindi-script answer or a safe localized fallback, while requiring final language diagnostics `MATCH`.
- Rerun result: **PASS**, exit code 0, 70.95 seconds. The real Main Brain returned a Hindi answer with verification status `VERIFIED`; translation diagnostics `TRANSLATED_AND_LANGUAGE_CHECKED`; numeric and URL tokens preserved; original English answer retained in traceability. Four publisher pages from the same four distinct hosts passed the 24-hour freshness gate (45,460–61,487 seconds old). Claim arbitration accepted one multi-source claim; language diagnostics `MATCH`; no unresolved conflicts.
- This test did not persist the opt-in translation setting. Temporary isolated DB; 0 rows were promoted into the dedicated verified-knowledge table.

### Controlled self-improvement: integrated live lifecycle
- Exercised `brain.continuous_learning` from a real `MasterBrain()` instance with a temporary persistent audit database.
- Created metadata-only v1 proposal, passed security/regression/verification checks, obtained Mother and explicit human approval, and activated v1. Repeated for v2, activated v2, then performed an approved verified rollback to v1.
- Closed and reopened the SQLite audit database; audit hash chain remained valid and lifecycle events persisted (12 events in the integrated smoke run, including activation commit and rollback completion).
- Separate regression tests prove failed regression blocks activation, missing human approval blocks activation, tampered audit chain blocks activation, and injected activation-commit audit failure restores the previous active version and records recovery.
- **Safety boundary:** this proves controlled metadata/skill-version lifecycle only. No executable code, Constitution, or authority was changed or auto-updated.

### Final regression and static checks
- Focused acceptance/security/self-improvement batch: **309 passed in 10.92s**.
- Focused failure-recovery/search/evidence/conflict/translation batch: **84 passed in 6.07s**.
- Full repository: `PYTHONPATH=. pytest -q` → **1935 passed in 161.07s (0:02:41), exit code 0**.
- `python -m compileall -q core app tools tests scripts`: **PASS**.
- Shell syntax (`start_sahibex_live.sh`, `start_sahibex_background.sh`, `sahibex_supervisor.sh`, `start_sahibex_media_bridge.sh`): **PASS**.
- `git diff --check`: **PASS**.

### Final disposition
**P6 PASS — bounded to verified bilingual research answers and metadata-only controlled self-improvement.** No remaining blocker for that defined acceptance gate. Remaining out-of-scope / future gates: persistent restoration of active skill-version registry across process restart; automatic promotion into the separate verified-knowledge table; executable-code self-update (not enabled for safety); physical Android microphone/speaker, camera/OCR and Accessibility acceptance. Earlier provisional stale-source and language-mismatch results above remain as historical runs; the final fresh-source reruns in this section supersede them for the current gate.


## P6 gap-closure recheck — persistent recovery + verified-knowledge promotion (2026-10-17, latest)

This section supersedes the earlier statements above that the active skill registry was memory-only and that accepted answers could not promote verified knowledge. Earlier live failures remain historical evidence; the results below are the latest post-change checks.

### Persistent self-improvement state and real process restart
- Added `core/brain/self_improvement_state_store.py`: SQLite-backed versioned snapshot with transactional updates, schema validation, SHA-256 integrity checks, and fail-closed behavior for corrupt state.
- `ContinuousLearningImprovement` now restores proposals/skill versions on startup and persists proposal creation, test results, approvals, activation, and rollback. Failed activation/rollback persistence restores the previous state. Startup rejects a tampered audit chain.
- Production defaults wired through `SAHIBEX_SELF_IMPROVEMENT_STATE_DB` in `scripts/start_sahibex_live.sh`, `scripts/sahibex_supervisor.sh`, and `scripts/start_sahibex_media_bridge.sh`, defaulting to `data/runtime/self_improvement_state.sqlite3`.
- Actual OS-process restart acceptance: `tests/unit/test_p6_self_improvement_restart_recovery.py` starts a first Python process to activate v1, a second process to recover v1/activate v2/rollback to v1, and a third process to confirm v1 remains active and the audit hash chain is valid. Dedicated restart suite: **7 passed**.
- Also verified corrupt state rejection, startup audit-tamper rejection, failed state commit recovery, missing approval, failed regression, and rollback recovery.

### Evidence-gated promotion into durable verified knowledge
- `MotherResearchIntegration` now promotes only selected knowledge IDs from a final `VERIFIED` answer when arbitration is `ACCEPTED`, there are no unresolved conflicts, the answer trace is complete/supported/verified, at least two distinct source IDs and linked evidence IDs exist, and the stored candidate has evidence and confidence >= 0.60.
- Unresolved conflicts, unselected conflict participants, `CONFLICTED` lifecycle state, absent evidence, or failed final-answer gates are not promoted. Promotion writes provenance metadata and a `VERIFIED` lifecycle event. A candidate's boolean flag alone is insufficient for verified-only retrieval; lifecycle checks remain active.
- The physical schema uses the `knowledge_candidates` table plus `knowledge_verification_records` lifecycle history (not a separate physical table named `verified_knowledge`). The acceptance runner's `verified_knowledge_rows` count means candidates whose persisted verified flag and lifecycle agree.
- Unit test proves accepted traceable multi-source evidence promotes and is retrievable through `KnowledgeBrain.retrieve(..., verified_only=True)`; unresolved conflicts block promotion.

### Post-change real Main Brain acceptance
- English stable-fact query `What is the capital of India?`: **PASS**, real `MasterBrain.process()`, three publisher hosts acquired, one claim accepted by arbitration and traceability, language `MATCH`, one knowledge candidate promoted, isolated DB reported `verified_knowledge_rows: 1`, `failed_checks: []` (23.30 seconds).
- Hindi stable-fact query `भारत की राजधानी कौन सी है?`: **PASS**, explicit `SAHIBEX_TRANSLATION_PROVIDER=mymemory` for that process only, Hindi output and language diagnostics `MATCH`, arbitration accepted, one candidate promoted, isolated DB `verified_knowledge_rows: 1`, `failed_checks: []` (37.75 seconds).
- Latest current-news attempts also ran. The English Anthropic current-news run and the Hindi Anthropic current-news run were safely rejected because the selected publisher set did not corroborate a claim; Hindi returned a localized fallback with language `MATCH`. These are **expected fail-closed outcomes**, not verified-answer passes; they must not be represented as successful current-news answers.
- Protected delete remained blocked before planning/execution; Constitution unchanged. Live acceptance databases were temporary and production knowledge was not modified.

### Final post-change verification
- Full repository regression after all P6 code/test changes: `PYTHONPATH=. pytest -q` → **1942 passed in 160.30s (0:02:40), exit code 0**.
- Targeted self-improvement, knowledge, traceability, and research integration checks passed; the dedicated restart suite passed with **7 passed**.
- `compileall`, targeted `py_compile`, shell syntax for live/background/supervisor/media-bridge scripts, and `git diff --check`: **PASS**.

### Updated P6 disposition
**P6 PASS for the defined bounded gate:** evidence-backed bilingual answers, safe rejection when live evidence does not corroborate, durable verified-knowledge promotion/retrieval, persistent self-improvement registry across actual process restart, explicit approvals, audit integrity, and rollback recovery. **No P7 work is started by this update.** Executable-code self-update remains intentionally disabled; physical Android microphone/camera/Accessibility acceptance is outside this P6 gate and remains a separate product-release gate.
