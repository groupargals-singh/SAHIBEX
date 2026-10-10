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

## Latest verified state — 2026-10-10
- Full repository regression after bilingual query expansion, CAPTCHA detection, and localized acquisition-failure handling: **1550 passed, 0 failed** in 127.09 seconds.
- Focused search provider + permission tests: **14 passed**; focused DuckDuckGo challenge + search provider tests: **16 passed**; focused research integrity + Master Brain research/learning tests: **17 passed**.
- `python -m compileall -q app core security verification tools tests`: PASS; `git diff --check`: PASS.
- Commits pushed to `main`: `3b128ac` (consolidated work register), `c291bd1` (bilingual discovery and CAPTCHA detection), `d6e97e6` (localized provider failures).
- After bridge restart, health: local model ONLINE, web search ACTIVE, supervisor ONLINE, Android voice bridge HTTP HEALTHY.
- Live quality smoke: curated sky explanation and India capital/history responses succeed with `STRUCTURALLY_VALID`; current AI-security research returns `NOT_EXECUTED` because DuckDuckGo served a CAPTCHA challenge. User-facing Hindi error is now localized and does not expose raw backend internals. This is a known live research blocker, not a verified research success.
- Directly tested Google News RSS with the existing hardened RSS provider: feed acquisition succeeded and returned five current-ish source leads. This proves RSS discovery can work even while DuckDuckGo is challenged; full verified answer synthesis from those leads has not yet been integrated or accepted. Do not mark research complete on RSS discovery alone.
- Current Git tree was clean before this status append; rerun final status after commit.

## Engineering continuation — alternate RSS discovery fallback
- Implemented `core/research/google_news_rss_search_backend.py` as a credential-free discovery fallback using the existing hardened RSS/Atom provider and a fixed Google News RSS host. It returns discovery metadata only; it does not mark feed snippets as evidence or verified facts.
- Runtime search now tries configured DuckDuckGo HTML first and falls back to Google News RSS if the primary backend fails or returns no results. Existing network permission gating remains upstream. No CAPTCHA is bypassed.
- Research pipeline preserves discovery results if publisher fetching fails. Google News wrapper URLs are not passed to the direct-web fetcher because that provider intentionally blocks automatic redirects; they are surfaced only as unverified research leads until publisher content can be safely acquired and verified.
- User-facing failure messages can now include those leads while explicitly labeling them unverified. Added unit tests for fallback backend, result metadata, lead preservation, and localized failure handling.
- Focused suite: **34 passed**. Full repository regression after this integration: **1553 passed, 0 failed** in 118.44 seconds. Compileall and `git diff --check`: PASS.
- Next verification step: restart the bridge and run the real authenticated research smoke. Expected safe outcome if the feed provides only aggregator URLs is `NOT_EXECUTED` plus useful leads, not a verified answer. The research synthesis blocker remains open until publisher pages are safely acquired and corroborated.

## Engineering continuation — relevance filter for RSS leads
- Live Google News RSS discovery returned some AI headlines that did not clearly address safety/security. Added a conservative lexical relevance filter for AI safety/security queries: requires both AI-related and safety/security/risk-related terms. General non-AI-security queries are not forced through this filter.
- Live direct backend probe after filtering: English AI safety/security query returned 3 relevant leads; Hindi query returned 2 leads. This is still discovery-only; publisher article content has not yet been acquired and verified, so no verified answer is claimed.
- Focused RSS/search tests: **13 passed**. Full regression is being rerun against this latest change before committing.

## Live verification after RSS fallback + relevance filter
- Restarted the media bridge from current source and rechecked health: local model ONLINE, web search ACTIVE, supervisor ONLINE, bridge HTTP HEALTHY.
- Re-ran authenticated `/voice` quality smoke: curated Hindi sky answer PASS (`STRUCTURALLY_VALID`); India capital/history curated answer PASS (`STRUCTURALLY_VALID`); AI-security research returns `NOT_EXECUTED` with three topical source leads clearly labelled unverified. Smoke exits nonzero because the research task did not produce a verified answer. This is intentional and must remain visible as an open quality gap.
- Google News RSS discovery now works in the live research route, but publisher-page retrieval and multi-source claim corroboration are still not integrated to completion. Do not report live research as finished.
- Full regression: **1555 passed, 0 failed**; compileall and diff checks passed before the latest commit. Latest source commit pushed: `2d95604`; working tree clean after commit.

