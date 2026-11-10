# SAHIBEX — Understanding Intelligence Acceptance Report
Date: 2026-10-31
Workspace: ~/SAHIBEX

## Executive decision

**The four Understanding Brains are NOT fully COMPLETE.** Their deterministic software foundations and safety integration are implemented and regression-tested. Persistent recent-context recovery and context-aware Hinglish bug-fix intent were improved in this checkpoint. General multilingual semantic quality and real phone voice acceptance remain blocked/partial.

No P-series gate is promoted by this report.

## 1. Intent Understanding Brain

**Disposition: PASS for the bounded deterministic routing scope; PARTIAL for general semantic intent.**

Implemented and checked:
- Explicit Hinglish bug-fix phrases such as "is bug ko fix karo" and "bug ko thik kro" map to the code intent.
- "isko thik kro" without a usable referent asks for clarification before planning.
- The same short request with recent software-bug context resolves to the code intent.
- Contextual intent refinement does not grant permission or execute code.
- Original user text remains preserved; protected-action signals are still classified from raw plus normalized text.

Focused tests cover the explicit phrase, missing-context clarification, and contextual resolution. The local model classifier did not return an accepted structured result in the live provider smoke.

## 2. Context and Memory Brain

**Disposition: PASS for bounded persistent recent-context recovery; PARTIAL for complete lifetime/project-context understanding.**

Implemented and checked:
- ResearchStorage.list_recent_memories() returns a bounded newest-first slice using the indexed memory type/source filters and stored creation timestamp.
- MemoryBrain.retrieve_recent_conversations() exposes only recent conversation records from the Master Brain source.
- A fresh Master Brain process can reconstruct a bounded context window from persistent conversation memory after restart.
- In-memory and persisted turns are deduplicated; prior assistant clarification questions are not treated as evidence that the user selected one of the offered meanings.
- The reconstructed context is bounded; it is not an unrestricted dump of the user's full history.

Focused tests include newest-first conversation retrieval and a two-instance/restart test where "isko thik kro" resolves to a code intent from the persisted prior software-bug context.

## 3. Voice Understanding Brain

**Disposition: PARTIAL.**

Readiness observed:
- Local whisper-cli executable exists and is executable.
- Local Whisper tiny Q5 model exists (32,152,673 bytes).
- Local Sherpa Supertonic-3 TTS backend and all required model files are present.
- Media Bridge /health returned HTTP 200.
- Android Companion captures mono 16 kHz PCM, sends it to the local ASR endpoint, shows the transcript for user review, and sends only the user-confirmed text to the Master Brain.
- The original heard transcript is retained in the request trace; voice input does not grant action confirmation.

Quality probe:
- Hindi local TTS synthesis succeeded (2.771 seconds; 44.1 kHz output).
- After resampling the generated test audio to the ASR-required 16 kHz mono PCM format, local Whisper returned "Namaste SAHIBEX, Main Brain," for the reference "नमस्ते, साहिबेक्स मेरी बात समझो।"; the transcript was incomplete.
- This is a synthetic TTS→ASR loopback only, not a human microphone test or speaker playback acceptance.
- ASR does not currently provide a calibrated confidence score to the Master Brain. The system does not invent one; transcript review and explicit user confirmation remain required.

Remaining: representative human Hindi/Hinglish/English speech corpus, measured word/character error rates, robust contextual repair, calibrated ASR confidence, and physical phone mic→ASR→transcript review→Master Brain→audible speaker E2E acceptance.

## 4. Confidence and Verification Brain

**Disposition: PASS for the deterministic safety/clarification boundary; PARTIAL for broad multilingual calibration.**

Implemented and checked:
- Common polysemy, unresolved demonstratives, unresolved action targets, and missing topic references can trigger clarification before planning/model/tool routing.
- Confidence and uncertainty are explicitly not factual truth scores.
- Generated or structurally valid output is not upgraded to fact without explicit upstream factual evidence.
- Protected actions remain under Constitution, PermissionGateway, user confirmation, verification, and audit.
- No ASR confidence is fabricated when the recognizer does not supply a calibrated score.

Remaining: broader Hindi/Hinglish/English ambiguity corpus, calibrated confidence thresholds, and adversarial/real-world accuracy evaluation beyond the bounded deterministic lexicon.

## Live model limitation

- Qwen3-1.7B is online on 127.0.0.1:8080 and reports text-only capabilities.
- A live SemanticIntentBrain → LocalLlamaProvider classification smoke returned no accepted structured result (None) after 24.73 seconds.
- Available RAM was approximately 1.5 GiB; the existing 3 GiB Qwen3-4B guard was not bypassed.
- Therefore model-backed general semantic understanding remains unaccepted. The deterministic fallback and fail-closed behavior remain authoritative.

## Verification

- Focused Understanding suite after the intent/context fixes: **137 passed in 19.29s**.
- Persistent-context focused suite: **80 passed in 16.37s**.
- Full repository regression after all code changes: **2,262 passed in 174.89s**, FULL_REGRESSION_EXIT=0.
- Python compileall: PASS.
- git diff --check: PASS.
- Logs:
  - logs/understanding_acceptance_after_fix_2026-10-31.log
  - logs/persistent_context_acceptance_2026-10-31.log
  - logs/full_regression_understanding_update_2026-10-31.log
  - logs/voice_loopback_hindi_2026-10-31.log
  - logs/semantic_provider_smoke_2026-10-31.log

## Remaining acceptance blockers

1. A quality-tested multilingual semantic model/runtime that fits the phone's available memory, with a representative accuracy/latency benchmark.
2. Human Hindi/Hinglish/English ASR evaluation and calibrated transcript confidence.
3. Physical Android microphone and audible speaker round-trip, including transcript review.
4. Broader context conflict/relevance tests and multi-turn project-instruction recall beyond the bounded recent window.

P6 remains PARTIAL for physical voice acceptance. Other P-series statuses are unchanged. No production database was bulk-modified, no model was downloaded or force-loaded, no RAM guard was bypassed, no destructive cleanup was performed, and no P-series gate was promoted.

## Final runtime snapshot after regression — 2026-10-31
- The Qwen3-1.7B server was online during the live semantic-provider smoke, but the final post-regression probe found port 8080 offline and no llama-server process. The reason for its exit was not established; I did not restart it.
- Media Bridge 38742 remained healthy (HTTP 200).
- Available RAM was approximately 2.3 GiB; the Qwen3-4B 3 GiB guard remains unmet. No guard was bypassed and no model was downloaded.
- Treat the semantic model as currently OFFLINE at the final snapshot. The earlier 24.73s None result remains evidence that it did not pass semantic acceptance while online.
