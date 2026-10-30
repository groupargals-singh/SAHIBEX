# SAHIBEX Architecture & End-to-End Data-Flow Audit
Date: 2026-10-10
Status: ACTIVE — implementation and live acceptance are not yet complete

## Audit method
Inspected the current Termux working tree, master/reconciled roadmap, reconstructed 417-requirement matrix, remaining-work register, MasterBrain dispatch path, model gateway, research provider registry/pipeline, child-brain lifecycle contracts, Android Companion source, and current modified-file state. Existing modifications and untracked files were preserved. This is a code/contract audit, not a claim that every hardware path has been exercised.

## End-to-end data flow observed in code

    Text UI / authenticated Android Companion API
      -> MasterBrain.process()
         -> input/state handling + deterministic safe fast paths
         -> intent/action/risk + Constitution/authority/permission/verification gates
         -> retrieve context from persistent memory/knowledge store
         -> Mother Reasoning -> Internal Brain Team dispatch
         -> Planner/Orchestration creates task plan
         -> route by intent/action:
            SEARCH -> MotherResearchIntegration
              -> provider registry/router
              -> ResearchAcquisitionPipeline permission gate
              -> search discovery (metadata/snippets are untrusted leads)
              -> URL validation / publisher fetch / freshness checks
              -> ingestion + deduplication + persistent research storage
              -> extraction -> evidence persistence -> verification
              -> claim/source arbitration + answer synthesis
              -> final answer accepted only when evidence status is VERIFIED
            LEARN -> MotherLearningIntegration + research result gates
            READ/WRITE/DELETE/EXECUTE -> Tool Brain + permission gateway
              -> bounded executor -> result verification/audit/recovery
            general/coding -> MotherOperationalIntegration
              -> Memory/Knowledge context -> ModelGateway -> selected provider
              -> response-language/answer-quality checks
         -> result/status/audit/context recording
         -> user-facing result

Cross-cutting controls: immutable Constitution, user authority, explicit approval for protected operations, prompt-injection defenses, child trust/identity boundaries, audit/provenance, fail-closed verification, and recovery controls.

## Findings — real gaps, not just missing filenames

1. **Research runtime configuration defect found and patched:** production launchers defaulted to duckduckgo_html, although the maintained audit says live DuckDuckGo HTML search is receiving HTTP 202 anti-bot/CAPTCHA responses. A credential-free Google News RSS backend already existed and had prior successful discovery evidence, but the production provider factory did not expose it as a selectable backend. Added google_news_rss registration with the existing Bing News RSS fallback and switched app/live/health/supervisor/media-bridge defaults to it. Search results remain discovery-only; no verification threshold was relaxed.
2. **Misleading status text found and patched:** CLI status said Child Brain was “NOT BORN (future DNA/spec only)” despite the persistent child registry, lifecycle, and specialist-manager code being present. Status now distinguishes framework presence from unverified persistent-child end-to-end deployment.
3. **Research remains functionally incomplete until a live query yields traceable VERIFIED evidence.** Publisher HTTP 200 alone is not sufficient; acquisition, extraction, date/relevance, claim support, independent-source corroboration, and final synthesis must all succeed.
4. **Vision is a contract, not a complete perception path:** core/brain/vision.py explicitly states it does not access a camera or process images; vision_reasoning.py also states it does not run computer vision. A compatible OCR/multimodal inference path and live acceptance are still required.
5. **Voice source exists, but device acceptance is separate:** Android Companion source contains speech recognition and TTS calls, while physical microphone-to-relay-to-audible-speaker behavior still needs installed-app, permission, and on-device confirmation.
6. **Child Brain lifecycle has contracts and persistent identity registry, but end-to-end persistence is not yet proven:** a real child must be created through Mother Brain, run an authorized task, restart the process, restore identity/parent/capabilities/trust, and pass lifecycle/audit tests.
7. **Controlled self-improvement is partial:** proposal/approval/sandbox/test/rollback components exist, but the production executor still needs an integrated harmless reversible change with durable audit, hash integrity, explicit human approval, and verified rollback.
8. **Requirement traceability is incomplete:** exact historical 417-item source was not recovered. G/K/T/U/V/AC and the E01–E13 / 6P-13..29 overlays remain reconciliation work; no exact 417/417 completion claim is valid.
9. **Operational observability/performance remain acceptance gates:** use structured per-stage telemetry, bounded retries/timeouts, cancellation, task checkpoint/resume, crash/disk/low-memory tests, and repeatable latency/quality measurements. A healthy HTTP endpoint or passing unit suite is not proof of a complete live Brain.

## Patch and verification recorded in this audit
- Provider factory now supports explicit SAHIBEX_SEARCH_BACKEND=google_news_rss; uses Google News RSS discovery with the existing Bing News RSS fallback.
- Defaults updated in app/main.py, scripts/start_sahibex_live.sh, scripts/sahibex_health.sh, scripts/sahibex_supervisor.sh, and scripts/start_sahibex_media_bridge.sh.
- Added provider-registry regression test for Google News RSS selection.
- CLI status text now truthfully distinguishes Child Brain framework presence from unverified persistent-child E2E.
- Focused runtime-provider/live-research tests: 5 passed; compileall, shell syntax checks, and git diff --check: passed.
- Live research test with the new backend is running; its final outcome must be appended before calling the research configuration patch functionally verified.

## Acceptance checklist — open until evidence is recorded
- [x] Trace main text request through MasterBrain, gates, reasoning, planning, and task dispatch in source.
- [x] Trace research stages from discovery through evidence and answer gate.
- [x] Identify and patch production default search-backend mismatch.
- [x] Correct misleading Child Brain status label.
- [ ] Confirm live Google News RSS discovery through the permission-gated research runtime.
- [ ] Produce at least one claim-level corroborated VERIFIED current-research answer or record the exact failing stage.
- [ ] Re-run broad regression after the current patch set.
- [ ] Physical Android mic/speaker acceptance.
- [ ] Image/camera -> OCR or multimodal model -> grounded answer E2E.
- [ ] Persistent Child Brain create/run/restart/restore E2E.
- [ ] Controlled self-improvement approval/sandbox/audit/rollback E2E.
- [ ] Integrated adversarial security and recovery acceptance.
- [ ] Reconcile all 417 baseline requirements from an authoritative source, or obtain approval for a separately labelled reconstructed baseline.

