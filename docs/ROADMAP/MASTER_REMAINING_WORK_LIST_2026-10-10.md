# SAHIBEX — Consolidated Remaining Work Register
Date: 2026-10-10
Branch baseline: main

## Purpose and completion rule
This is the single actionable remaining-work register, consolidated from the A–AC roadmap, E01–E13 expansion, 6P overlay, live commissioning list, security boundaries, and current device/research evidence. It does not replace the historical 417-item specification. An item is COMPLETE only when its required implementation, tests, security evidence, and applicable live/device acceptance are recorded. A passing unit test is not proof of a live feature.

## Current verified baseline
- Latest full pytest run: **1544 passed, 0 failed** after the Hindi research response fix.
- Latest source commit pushed: `d552865` (Hindi research failure message localization); preceding `20487a7` adds Hindi sentence boundaries.
- Git tree clean at latest check.
- Local Qwen3-1.7B model: ONLINE.
- Search/research providers: configured and reachable, but live synthesis quality gate fails for a current AI-security query; answer correctly remains NOT_VERIFIED and source leads are returned. **Research is not complete.**
- Supervisor: ONLINE. Authenticated Android media bridge `/health`: HTTP healthy.
- Smoke test results: two curated Hindi factual questions return STRUCTURALLY_VALID; a live/current research question remains NOT_VERIFIED. STRUCTURALLY_VALID is a format/contract status, not a universal truth guarantee.
- Physical phone speech recognition → relay → audible TTS is not verified in this session. Companion update/pairing and device permission acceptance remain user/device gates.
- Vision/OCR is not live: a text-only local model is present; no verified image-understanding path has been accepted.
- Exact historical 417-item source has not been recovered. Any reconstructed item matrix must be labelled `RECONSTRUCTED — NOT THE HISTORICAL ORIGINAL` and must not be presented as exact historical coverage without user approval.

## Priority 0 — Protect system authority and working state
- [x] Keep constitution immutable to autonomous runtime.
- [x] Keep protected write/delete/execute/network/credential/system-change/financial/self-update/external-control operations behind permission/approval boundaries.
- [x] Preserve existing source files, data, model, and local token; never expose pairing token in logs or chat.
- [ ] Run final integrated adversarial gate against the actual current runtime (not just unit tests).

## Priority 1 — Live answer quality and research (critical blocker)
- [x] Fail closed when verified evidence is missing; never label unsupported research VERIFIED.
- [x] Strip active/navigation HTML from extracted visible content.
- [x] Bound extraction size and finding count.
- [x] Recognize Hindi danda `।` and double danda `॥` sentence boundaries; regression tested.
- [x] Match insufficient-evidence message to Hindi/English query script; regression tested.
- [ ] Diagnose and fix the current research-query path that finds weak/irrelevant source leads and cannot synthesize a verified answer for current AI-security research.
- [ ] Implement auditable claim-to-evidence linking across independent sources; deduplicate mirrors/same publisher; track publisher/domain and publication date.
- [ ] Add conservative conflict handling and freshness checks for current-event claims.
- [ ] Add source-quality/relevance scoring with explainable factors; do not promote confidence by arbitrary threshold changes.
- [ ] Add Hindi/English query expansion or translation only with traceable original query, expanded queries, and tests; never silently change the user's intent.
- [ ] Return verified answer with citations when evidence supports it; otherwise return concise uncertainty + useful leads. Never call source leads verified conclusions.
- [ ] Add golden live-research acceptance cases for current news, stable facts, conflicting sources, stale sources, empty search, inaccessible pages, Hindi and English.
- [ ] Improve research latency and ensure bounded cancellation/timeouts and clean resource cleanup.

## Priority 2 — Reasoning, response quality, and recovery
- [ ] Test intent detection for Hindi, Hinglish, English, compound requests, ambiguous tasks, and coding requests.
- [ ] Verify answer verification status reflects evidence semantics rather than structural validity alone.
- [ ] Add hallucination/conflict/uncertainty checks to the user-visible final answer path.
- [ ] Test retry/replan limits and ensure no infinite retry loops.
- [ ] Verify that failures preserve task state, useful partial results, and actionable next steps.
- [ ] Benchmark local Qwen3-1.7B answer quality/latency on a fixed Hindi/English question set; record limitations rather than overstate capability.

## Priority 3 — Memory and learning
- [x] Exact high-confidence project-codename recall path exists with ambiguity/type/confidence guards.
- [ ] Verify memory write/read/retrieval/de-duplication, timestamps, provenance, expiry, and conflict resolution in one integrated live flow.
- [ ] Ensure unverified research cannot be promoted to trusted long-term memory.
- [ ] Verify forgetting/cleanup does not delete protected data or corrupt identity/authority state.
- [ ] Test learning from success/failure outcomes without treating prompt injection or user-provided documents as instructions.
- [ ] Verify persistent memory recovery after process restart and backup restore.

