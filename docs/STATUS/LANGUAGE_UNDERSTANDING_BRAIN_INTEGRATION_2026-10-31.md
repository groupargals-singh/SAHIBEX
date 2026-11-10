# SAHIBEX Language & Understanding Brain Integration — 2026-10-31

## Decision

**Scoped software integration: PASS.** The text and Companion voice request paths now use one Master Brain input-understanding pipeline. This checkpoint does not claim human-level or GPT-level general understanding, nor does it promote any P-series gate.

## Integrated pipeline

1. `InputNormalizationEngine` creates a bounded canonical text observation while retaining the original user request for the conversation/audit path.
2. `PerceptionLanguageBrain` applies only curated high-confidence spelling and project-name corrections. Uncertain single-edit dictionary matches remain suggestions; they are not silently applied.
3. `UniversalLanguageBrain` identifies language/script and mixed-language signals for the normalized request.
4. `ContextualInputUnderstandingBrain` is wired as a second-stage repair for ambiguous input (dictionary suggestions or multiple curated corrections). It is enabled by default for the local model provider, remains fail-closed on invalid/provider output, and uses numeric, negation and similarity guards. Remote model use still requires explicit opt-in.
5. Existing `IntentEngine` processes the normalized request. `SemanticIntentBrain` remains an optional model-backed fallback; it does not grant permissions or execute actions.
6. Existing `ContextManager` and `MemoryBrain` receive the original user text and result. The response metadata includes a bounded `input_understanding` trace with normalized text, language, corrections, unapplied suggestions and contextual-repair status.

## Voice integration

- Companion `/voice` now passes the untouched transcript to `MasterBrain.process()` rather than maintaining a second independent correction pipeline.
- `heard_text` remains the original transcript; `processed_text`, correction/suggestion lists, known terms and input language are read from the Master Brain trace.
- Voice input remains non-authorizing (`user_confirmation=False`).
- This validates software routing only; physical microphone → ASR → Main Brain → audible TTS round-trip is still pending.

## Safety invariants

- Raw and normalized text are both included in action classification so normalization cannot erase a protected-action signal from the original request.
- Number and explicit-negation changes are rejected; the original input is retained.
- No spelling suggestion or language assessment grants authority, permission, or action execution.
- Protected actions continue through the existing Constitution, PermissionGateway, approval and verification path.
- No knowledge records, credentials, model files, APKs, or user backups were deleted or bulk-modified for this integration.

## Verification evidence

- Focused language, perception, contextual repair, semantic intent and voice endpoint suite: **47 passed**.
- Full repository regression after the final text/voice integration and input-size fallback: **2,210 passed in 187.19s**, exit 0.
- `compileall` for changed Python modules/tests: PASS.
- `git diff --check`: PASS at the final code checkpoint.
- Live typed smoke: `sahibaks kya hai?` normalized to `SAHIBEX kya hai?` and returned the curated identity answer. `Pahle mujhe samjhao` safely corrected `Pahle` → `Pehle`.
- Uncertain `dictioary` remained unchanged and was surfaced as a suggestion.
- Protected-action regression confirmed that a contextual rewrite cannot remove the raw `delete` signal; action remained blocked and `NOT_EXECUTED`.

## Remaining limitations / gate disposition

- General semantic understanding still depends on model quality. `SemanticIntentBrain` remains opt-in pending a real local-model accuracy/latency evaluation; the deterministic intent engine is the fallback.
- Contextual repair only attempts a model call when lexical analysis finds ambiguity; it does not promise correction of every typo or every language.
- Real Android microphone/ASR transcript quality, user confirmation, TTS playback and full physical round-trip remain unverified.
- P6 remains PARTIAL; P7/P8/P10/P11 and P1–P12 statuses are unchanged. **No P-series gate is promoted by this software integration.**


## Live Companion text-route smoke — 2026-10-31
- Restarted the Media Bridge from the updated source with the project root on `PYTHONPATH`; `/health` returned success on loopback port 38742.
- Authenticated `/voice` request with raw text `sahibaks kya hai?` returned HTTP 200, `success=true`, `heard_text` preserved, `processed_text=SAHIBEX kya hai?`, `input_language=hi-Latn`, `answer_language=hi-Latn`, `CURATED_KNOWLEDGE`, and the expected three-point identity answer.
- This is a text-to-Master-Brain Companion route smoke, not a physical microphone/ASR or speaker playback test.


## Model/runtime limitation observed at final verification — 2026-10-31
- Local model endpoint `127.0.0.1:8080/health` returned connection-refused; available RAM snapshot was approximately 1.6 GiB. No model was started, downloaded, or force-loaded.
- Therefore deterministic normalization, curated spelling/name correction, language detection, raw-input preservation and permission-safe routing are live; model-backed contextual repair will fail closed/leave uncertain text unchanged while the local model is offline. General semantic-intent model accuracy remains unaccepted.
- This does not invalidate the software integration tests or authenticated Companion text-route smoke. It is a separate runtime/model-quality blocker. No P-series gate promoted.

## 2026-10-31 — ASR transcript alias correction and live bridge re-verification
- Added closed alias sahibaqs → SAHIBEX after the local Whisper synthetic Hindi loop produced “Sahibaqs”. Raw heard_text remains preserved; normalization is a curated project-name correction only, not a general fuzzy rewrite.
- Focused perception/language/media/voice regression: 43 passed.
- Repaired Media Bridge lifecycle scripts and restarted the verified project-.venv server. Authenticated English/Hindi synthesis and transcription returned HTTP 200; audio_retained=false; transcript confirmation remains required.
- Synthetic Hindi ASR still misrecognizes ordinary words (“Parikshar”); real human speech corpus and physical microphone/speaker acceptance remain pending. No P6 promotion.

## 2026-10-31 — Persistent context and contextual Hinglish intent follow-up
- Added deterministic code-intent patterns for explicit Hinglish bug-fix phrases, including "is bug ko fix karo" and "bug ko thik kro".
- Added context-aware refinement for "isko thik kro": recent software-bug context maps to code intent; without a usable referent the Confidence/Verification gate asks for clarification before planning.
- Added bounded newest-first persistent conversation retrieval to ResearchStorage/MemoryBrain and wired MasterBrain to reconstruct recent context after process restart. Up to five persisted conversation turns are considered; duplicate in-memory turns are removed; prior clarification questions are not treated as selected meanings; total context is bounded to 4,000 characters.
- Focused language/context/voice suite: 137 passed; persistent-context focused suite: 80 passed.
- Full repository regression after these changes: 2,262 passed in 174.89s, exit 0. Compileall and git diff --check PASS.
- This improves bounded context continuity; it does not prove complete lifetime memory recall or universal semantic understanding. No P-series gate promoted.
- Detailed evidence: docs/STATUS/UNDERSTANDING_INTELLIGENCE_ACCEPTANCE_2026-10-31.md.