## Truthful completion rule
SAHIBEX has a substantial modular brain/runtime foundation. It is not yet accepted as a fully integrated, universally capable “Human-Brain AI.” Mark a capability COMPLETE only when implementation, permission boundaries, dedicated tests, source/data-flow traceability, and applicable live/device evidence all pass.

## Follow-up live probe and diagnostic instrumentation — 2026-10-10
- A real permission-confirmed MasterBrain query was run with the new Google News RSS backend: 53.92 seconds, 3 source leads returned, final status NOT_VERIFIED. The configuration change improved/changed discovery output but did not fix claim-level evidence verification. Do not call the research feature fixed.
- The visible result confirms the fail-closed response is still active and labels links as unverified. No evidence threshold was weakened.
- The first probe showed a diagnostics gap: stage-level publisher acquisition/extraction/evidence counts existed inside ResearchPipelineContext but were not surfaced in the MasterBrain failure metadata. Added a bounded diagnostic summary to MotherResearchResult and propagated it into the MasterBrain research-failure metadata. It includes counts/status and short error strings, but intentionally excludes page bodies and credentials.
- Added regression coverage for diagnostic bounds and page-body exclusion. Focused tests are being rerun before a second permission-confirmed live query.

## Root-cause fix under live verification — publication timestamp provenance
- Stage telemetry isolated a specific pipeline defect: 10 publisher URLs were requested, only 3 were acquired, and the other 7 were rejected because the publisher HTML lacked an explicit publication date. The RSS discovery records already carried publication timestamps, but the pipeline discarded that metadata when it converted discovery results into a plain list of URLs.
- Preserved exact-URL RSS discovery timestamp metadata through Google News wrapper resolution and into the direct publisher acquisition request.
- Updated the direct-web provider to use a discovery timestamp only when publisher publication metadata is absent, the timestamp is timezone-aware and within the 7-day window, the URL matches exactly, and the discovery backend is explicitly allow-listed (Google News RSS, Bing News RSS, or Brave). A publisher-supplied stale date still causes rejection; stale/naive/unknown timestamps do not pass. Publisher page content is still fetched and used as evidence; snippets remain discovery-only.
- Added tests that a fresh explicit RSS timestamp can fill a missing publisher date and that a stale RSS timestamp is rejected. Focused research/web/date regression: **52 passed, 0 failed**; compileall and diff checks passed.
- Improved stage diagnostics to report nested answer status, count of claims with multi-source support, answer arbitration and traceability state. This should distinguish a fetch/freshness problem from an evidence-linking/arbitration problem on the next live probe.
- The post-fix permission-confirmed live research probe is in progress. Do not call the root-cause fix complete until the new acquisition counts and final verification status are observed.

## Live re-test after timestamp provenance fix — 2026-10-10
- A permission-confirmed live research run now acquired **9 of 10** publisher pages (previously 3 of 10) after preserving RSS timestamps and parsing both ISO-8601 and RFC-2822 timestamps. One page remained correctly rejected because its publisher publication date was missing/outside the window.
- The freshness fix is therefore functionally verified at the acquisition stage. It does **not** fix end-to-end research answer acceptance: the final status remains NOT_VERIFIED.
- Stage diagnostics show 203 findings/evidence records across 9 documents, but 0 query-result matches after the current claim filters, 0 aggregation results, 0 answer claims, and 0 multi-source quality claims. Traceability reports NO_KNOWLEDGE and arbitration rejects the answer. This is the next real blocker: discovery/fetch works substantially better, but current-research claim relevance and independent-source linking do not produce a supported claim set.
- Do not lower the multi-source corroboration gate. Next fix must establish which filter removes all candidates and improve relevance/claim matching or discovery coverage, with regression cases for same-claim independent sources and unrelated single-source headlines.
- The live result is still a safe NOT_VERIFIED response; research remains NOT COMPLETE.

- Additional runtime-default audit found one missed override: tools/android_companion_media_server.py also defaulted to duckduckgo_html, and the currently running bridge process still had the old inherited environment. Updated the server-side default to google_news_rss as well. The running bridge/supervisor must be restarted after regression so the active process picks up the new default; current health checks alone do not prove the new backend is active in the existing process.

## Final acceptance snapshot — 2026-10-10
- Full grouped regression after the research timestamp/diagnostic changes: tests/unit **1355 passed, 0 failed** (45.39s); tests/test_legacy_main_script_regression.py **286 passed, 0 failed** (67.92s). Combined executed groups: **1641 passed, 0 failed**. compileall, shell syntax checks, and git diff --check passed.

## Main Brain architecture audit follow-up — 2026-10-16
- Re-traced current MasterBrain wiring for injected/default Operational, Research, and Learning integrations, plus the persistent retrieval objects used by OperationalMemoryKnowledge, MemoryBrain, and KnowledgeBrain.
- **Bug fixed: split persistent data plane.** If a caller injected both Operational and Research integrations with different database paths, MainBrain could previously initialize successfully while research wrote to one database and retrieval read another. MainBrain now rejects that unsafe explicit mismatch with a clear ValueError. Default-created Operational/Research wiring now reuses the same storage object, including in-memory stores.
- **Bug fixed: custom operational storage did not flow into default research ingestion.** When an explicit Operational integration was supplied without a Research integration, MainBrain now builds Research using that operational storage. MotherResearchIntegration also derives the acquisition/ingestion database path from its selected storage, instead of silently hard-coding the default database path.
- **Bug fixed: split learning integration.** MainBrain now rejects an explicitly injected MotherLearningIntegration that is bound to a different MotherResearchIntegration instance, preventing research and learning from silently using different evidence/knowledge pipelines.
- Regression coverage added for rejecting split explicit databases and rejecting a learning integration bound to another research instance. Existing tests also assert the default research/operational/memory/knowledge storage object is shared.
- Focused architecture/security/legacy integration regression: **309 passed**. Final full suite after the fixes: **1817 passed, 0 failed in 169.04s**. py_compile and git diff --check passed.
- This is a code-level architecture/wiring pass, not final live acceptance. Real-source current-research acceptance remains open; see Task 36 in the master list. Camera/microphone physical acceptance, persistent child-brain restart acceptance, and controlled self-improvement end-to-end acceptance remain open as listed above.

