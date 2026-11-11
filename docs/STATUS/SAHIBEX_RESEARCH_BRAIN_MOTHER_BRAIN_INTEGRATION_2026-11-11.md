# SAHIBEX Research Brain ↔ Mother Brain Integration Audit — 2026-11-11

## Disposition
**ALREADY IMPLEMENTED; RE-VERIFIED PASS for the bounded software integration scope.** This task did not require a duplicate research engine or speculative code changes. The existing integration was traced end-to-end and its relevant tests were rerun.

## Verified integration path
1. `MasterBrain` owns the `MotherResearchIntegration` instance and constructs `ResearchLearningBrain` as the bounded research/learning facade.
2. Research storage is wired to the same storage object/database used by operational retrieval, Memory Brain and Knowledge Brain. Split persistent stores are rejected when explicitly injected; the learning integration must use the same Mother Research instance.
3. MainBrain's `search` intent enters the research branch and dispatches the registered `research` internal role through `InternalBrainTeam`.
4. Dispatch requires explicit upstream authorization and request-verification booleans. The internal role does not grant permission or authority.
5. `_internal_research_handler` validates that confirmation is a boolean and delegates to `ResearchLearningBrain.research_topic()`.
6. The facade normalizes only recognized leading search-command framing, delegates to the existing Mother Research pipeline, and marks the result successful/persisted only when the underlying result is successful and `verification_status == VERIFIED`.
7. MainBrain independently checks handler success, verified and persisted flags, underlying research success and `VERIFIED` status before surfacing the answer. Failed verification produces an evidence-insufficiency response rather than leaking an unverified inner answer.
8. Existing acquisition/network permission, evidence extraction, conflict resolution, prompt-injection guard, provenance and knowledge lifecycle filters remain the authoritative lower-level controls.

## Validation on 2026-11-11
- Focused integration/security regression: **62 passed in 11.59s**, exit 0. Command used `.venv/bin/python -m pytest -q` with:
  - `tests/unit/test_master_brain_research_flow.py`
  - `tests/unit/test_research_learning_brain.py`
  - `tests/unit/test_research_learning_brain_query_normalization.py`
  - `tests/unit/test_task30_integration_boundaries.py`
  - `tests/unit/test_mother_research_prompt_injection.py`
  - `tests/unit/test_mother_research_answer_integrity.py`
  - `tests/unit/test_research_findings_to_knowledge_linking.py`
  - `tests/unit/test_research_persistent_source_rehydration.py`
- Full repository regression: **2,365 passed in 167.85s**, exit 0.
- An initial invocation using the `pytest` console script failed collection because `core` was not on that entry-point's import path; rerunning with the repository interpreter as `.venv/bin/python -m pytest` resolved the invocation issue. No product-code defect was exposed by that collection error.

## Explicit limits — not promoted by this task
- This verifies the existing software integration, not live web-provider availability, external source quality on every query, or real-time network operation on the phone.
- It does not prove independent corroboration for the legacy 83,908-candidate knowledge corpus. No candidate was promoted, migrated or modified.
- It does not turn the research role into an independent child brain or grant it permission, file-write, execution or Constitution authority.
- Research answer verification remains bounded by the current evidence pipeline; `VERIFIED` does not certify every external publisher as authentic in all contexts.
- P6/P7/P8/P10/P11 and the knowledge trust-lifecycle blocker remain unchanged.

## Files
- Existing implementation reviewed: `core/brain/master_brain.py`, `core/brain/research_learning_brain.py`, `core/brain/mother_research_integration.py`, `core/brain/internal_brain_team.py`.
- Existing tests rerun: files listed above.
- This checkpoint changes documentation only; no implementation, production database, backup, credentials, device settings or user data were changed.