## Priority 4 — Controlled self-coding / self-improvement
- [x] Proposal/test/approval/activation/rollback metadata path has focused commissioning evidence.
- [x] Persistent append-only child self-improvement audit store and final persisted-audit gate exist.
- [ ] Wire persistent audit into the actual production self-improvement executor and prove every accept/block decision is recorded.
- [ ] Run a harmless reversible skill change end-to-end: proposal → isolated sandbox → regression → security review → explicit human approval → activation → observation → rollback.
- [ ] Prove invalid tests, missing audit, missing approval, tampered hash chain, or failed rollback all fail closed.
- [ ] Prove autonomous runtime cannot execute arbitrary generated code outside the sandbox, grant itself authority, or modify the Constitution.
- [ ] Add backup/recovery and a kill switch for any live improvement job.

## Priority 5 — Specialist / child brains and orchestration
- [x] Specialist manager, capability profiles, trust/lifecycle boundaries, and persistent child identity registry are implemented.
- [ ] Create a real persistent specialist child through the Mother Brain at runtime; restart process and verify identity/parent binding/capabilities/trust survive.
- [ ] Verify isolated memory, source attribution, parent-child message validation, suspension/resume/replacement/retirement after restart.
- [ ] Run specialist research/coding/business tasks through the same permission and verification gates as the Mother Brain.
- [ ] Reconcile 6P-13..29 test milestones with the official 6P-1..12 roadmap and A–AC architecture before treating them as official phases.

## Priority 6 — Android voice / companion
- [x] Authenticated localhost relay-to-MasterBrain HTTP E2E works; health endpoint healthy.
- [x] Native Companion voice UI source and APK exist; staged APK hash was verified in the prior session.
- [ ] Update installed Companion through Android installer confirmation; verify installed version, then pair without exposing token.
- [ ] Run actual speech recognition → authenticated relay → MasterBrain response → audible Android TTS round trip.
- [ ] Test Hindi and English, silence, cancellation, empty transcript, denied permissions, network/bridge unavailable, timeout, and recovery.
- [ ] Verify no background recording; microphone access must be visible, consented, and user-controlled.
- [ ] Verify TTS playback and UI state on the physical phone; HTTP success alone is insufficient.

## Priority 7 — Vision / OCR / multimodal
- [ ] Choose and install a compatible OCR or image-understanding component within phone RAM/storage constraints.
- [ ] Add explicit-consent image acquisition, MIME/hash/size validation, temporary storage policy, and deletion behavior.
- [ ] Integrate OCR/vision outputs as untrusted evidence with provenance, not as instructions.
- [ ] Test blurry/blank/rotated/malformed/oversized images, Hindi text, sensitive documents, and uncertainty.
- [ ] Complete camera/image → OCR/vision → grounded answer end-to-end. Do not route images to the text-only Qwen model as if it can see.

## Priority 8 — Android Accessibility / computer control
- [x] Gated computer-control implementation and protocol/security tests exist.
- [ ] Install/update Companion and enable its Accessibility service on-device with user consent.
- [ ] Re-run current-device UI tree, tap, typing, key press, screenshot, emergency stop, audit, and denied-permission tests.
- [ ] Prove every protected device action has explicit user authorization and visible audit evidence.
- [ ] Test app/process restart, bridge disconnect, stale UI coordinates, unexpected dialogs, and emergency stop.

## Priority 9 — Security, integrity, operations
- [x] Research source HTML parsing, extraction bounds, permission gates, nonce/authenticated bridge, audit/hash-chain components, checkpoint and child identity checks exist.
- [ ] Run current cross-layer prompt-injection, hostile web content, SSRF, path traversal, secret leakage, replay, unauthorized network/write/delete/execute, child privilege escalation, emergency-stop, corrupt checkpoint, memory-amplification and rollback tests against integrated runtime.
- [ ] Verify supervisor restart policy, crash loops, stale PID handling, bounded logs, model unavailable, disk-full and low-memory recovery.
- [ ] Verify backups can actually restore a known-good state without overwriting user work.
- [ ] Add bounded queue/backpressure for long-running research and background workers; ensure tasks can be cancelled and resumed.
- [ ] Verify local-only endpoints stay bound to loopback and credentials never appear in process output or audit logs.