## Complete data-flow audit — 2026-10-16 (Task 24)
- Traced the main request path through MasterBrain intent/action classification, Constitution and PermissionGateway decisions, safety verification, retrieval, reasoning/department dispatch, Research/Learning/Operational branches, final status propagation, context recording, persistent memory, and continuous-learning telemetry.
- **Critical integration bypass found:** OperationalMemoryKnowledgeIntegration queried ResearchStorage.retrieve_knowledge() directly. This bypassed KnowledgeBrain's persisted verification-lifecycle and unresolved-conflict filters. A candidate with stale verified=True metadata or an unresolved conflict could therefore be passed into operational model context.
- **Fix:** OperationalMemoryKnowledgeIntegration now delegates knowledge retrieval through KnowledgeBrain's trust boundary. Ordinary operational context defaults to verified_knowledge_only=True; unverified candidates remain accessible only when a caller explicitly requests review mode. Latest persisted lifecycle status and unresolved conflict records are checked before candidates are returned.
- Regression tests added for stale verified=True followed by an UNVERIFIED lifecycle event, and for an unresolved conflict between candidates. Retrieval fixtures now include persisted VERIFIED lifecycle events rather than relying on the candidate flag alone.
- Focused regression: **32 passed, 0 failed** across operational retrieval, knowledge lifecycle, MasterBrain Research/Learning flow, and end-to-end operational tests.
- Full-suite verification after the fixture correction: **1818 passed, 0 failed in 123.06s**. Python compilation and git diff --check both passed. The first full run correctly exposed one legacy fixture that set verified=True without a persisted VERIFIED lifecycle event; the fixture was corrected to record that event, then the full suite was rerun successfully.
- Task 24 code/data-flow audit is complete for the inspected request, retrieval, Research/Learning/Operational, memory, and verification paths. This is not overall Main Brain acceptance: restart/recovery and live-source acceptance remain separate gates, including Task 36.
- Restarted the background supervisor and Android media bridge so the active process inherited the new default. Health check reports local model ONLINE, web search ACTIVE, active providers direct_web/document/rss_atom/search, Android voice bridge HTTP HEALTHY, and public tunnel /health HTTP 200. The active bridge process environment is confirmed as SAHIBEX_SEARCH_BACKEND=google_news_rss and SAHIBEX_MODEL_PROVIDER=local.
- Final live quality smoke through the active Companion bridge: the two ordinary Hindi questions passed STRUCTURALLY_VALID (0.84s and 0.17s). Current AI-security research took 52.69s and remained NOT_VERIFIED, with source leads explicitly marked unverified. The smoke exits 0 because fail-closed behavior is expected; it is not a verified-research pass.
- Therefore: the research freshness acquisition bug is improved (9/10 publisher pages fetched), but research synthesis/corroboration remains the top functional blocker. Vision, physical mic/speaker acceptance, Android device control, persistent child-brain E2E, production self-improvement E2E, and authoritative 417-item traceability also remain open. SAHIBEX is live at the service/relay level, but is not yet a fully accepted human-brain AI.

## Architecture-first re-audit — 2026-10-11
- Re-scanned 336 Python files under `core`, `app`, `tools`, and `verification`: zero AST parse failures and zero unresolved internal imports. A static import graph from four major roots reaches 150 modules and leaves 186 outside that graph. This is a review signal, **not** proof that 186 modules are broken: runtime registrations, test-only helpers, CLI tools, and intentionally optional expansion modules can be outside static reachability. Do not auto-wire them without contracts and tests.
- Inspected MasterBrain initialization and request dispatch. Main path instantiates intent/context/planner/constitution/permission/approval/verification, operational/reasoning/research/learning integrations, memory/knowledge, Tool Brain, autonomous-work brain, security/emergency-stop, lifecycle, child manager, and internal role registry. Internal role registry defines 10 roles and MasterBrain registers all 10 handlers; actual role dispatch is explicit and requires upstream authorization plus request verification. The internal role registry does not create independent child brains or grant permissions.
- Executed `tests/unit`, `tests/security`, and `tests/test_legacy_main_script_regression.py` after the current working-tree changes: **1641 passed, 0 failed** in 110.02 seconds. Focused research answer/integrity/pipeline/content-filter suite after the current relevance patch: **44 passed, 0 failed**.
- New concrete research-flow defect found: `_ai_safety_claim_is_relevant()` required literal safety/security vocabulary. A current claim such as “Anthropic AI agents go rogue…” was dropped before evidence/source corroboration, because it described unsafe behavior without those exact words. Expanded only the bounded relevance vocabulary (rogue/misuse/unsafe/harmful/deceptive/agent behavior and Hindi equivalents); did not change evidence, freshness, or independent-source verification thresholds. Added regression proving rogue-agent claim survives while a generic model-launch claim is still filtered.
- Live acceptance after this filter patch is pending. Do not mark research complete unless the live query produces a claim-level, traceable `VERIFIED` answer; `NOT_VERIFIED` remains a safe failure, not a pass.
- Architecture gaps remain: vision/OCR has no accepted live image-processing path; physical mic→relay→speaker acceptance is unconfirmed; Android Accessibility control, persistent child create/run/restart/restore, production self-improvement approval/sandbox/rollback, adversarial integrated runtime checks, and historical 417-item traceability are still open. These are integration/acceptance gaps, not missing filenames alone.


## Follow-up acceptance correction — evidence is not truth verification — 2026-10-11
- ResearchPipelineIntegration previously emitted `verification.status="verified"` when at least one evidence record existed. That name overstated what this stage actually did. It now emits `status="evidence_available"` and `truth_status="not_evaluated"`; answer synthesis checks evidence availability, while truth acceptance remains downstream.
- Added regression coverage for the available-evidence/not-yet-truth-verified distinction. Focused suite: 50 passed. Full regression is running after this patch.
- Latest live smoke before this patch: ordinary Hindi responses were structurally valid; the current AI-security research query took 60.93 seconds and returned NOT_VERIFIED with source leads explicitly labelled unverified. The smoke's attempt to read nested research diagnostics returned an empty object; response-shape propagation is a newly recorded observability gap. Do not call research complete until both the diagnostics are inspectable and a live answer passes claim-level independent-source verification.