## Engineering continuation — bounded publisher redirect resolver (2026-10-10)
- Added `DirectWebResearchProvider.resolve_redirect_url()` as an explicit manual redirect resolver for search-aggregator links. Automatic redirects remain disabled. Each redirect target is scheme/hostname/IP validated before the next request; missing `Location`, private/reserved targets, loops, and excessive hop counts fail closed. Resolver responses are closed and their bodies are not used as evidence.
- Research integration now attempts this resolver only for `news.google.com` discovery wrappers, then sends resolved publisher URLs through the existing direct-web acquisition, ingestion, extraction, and verification chain. If the resolver is unavailable or resolution fails, research remains blocked rather than trusting snippets.
- Added redirect security tests for valid destination, private-IP redirect, missing `Location`, redirect loop, hop limit, and preservation of default automatic-redirect denial.
- Focused provider/search tests: **23 passed**. Full repository regression: **1561 passed, 0 failed** in 111.82 seconds. `compileall` and `git diff --check`: PASS.
- Live device health remains: local model ONLINE, search ACTIVE, supervisor ONLINE, Android voice bridge HTTP HEALTHY. Live quality smoke still passes two curated Hindi tasks but the AI-security research query returns `NOT_VERIFIED` with source leads; smoke exit is **1**. Therefore the redirect resolver alone has NOT completed verified live research. The next blocker is to inspect the real publisher acquisition/extraction/evidence path and achieve traceable, multi-source verification before calling research live.
- No claim is made that SAHIBEX is fully live or that the entire A–AC / E01–E13 / 6P roadmap is complete. Physical microphone/speaker, Android Companion update/pairing/accessibility, vision/OCR, child-brain restart/trust, controlled self-improvement, adversarial integrated acceptance, and historical 417-item reconciliation remain open as listed above.


## Engineering continuation — direct publisher discovery, freshness gates, and page-content scoping (2026-10-10)
- Replaced the runtime RSS fallback for DuckDuckGo CAPTCHA/provider failures with a credential-free Bing News RSS backend. It extracts only the explicit destination URL parameter from Bing's known News redirect endpoint, validates the publisher URL with the existing HTTP(S), hostname, and public-IP checks, rejects listing/category pages, and marks results as discovery-only. Publisher article text is still fetched through the hardened direct-web provider; no feed snippet is promoted to evidence.
- Hardened bilingual query expansion: removed redundant Hindi-to-English synonyms so the expansion for “आज AI सुरक्षा में क्या नया है?” becomes the compact query “latest AI safety security news”. A transient fallback failure for one query variant no longer aborts later variants or discards results from other variants.
- Added explicit publisher publication-time extraction. Modification timestamps are no longer misrepresented as publication dates. For time-sensitive queries, direct-web acquisition now rejects undated or older-than-seven-day publisher pages and category/listing pages. HTML extraction prefers an article/main fragment and records the extraction scope, reducing navigation/related-story noise. If every publisher page is rejected, the pipeline preserves the discovery leads and fails closed rather than synthesizing from snippets.
- Added regression tests for Bing destination URL validation, private destination rejection, spoofed Bing hosts, recency filtering, listing-page filtering, compact bilingual queries, per-variant fallback errors, publication-vs-modification timestamp handling, article-scoped extraction, and time-sensitive page freshness.
- Focused suite: **55 passed**. Full repository regression after these changes: **1582 passed, 0 failed** in 124.74 seconds. Compileall and git diff check: PASS before final documentation/commit.
- Live device state was recovered after the phone-side processes had stopped: local Qwen3-1.7B model ONLINE, supervisor ONLINE, authenticated media bridge HTTP HEALTHY.
- Live authenticated quality smoke: curated Hindi sky and India capital/history responses PASS (STRUCTURALLY_VALID). AI-security research still fails closed as NOT_VERIFIED and shows three publisher leads. A direct diagnostic confirmed the pipeline fetched three current publisher pages and persisted evidence, but the answer aggregator still chose irrelevant/stale text and returned status STALE; no verified research answer is claimed. The next blocker is query-grounded claim selection and independent-source corroboration in answer synthesis/aggregation, not RSS discovery or publisher acquisition.
- Keep Priority 1 research acceptance OPEN until a live answer is query-relevant, grounded in traceable publisher evidence, has acceptable freshness, and passes independent-source corroboration. Do not lower the verification threshold to make the smoke green.


## Engineering continuation — relevance-scoped extraction and latest live acceptance (2026-10-10)
- Added a bounded HTML extraction improvement that ignores common sidebar/related-content class hints, with tag-stack handling to avoid nested ignored-region leakage. Added query-aware filtering for AI safety/security knowledge statements so unrelated page/sidebar claims do not enter that specialized answer path.
- Focused direct-web, integration, search, RSS, and answer-pipeline suite: **35 passed**. Full repository regression: **1584 passed, 0 failed** in 106.58 seconds. `compileall` and `git diff --check`: PASS.
- Live authenticated bridge acceptance: HTTP 200, `success=True`, `STRUCTURALLY_VALID` for a short text interaction. Health check: local model ONLINE, web search ACTIVE, supervisor ONLINE, Android voice bridge HTTP HEALTHY.
- Re-ran the three-query live quality smoke: sky explanation PASS; India capital/history PASS; current AI-security research FAILS CLOSED as `NOT_VERIFIED` after 18.16 seconds, returning two relevant-looking publisher links explicitly marked unverified. Smoke exit code **1**. This remains a real blocker: publisher pages may be acquired, but the end-to-end answer is not yet sufficiently corroborated/verified. Do not lower the threshold or label this verified.
- Commit `4057f6d` (`Filter irrelevant research claims and page navigation`) pushed to `origin/main`; tree was clean immediately after push.
- Next work remains: instrument why extracted publisher evidence fails the answer quality/corroboration gate; add tests for query relevance and independent publisher-domain corroboration; rerun live research until it returns traceable `VERIFIED` evidence or report a specific external block. Other device-only and roadmap-traceability blockers listed above remain open.