## Priority 10 — Historical roadmap and requirement traceability
- [ ] Retry source recovery only in permitted local repository/Git/backup sources; do not invent a historical 417 list.
- [ ] If original remains unavailable, maintain a separate explicitly reconstructed candidate baseline and obtain user approval before calling it authoritative.
- [ ] Map every baseline item to A–AC phase, E01–E13 extension if relevant, source files, dedicated tests, security evidence, live evidence, and status.
- [ ] Reconcile phases G/K/T/U/V/AC against available project intent/specs.
- [ ] Map E01–E13 into A–AC without duplicate counting.
- [ ] Reconcile 6P-1..29 tests and official milestone definitions.
- [ ] Report item counts by COMPLETE / IMPLEMENTED-PENDING-VERIFICATION / PARTIAL / BLOCKED / NEEDS-RECONCILIATION; do not claim exact historical completion without the source baseline.

## Priority 11 — Final integrated live acceptance
- [ ] Text-only everyday task: understand → reason → answer → verify.
- [ ] Research task: acquire multiple independent sources → extract → verify claims → cite answer or fail safely.
- [ ] Protected action: deny without permission; allow only after valid explicit approval; audit outcome.
- [ ] Harmless write/read/delete: sandboxed test data only, with permission and recovery verification.
- [ ] Memory recall and learning: provenance-aware write/read across restart.
- [ ] Specialist child task with trust, isolated memory, and parent boundary.
- [ ] Self-improvement reversible cycle with persistent audit and rollback.
- [ ] Phone voice and Accessibility acceptance after physical setup.
- [ ] Vision acceptance only after real OCR/model path is installed.
- [ ] Run full pytest, legacy-main regression, compileall, diff check, health check, and record exact outputs/commit.

## Priority 12 — Publish truthful completion report
- [ ] Report engineering readiness separately from live-device acceptance and historical 417 coverage.
- [ ] State every remaining blocker and the user/device action needed.
- [ ] Never claim autonomous continuous operation after chat ends unless an actual device-side job/supervisor has been configured and verified.
- [ ] Never claim consciousness, biological equivalence, or universal correctness.

## Device-only gates that cannot be honestly completed by code-only changes
1. User confirms Android installer update and pairing.
2. User grants microphone/speech/Accessibility permissions where needed.
3. Real speaker/microphone and screen behavior are observed on the phone.
4. If vision needs a large model or incompatible package, hardware/storage/source compatibility must be checked before install.
5. If original 417 source is absent, the user must approve any reconstructed candidate before it becomes the working baseline.

## Session rule
Work in priority order. For each fix: reproduce → patch → focused regression → full regression where practical → live test if safe → update this register → commit/push. Keep unresolved blockers visible. This register is a work queue, not a claim that its items have all been completed.

## Engineering continuation — bilingual discovery + search failure visibility
- Added a conservative Hindi keyword-expansion path in `core/research/search_provider.py`: original query is searched first; a second query is created only when known Hindi topical terms can be expanded; original wording is retained and each result records its `discovery_query`. Query result capacity is split across variants so the original query cannot crowd out the English expansion. This is discovery assistance only, not answer translation or verification.
- Added bilingual-query regression coverage, including a result-budget case. Search-provider + permission tests: **14 passed**.
- Live investigation found DuckDuckGo returned HTTP 202 anti-bot/CAPTCHA HTML (`anomaly-modal`) instead of result HTML. The old parser silently treated this as zero results, hiding the actual provider failure. Added explicit anti-bot challenge detection with an actionable `RuntimeError`, plus tests for challenge detection and normal HTML parsing. Focused combined search tests: **16 passed**.
- Important remaining limitation: a live provider may still block automated searches. This fix makes the failure visible; it does not bypass CAPTCHA or claim live research success. Use a permitted, configured alternative search backend for dependable research.

## Engineering continuation — user-safe provider failure responses
- Live authenticated voice smoke reproduced the provider failure after the search backend change. Before the latest fix, the raw English DuckDuckGo CAPTCHA error appeared directly in the Hindi answer (`NOT_EXECUTED`).
- Added `_execution_failure_message()` in `core/brain/mother_research_integration.py`. Failed acquisition now returns a language-matched, user-safe explanation and keeps the raw error only in the structured error field for diagnostics. The message clearly says no unverified conclusion was generated and gives an actionable next step.
- Focused research integrity + Master Brain research/learning regression: **17 passed**.
- Remaining research blocker is external/backend availability and robust verified synthesis. The current DuckDuckGo HTML backend is being challenged; this is now detected rather than silently treated as an empty result set. Do not bypass the challenge. Configure an approved search API/backend for dependable live research.