## Relay diagnostics acceptance — 2026-10-11
- Identified why the live smoke printed `RESEARCH_DIAGNOSTICS {}`: `tools/android_companion_media_server.py` did not forward any diagnostics from the MasterBrain result. It now forwards only the bounded, secret-free `research_diagnostics` object prepared by MotherResearchIntegration; the smoke test reads that explicit field.
- Added a regression for relay diagnostic forwarding. Focused suite after this change: 45 passed; compileall and diff checks passed. Full repository regression just before this relay-only patch: 1644 passed.
- Restarted the relay under the existing supervisor and confirmed its localhost health endpoint. Live quality smoke is being rerun to verify the diagnostic propagation and record the exact remaining research stage failure.


## Research relevance filter root cause and patch — 2026-10-11
- With diagnostics propagated through the relay, the live query showed 9/10 publisher pages fetched and 320 evidence records, but 0 query matches/aggregation results. Read-only inspection of persisted records found relevant sentences (e.g. employee safety concerns) were filtered because the claim sentence omitted “OpenAI/AI” even though its linked article title clearly named OpenAI and AI safety researchers.
- The relevance filter now uses linked source-title context to establish the AI subject while requiring safety/event signal in the extracted claim itself. This avoids admitting unrelated sidebar claims merely because a page is relevant. A regression covers both the contextual claim and the unrelated sidebar exclusion.
- Focused research answer/integration/integrity tests: 40 passed; compileall and diff checks passed. Full repository regression is running. Live acceptance after bridge restart is still pending; no VERIFIED claim is made yet.


## Full regression after relevance-context patch — 2026-10-11
- Full grouped regression: **1645 passed, 0 failed** in 102.59 seconds. Focused answer pipeline/research integration/integrity: 40 passed. Targeted compileall and diff checks passed.
- Media bridge restarted under supervisor and health returned HTTP 200. Live smoke is rerunning against the new relevance filter; current-news verification remains pending until that query returns its actual diagnostics.


## Corroboration-stage telemetry — 2026-10-11
- Reproduced the live query against the persisted current-run candidates: 242 candidate knowledge records → 43 relevance-filter survivors → 0 claims with two distinct publisher identities. The earlier single `retrieval_matches=0` field conflated post-corroboration output with pre-corroboration relevance.
- Added separate pre-corroboration and post-corroboration counts to ResearchAnswerPipelineResult and MotherResearchIntegration diagnostics, with regression coverage. Focused suite: 41 passed; targeted compileall/diff checks passed. Full regression is running.
- No verification threshold was lowered. The next blocker is discovery/linking of the same claim across independent publishers; a safe NOT_VERIFIED answer remains the correct outcome until that is solved.


## Regression result after corroboration-count telemetry — 2026-10-11
- Full grouped regression: **1646 passed, 0 failed** in 146.54 seconds. Focused suite: 41 passed; compileall and diff checks passed.
- Bridge restarted under supervisor; live smoke is running with new `relevance_candidate_count` and `corroborated_candidate_count` diagnostics so the remaining stage is explicit.


## Publisher-diversity selection fix — 2026-10-11
- Diagnosis: source selection attempted to diversify hostnames before resolving Google News wrapper links, so wrappers all appeared to come from `news.google.com`. The research job then fetched 9 pages but only retained a small set of distinct publisher identities for corroboration.
- Added a bounded safe-resolution stage before publisher-host diversity selection (20 candidate URLs max, 10 selected URLs max), preserving source timestamp metadata only for the exact resolved URL. Added a regression for same-publisher wrappers versus distinct publishers.
- Focused suite: 42 passed; full regression is running. Live verification after bridge restart remains pending.


## Regression result after publisher-diversity refactor — 2026-10-11
- Full grouped regression: **1647 passed, 0 failed** in 143.01 seconds. Focused research pipeline suite: 42 passed. Compileall and diff checks passed.
- Media bridge restarted under supervisor and health confirmed. Fresh live smoke is running with resolved-publisher diversity and pre/post-corroboration telemetry.


## Selected-publisher telemetry — 2026-10-11
- Added `resolved_candidate_url_count` and up to 10 selected publisher hostnames to bounded research diagnostics, allowing the next live run to distinguish insufficient discovery diversity from claim-linking failures.
- Full regression: 1647 passed; latest focused suite: 48 passed; compileall and diff checks passed. Bridge restarted and the newest live smoke is running.


## Conservative cross-publisher paraphrase matching — 2026-10-11
- The remaining zero-corroboration blocker includes a same-event LiveMint/note.com pair whose statements differ in wording but share event-specific terms (AI-generated false police tip). The previous 75% containment plus two-entity requirement rejected this pair.
- Added a conservative headline-context fallback requiring a shared named AI organization, multiple shared event-specific claim tokens, minimum overlap, identical numeric details, and consistent negation. Added positive same-event and negative counterclaim tests. The fallback links evidence only; it does not mark claims verified.
- Focused research pipeline suite: 44 passed. Full regression is running; live acceptance remains pending.


## Full regression after contextual paraphrase matcher — 2026-10-11
- Full grouped regression: **1649 passed, 0 failed** in 142.07 seconds; focused research pipeline: 44 passed; compileall/diff checks passed.
- Bridge restarted under supervisor; current live smoke is testing whether cross-publisher event paraphrases now survive corroboration. Research completion is not yet claimed.


## Follow-up discovery and unresolved-wrapper safety — 2026-10-11
- Live run had only four selected hostnames, one still `news.google.com`, plus 19 relevant claims and 0 multi-source claims. Expanded bounded headline follow-up selection from 3 to 5 distinct queries and made the resolver discard any wrapper that resolves back to `news.google.com` instead of treating it as publisher evidence.
- Added tests for query bound/deduplication and unresolved-wrapper rejection. Focused suite: 46 passed; full regression is running. Live acceptance pending.


## Regression result after five-query follow-up hardening — 2026-10-11
- Full grouped regression: **1651 passed, 0 failed** in 146.47 seconds. Focused suite: 46 passed; compileall and diff checks passed.
- Media bridge restarted under supervisor; latest live smoke is testing the broader corroboration discovery and contextual claim matcher.


## Multi-source discovery wiring — 2026-10-11
- Configured search now merges Google News RSS, Bing News RSS and DuckDuckGo HTML results; a pre-configured Brave key adds Brave Search as a fourth independent discovery backend. The fan-out interleaves engines, deduplicates tracking variants, records provenance and isolates individual provider outages.
- Unit coverage added for cross-engine deduplication, diversified ordering, partial-provider failure, all-provider failure and runtime wiring. All retrieved items stay unverified discovery leads until publisher content/evidence checks accept them. Compileall and diff check passed; full regression running; live end-to-end acceptance pending.


## Research latency hardening — 2026-10-11

- Multi-source discovery now fans independent search engines out concurrently and collects results in configured order for deterministic merging.
- A malformed-port or non-HTTP(S) URL is skipped instead of aborting the merge.
- Google News wrapper resolution is bounded and concurrent; an individual broken wrapper is isolated and never promoted to publisher evidence.
- Current-news work is bounded to one English expansion, two headline corroboration searches, and at most four publisher pages per pass to avoid repeated multi-minute search/fetch chains. Evidence thresholds are unchanged: search snippets remain discovery-only and the publisher content plus verification gate are still required.
- Focused regression after these changes: 34 tests passed; compileall and `git diff --check` passed. Full grouped regression and live current-news smoke are in progress; do not mark end-to-end acceptance passed until both results are recorded.


## Task 25 — Intent-to-research-and-answer routing — 2026-10-16
- Audited `MasterBrain.process()` from intent classification through authorization, verification, internal Brain dispatch, research/learning result acceptance, and final `BrainResult` construction.
- Critical trust-boundary bug: the Main Brain extracted the nested research/learning result and checked only its inner `success` flag. It ignored the Research/Learning Brain wrapper's `verified` and `persisted` flags and did not require `verification_status == "VERIFIED"` at the final routing boundary. An inconsistent inner result could therefore be surfaced as successful despite failed verification; the failure path also preferred the inner answer text, potentially exposing an unverified claim.
- Fix: research dispatch now requires wrapper `success`, `verified`, and `persisted`, plus inner result success and `VERIFIED` status. Learning applies the same checks and additionally requires at least one verified knowledge item. Failed trust checks return a controlled evidence-insufficiency message instead of the unverified answer. Integration metadata now reports success only when those same acceptance conditions hold. Final `BrainResult.verification_status` now carries the actual research/learning status instead of the unrelated preflight safety-verification status.
- Added regression tests for both accepted verified routes and the malicious/inconsistent case where an inner result says success but the wrapper/verification gate rejects it. The tests assert that the unverified answer text never reaches the user-facing message.
- Focused routing regression: **34 passed, 0 failed**. Full suite: **1822 passed, 0 failed** in 130.59 seconds. Python compilation and `git diff --check` passed. This completes Task 25 code-level routing acceptance; Task 36 real-source live research acceptance remains a separate blocker.


## Task 26 — Memory and Knowledge Integration — 2026-10-16
- Traced the Main Brain's persistent-context flow: `MasterBrain` constructs `MemoryBrain` and `KnowledgeBrain` against the selected operational storage; `MotherDecisionContext` is populated through `OperationalMemoryKnowledgeIntegration`; the same retrieval is used by operational answer generation.
- Found a trust-boundary bypass in `OperationalMemoryKnowledgeIntegration`: knowledge retrieval already passed through `KnowledgeBrain`, but memory retrieval queried `ResearchStorage.retrieve_memories()` directly. This meant a factual memory with forged `verified=True` / `verification_status="VERIFIED"` metadata and nonexistent evidence/source IDs could enter Main Brain decision context without the `MemoryBrain` provenance/lifecycle gate.
- Fix: operational retrieval now uses `MemoryBrain.retrieve()` with the same filters and limit, so factual-memory provenance checks apply before memory enters decision context/model prompt. Knowledge retrieval continues to use `KnowledgeBrain`, including persisted lifecycle and unresolved-conflict checks. Both specialists share the exact same `ResearchStorage` instance.
- Added a regression in `tests/unit/test_operational_memory_knowledge.py` proving a forged factual memory with missing evidence/source records is excluded from operational context. Focused memory/knowledge/Main Brain integration suite: **50 passed, 0 failed**. Full suite: **1823 passed, 0 failed** in 130.35 seconds. Python compilation and `git diff --check` passed. Task 26 code-level integration acceptance is complete; Task 36 live-source acceptance remains separate and blocked.


## Task 27 — Verification and Conflict-Resolution Integration — 2026-10-16
- Traced conflict detection/resolution from `ResearchResultAggregator` through `ResearchAnswerPipeline`, durable `KnowledgeConflictRecord` storage, `ResearchQueryEngine`, `KnowledgeBrain`, and operational-context retrieval.
- Found two connected trust-boundary gaps: the answer pipeline computed conflict-intelligence assessments but did not persist them for later Main Brain turns; and knowledge retrieval checked only whether a conflict remained unresolved, not whether the current candidate was the selected winner after a resolved conflict. In addition, `KnowledgeBrain` used the lower-level conflict summary, which does not expose the selected knowledge ID.
- Fixes: answer pipeline now persists each conflict assessment through the same `ResearchStorage` used by retrieval. If persistence fails, the answer is marked unverified with `CONFLICT_PERSISTENCE_FAILED` and arbitration is rerun. `KnowledgeBrain` now uses the verification-aware conflict context and only accepts the selected candidate; ambiguous/missing selections fail closed. `ResearchQueryEngine` and the pre-aggregation answer candidate filter apply the same winner-only rule, while unresolved conflicts continue to block both candidates.
- Added regression coverage proving (a) a resolved conflict's selected claim remains retrievable while the losing claim is excluded, (b) query retrieval applies the same gate, and (c) answer pipeline persists newly detected conflicts for future retrieval.
- Focused conflict/memory/answer regression: **75 passed, 0 failed**. Additional direct regressions: **2 passed**. Full repository suite: **1825 passed, 0 failed** in 130.65 seconds. Targeted `py_compile` and `git diff --check` passed.
- Task 27 code-level integration acceptance is complete. This does not close Task 36: real-source live research acceptance remains a separate blocker and must not be inferred from unit tests.


## Task 28 — Worker / Department Coordination Audit — 2026-10-16
- Audited `BackgroundWorkerManager`, `InterModuleBus`, `ResearchLearningCommander`, the Research/Learning facade, and Main Brain internal-role dispatch.
- Found a worker lifecycle race: `BackgroundWorkerManager.run()` did not reject an already-`RUNNING` worker, allowing duplicate concurrent execution and racing run/history sequence values. Fixed with an `RLock`, atomic RUNNING reservation, duplicate-run rejection, protected lifecycle/history/checkpoint reads and writes, and worker invocation outside the manager lock so independent workers are not serialized. Successful completion preserves an explicit concurrent PAUSED/STOPPED state rather than accidentally resetting it to READY.
- Found an inter-module bus race: concurrent `send()` calls could increment sequence and append history without synchronization; subscription and history snapshots were also unprotected. Added locking around sequence/history updates, subscriptions, dispatch handler snapshots, and history reads.
- Found a department trust/trace issue: `ResearchLearningCommander` could mark an inconsistent result complete if its status string said VERIFIED despite an explicit `verified=False`, and concurrent dispatches returned shared `_last_trace` rather than their own local trace. It now respects explicit false verification/persistence flags, requires a positive verified-knowledge count when that field exists for learning, stores and returns a task-local immutable trace, and synchronizes the shared last-trace property.
- Added `tests/unit/test_worker_coordination_races.py` covering duplicate concurrent worker run rejection, unique run/history sequences, 100 concurrent bus sends with unique ordered IDs, inconsistent verification/persistence flags, and zero-knowledge learning rejection.
- Focused coordination suite: **22 passed, 0 failed**. Full repository suite: **1830 passed, 0 failed** in 132.16 seconds. Final `py_compile` and `git diff --check` verified separately.
- Task 28 code-level acceptance is complete. The internal role registry remains in-process and its advisory roles are not separate independent model instances; this audit does not claim distributed worker execution or live-source acceptance. Task 36 remains blocked pending real-source live research acceptance.


## Task 29 — Permission and Security Boundaries — 2026-10-16
- Audited `PermissionEngine`, `ToolPermissionGateway`, `SafeToolExecutor`, `ToolInvoker`, registry metadata, Mother Sandbox pre-execution validation, and protected tool registration/invocation contracts.
- Found a confirmation type-confusion bug: Python truthy values such as the string `"false"` or integer `1` could be treated as user confirmation by the central `PermissionEngine` and tool gateway. Both now require actual booleans and reject invalid types before making a permission decision.
- Found a direct-executor authorization bypass: `SafeToolExecutor.execute()` trusted caller-supplied `_permission_granted=True` for protected tools instead of independently consulting the canonical permission gateway. The executor now strips caller-supplied grant flags, fails closed when a protected tool has no bound gateway, rechecks permission itself, and injects the handler grant flag only after an allowed decision. `ToolInvoker` binds its canonical gateway to the executor; a conflicting gateway binding is rejected.
- Found a metadata downgrade risk: a tool marked both `read_only=True` and assigned a protected action could be classified as a low-risk read. The gateway and executor now reject this inconsistent metadata instead of silently downgrading the action.
- Added `tests/unit/test_permission_security_boundaries_task29.py` for malformed confirmation values, forged permission flags, independent executor permission rechecks, and read-only/protected-action metadata conflicts.
- Focused regression: **19 passed, 0 failed**. Full repository suite (`PYTHONPATH=. pytest -q`): **1835 passed, 0 failed** in 129.75 seconds. Final targeted `py_compile` and `git diff --check` both passed after the report update.
- Task 29 acceptance covers code-level permission routing and regression behavior only. It does not claim a formal security certification, OS-level sandbox isolation, or real external-action acceptance. Task 36 remains blocked pending real-source live research acceptance.


## Task 30 — Missing Connections and Integration Bugs — 2026-10-16
- Audited the Main Brain's internal-role dispatch, Research/Learning handlers, Tool Brain composition, shared emergency-stop path, and adjacent regression tests.
- Found a safety-control integration gap: `MasterBrain` created its canonical `EmergencyStop`, but `ToolBrain` was initialized without it and created a separate stop latch. Engaging the Main Brain stop therefore did not necessarily block direct Tool Brain execution. Fixed the composition root to inject the exact same `self.emergency_stop` into `ToolBrain`; regression confirms object identity and that a Main Brain stop blocks Tool Brain execution.
- Found authorization-gate type confusion at the internal department boundary: `InternalBrainTeam.dispatch()` relied on truthiness, so non-boolean values such as `"false"` or `1` could satisfy authorization/verification checks. It now requires actual Boolean gate results and rejects malformed context instead of coercing it into a dictionary.
- Found a related Research/Learning bridge bug: Main Brain handlers converted `context['confirmation']` with `bool(...)`, allowing strings/integers to become explicit confirmation. Both handlers now reject non-boolean confirmation and return unverified/non-persisted failure without calling their underlying research or learning pipeline.
- Added `tests/unit/test_task30_integration_boundaries.py` covering malformed authorization/verification flags, invalid context, research/learning confirmation coercion, and shared emergency-stop propagation.
- Focused integration/security regression: **50 passed, 0 failed**. Full repository suite (`PYTHONPATH=. pytest -q`): **1840 passed, 0 failed** in 133.90 seconds. Final targeted `py_compile` and `git diff --check` passed after the report update.
- Task 30 code-level integration acceptance is complete. This does not claim that every architecture module is a separate live model, nor does it close real-source live research acceptance (Task 36 remains blocked).


## Task 31 — Main Brain Architecture Integration Acceptance — 2026-10-16
- Acceptance audit traced the `MasterBrain` composition root across Research/Learning, operational retrieval, nested Memory/Knowledge specialists, internal role handlers, advisory cognitive/council review, context recording, Tool Brain, and the shared emergency-stop latch.
- Regression-first reproduction found a real storage wiring defect: when a caller injected `mother_research` but left `mother_operational` at its default, the constructor synchronized `MotherOperationalIntegration.storage` and its `memory_knowledge.storage` facade only. The nested `memory_knowledge.memory_brain` and `memory_knowledge.knowledge_brain` still held the previous storage object, so operational retrieval could read from a different store than research/learning writes.
- Fix: the default-operational wiring path now synchronizes the nested MemoryBrain and KnowledgeBrain storage references along with the integration facade. Added `tests/unit/test_task31_main_brain_architecture_acceptance.py` to assert object-identity consistency across all storage consumers and Research/Learning integration references, all declared internal roles being registered, and safe fast-path cognitive/context instrumentation.
- Initial reproduction was red on the nested storage identity assertion; after the fix the focused regression suite passed: **24 passed, 0 failed** in 6.47 seconds. Full repository suite (`PYTHONPATH=. pytest -q`) passed: **1843 passed, 0 failed** in 127.39 seconds.
- Targeted `py_compile` for `core/brain/master_brain.py` and the new acceptance test passed; `git diff --check` passed. Logs: `logs/task31_focused_verification.log` and `logs/task31_full_pytest.log`.
- Task 31 code-level architecture integration acceptance is PASS. Architecture limitation remains explicit: the three-brain council is heuristic/advisory, and internal roles are in-process handlers rather than independent live model instances. This does not close Task 36 real-source live research acceptance.


## Task 32–33 Re-verification — 2026-10-16
- Task 32 targeted regression re-run covered Task 29 permission boundaries, Task 30 integration boundaries, Task 31 Main Brain architecture acceptance, worker coordination races, Main Brain decision/research flow, operational memory/knowledge, verified-only retrieval, and learning history persistence: **43 passed, 0 failed** (`logs/task32_targeted_regression_verification.log`).
- Task 33 research integration re-run covered the research pipeline integration, full research intelligence integration, end-to-end research, Mother Research answer integrity, final answer traceability gate, multi-source verification/acquisition/agreement, research-to-knowledge linking, and knowledge conflict integration/lifecycle/persistence: **73 passed, 0 failed** (`logs/task33_research_integration_verification.log`).
- Full repository pytest re-run completed: **1843 passed, 0 failed** in 131.71 seconds (`logs/task32_33_full_pytest.log`). Final `py_compile` and `git diff --check` passed after the verification report updates.
- No code defect was exposed by this re-verification cycle; Tasks 32 and 33 remain PASS. These tests exercise deterministic and mocked/fixture paths; they do not establish current live-source research acceptance. Task 36 remains blocked pending separate live evidence.


## Task 34 — Persistence and Restart Recovery Acceptance — 2026-10-16

- Reproduced a restart-recovery defect: FTS5 memory/knowledge search indexes were rebuilt only when row counts differed. A canonical record could change while the FTS companion retained stale text at the same row count, so restart did not repair retrieval.
- Fixed core/research/storage.py: canonical memory/knowledge changes invalidate a persistent FTS dirty marker; startup rebuilds the indexes from canonical records when the marker is dirty or missing. This avoids scanning/rebuilding all records on every clean startup.
- Fixed save_memory and save_knowledge so canonical record writes, FTS companion updates, and clearing the dirty marker commit together. This removes the previous split-commit window.
- Added tests/unit/test_task34_persistence_restart_recovery.py with same-row-count stale-index recovery tests for knowledge and memory.
- Persistence/restart focused suite: **26 passed, 0 failed** (logs/task34_persistence_focused.log), including research storage, learning history/order, source rehydration, conflict persistence/lifecycle, memory storage, and knowledge verification lifecycle.
- Full repository suite: **1845 passed, 0 failed** in 139.56 seconds (logs/task34_full_pytest.log).
- python -m py_compile core/research/storage.py tests/unit/test_task34_persistence_restart_recovery.py: PASS. git diff --check: PASS.
- Scope limitation: this is automated SQLite/process-reopen coverage using isolated test databases, not a physical Android force-kill/power-loss or production-database restore drill. Task 35 failure/recovery acceptance remains separate.


## Task 35 — Failure and Recovery Acceptance — 2026-10-16

- Added deterministic failure-injection tests for Knowledge and Memory persistence: the derived FTS table is deliberately unavailable after a canonical update begins, then restored; a later unrelated successful write must not accidentally commit the failed update.
- Reproduced a real bug before fixing: a SQL error during the FTS part of save_knowledge/save_memory left the canonical row's transaction pending. A later commit could persist the replacement record even though the indexed save had reported failure.
- Fixed core/research/storage.py with a shared _save_search_indexed_record transaction boundary using the SQLite connection context manager. Canonical row, derived index row and dirty-marker update now commit together; SQL errors roll back the transaction.
- New Task 35 failure-injection tests plus Task 34 restart recovery and existing tool/storage failure tests: focused verification log logs/task35_failure_recovery_focused.log.
- Full repository suite: **1847 passed, 0 failed** in 136.96 seconds (logs/task35_full_pytest.log).
- python -m py_compile core/research/storage.py tests/unit/test_task35_failure_recovery.py: PASS. git diff --check: PASS.
- Scope limitation: injected SQLite storage failures and automated recovery were tested. Physical Android process-kill/power-loss drills, actual disk-full conditions and production DB restore remain outside this acceptance run.


## Task 36 — Real-source live research acceptance — 2026-10-17

- Executed `scripts/task36_live_research_acceptance.py` on the actual Termux working copy with real network requests and an explicit per-run `NETWORK_ACCESS` confirmation. The script scopes the free Google News RSS discovery backend to its own process and uses a temporary SQLite database; it does not change the user's persistent shell configuration or production research database.
- First live end-to-end run completed all five steps but exposed two concrete defects: (1) a publisher page with only 41 visible characters was accepted as source content and counted toward publisher diversity; (2) `ResearchAnswerPipeline` called `ResearchResultAggregator.aggregate()` without the linked `ResearchFinding` objects, so the final knowledge → finding → evidence → source trace gate rejected a claim even though its two-source evidence chain existed.
- Fixes: time-sensitive direct-web acquisition now rejects publisher responses with fewer than 160 visible article characters after checking listing-page and publication-date rules. The answer pipeline now resolves finding objects by canonical IDs from the live ResearchEngine, falls back to `ResearchStorage.get_finding()` when available, and passes those findings into the aggregator's answer-traceability engine. Optional storage adapters without `get_finding()` remain supported.
- Added regressions: `tests/unit/test_direct_web_publication_date.py` verifies near-empty publisher pages are rejected without overriding stale/listing/date errors; `tests/unit/test_research_answer_pipeline.py` verifies linked findings reach the final traceability gate.
- Focused suite after fixes: **78 passed, 0 failed** across direct-web publication dates, answer pipeline, final answer gate, answer traceability, and research integration tests. `py_compile` and `git diff --check` passed.
- Second actual live end-to-end acceptance: **PASS** in 31.75 seconds. Search backends returned 27 timestamped discovery leads; the pipeline safely resolved/selects 3 diverse candidate URLs, fetched 2 usable direct publisher pages from `lokmattimes.com` and `firstpost.com`, rejected the 41-character `konsulteer.com` page, extracted 73 findings/evidence records, linked the final claim to 2 distinct source IDs, produced `TRACEABLE` source traceability with complete knowledge/finding/evidence/source links, passed final answer verification (`VERIFIED`), and passed answer arbitration (`ACCEPTED`). No discovery snippet was accepted as publisher evidence.
- The live test's final report is retained at `logs/task36_live_acceptance_rerun.log` if present; the successful direct process output recorded `status: PASS`, `failed_checks: []`. Run again with `PYTHONPATH=. python -u scripts/task36_live_research_acceptance.py` to recheck live publisher availability.
- Acceptance scope: this demonstrates one real query through the actual acquisition, publisher fetch, extraction, evidence verification, answer synthesis, and traceability pipeline. It is not a guarantee that every query or publisher will pass; if independent evidence is insufficient, SAHIBEX must continue to fail closed. Full regression and final diff checks are required after these changes.


### Task 36 final regression confirmation — 2026-10-17
- Full repository regression after the Task 36 fixes: **1849 passed, 0 failed** in 196.42 seconds (`logs/task36_full_pytest.log`).
- `python -m compileall -q core tests scripts`: PASS. `git diff --check`: PASS.
- Captured live acceptance summary: `logs/task36_live_acceptance_report.json`.
- Task 36 is now **PASS** for the executed live query. Task 37 (full Main Brain end-to-end acceptance) and Task 38 (final overall report) remain pending.


## Task 37 — Full end-to-end Main Brain acceptance — 2026-10-17

- Exercised the actual `MasterBrain.process()` entry point on the Termux working copy with an isolated temporary SQLite database. The production knowledge DB and shell profile were not used or changed.
- Deterministic path: `What is 2 + 2?` → `उत्तर: 4`; runtime completed. Acceptance checker corrected to recognize the already-supported Hindi answer format rather than falsely failing the test.
- Protected-action path: `Delete the project files.` → blocked before plan creation; permission denied, explicit confirmation required, constitution override/mutation denied.
- Live research path: `Search the internet for latest AI safety security news today.` routed through reasoning → orchestration → Research/Learning department → live multi-source acquisition → direct publisher fetch → extraction/evidence verification → final answer verification and arbitration. Run completed in 34.3s; answer `VERIFIED`, answer arbitration `ACCEPTED`, traceability `TRACEABLE`, one claim backed by two distinct source identities. A 41-character publisher stub was rejected; two usable publisher pages contributed 73 findings/evidence records.
- The first E2E run exposed a query-normalization defect: the full command phrase was sent as the search topic. `ResearchLearningBrain.normalize_research_query()` now strips recognized English/Hindi command framing without inventing a topic; added parametrized and delegation regression tests. Focused suite: **34 passed**.
- Storage-wiring acceptance confirmed the same isolated `ResearchStorage` instance is shared by Mother Research, Mother Operational, nested Memory/Knowledge retrieval, Memory Brain, Knowledge Brain, and the Learning/Research bridge. The isolated run persisted 73 knowledge candidates and 3 memory records. Zero candidates were marked verified in this research-only request; this is intentional fail-closed behavior, not a failed test—research answers are verified for the current response, while unverified candidates are not automatically promoted into long-term verified knowledge by the research path.
- Acceptance script: `scripts/task37_main_brain_e2e_acceptance.py`; JSON report: `logs/task37_main_brain_e2e_acceptance_report.json`; captured run log: `logs/task37_main_brain_e2e_acceptance_final.log`.
- End-to-end checks: **10/10 PASS** (`failed_checks: []`). Protected actions remain blocked; live research may either return a fully verified, traceable answer or fail closed without surfacing unsupported claims.
- Final full repository regression after the Task 37 code/test changes: **1869 passed, 0 failed** in 135.40 seconds (`logs/task37_full_pytest_final.log`). `python -m compileall -q core tests scripts`: PASS; `git diff --check`: PASS.
- Scope boundary: one live research query plus deterministic/protected-action paths were exercised end-to-end. This does not guarantee every live query will return a verified answer; insufficient evidence must still fail closed.


### Task 37 latest final verification — 2026-10-17
- Re-ran the actual Termux MainBrain acceptance after the final integration changes: **PASS, 10/10 checks**, 34.64 seconds; `failed_checks: []`. Latest evidence: `logs/task37_main_brain_e2e_report.json` and `logs/task37_main_brain_e2e_acceptance.log`.
- Live request was routed as `intent=search`, `action=research`; reasoning, orchestration and research department all reported `DISPATCHED`. The answer was `VERIFIED`, arbitration `ACCEPTED`, traceability `TRACEABLE`, with one claim supported by two distinct source identities. The 41-character publisher stub was rejected. Isolated DB contained 73 knowledge candidates and 3 memory records; research-only candidates remain unpromoted to verified long-term knowledge by design.
- Fixed explicit-search intent precedence so `Search for an overview of the Python language` does not route to the coding department just because `Python`/`programming` appears in the topic. Added regression coverage for search-vs-code classification. MainBrain now exposes research diagnostics and prompt-injection status in its successful result metadata.
- Focused integration suite: **43 passed, 0 failed**. `python -m compileall -q core tests scripts`: PASS; `git diff --check`: PASS.
- Latest full repository regression: **1869 passed, 0 failed** in **133.83 seconds** (`logs/task37_full_pytest.log`). Task 37 is PASS. Task 38 (final overall PASS/FAIL report and remaining blockers) is the only remaining item in the 38-task list.

## 2026-10-25 follow-up — bilingual executive routing
The cognitive neural architecture's advisory routing now detects multi-step English, Romanized Hindi/Hinglish, and Devanagari requests, preserving Devanagari combining marks during normalization. Regression: 31 focused tests passed; compileall and `git diff --check` passed. Evidence: `logs/cognitive_neural_bilingual_routing_20261025.md`. This is a routing enhancement only; it does not grant authority or prove general intelligence.

## 2026-10-25 follow-up — OCR evidence boundary
P7 OCR-to-reasoning observation now bounds text at 16k characters, adds a truncation marker, sanitizes control characters in embedded filename/engine metadata, requires a valid SHA-256, and uses explicit untrusted-text/provenance boundaries. Evidence: `logs/p7_ocr_evidence_boundary_hardening_20261025.md`; 17 focused tests PASS. Actual vision-model reasoning remains outside this contract and P7 remains PARTIAL.
