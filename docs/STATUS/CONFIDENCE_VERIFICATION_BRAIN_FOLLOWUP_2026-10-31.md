# Confidence & Verification Brain — Semantic Follow-up
Date: 2026-10-31

## Result

**Software integration and safety fallback: PASS.**
**End-to-end human-like multilingual semantic quality on the phone's available model: BLOCKED / PARTIAL.**
This does not promote any P-series gate and does not mark all of item #6 complete.

## Implemented

1. MasterBrain enables SemanticIntentBrain by default for the local model provider; an explicit `SAHIBEX_SEMANTIC_INTENT_ENABLED=0` still disables it. Mock remains excluded; remote inference remains separately opt-in.
2. Semantic fallback now runs for general requests and deterministic intent confidence below 0.72 (previously below 0.50), so medium-confidence Hinglish/English intents reach the semantic classifier.
3. Independent language-perception code is passed to the classifier and takes precedence over the model's unreliable language guess.
4. LocalLlamaProvider discovers the actual loaded llama.cpp model ID from `/v1/models` if no explicit ID is configured; the live launcher now supplies the full model path rather than a basename.
5. Local model health preflight prevents offline semantic classification and contextual typo repair from waiting for the long inference timeout. Both request paths have a 45-second ceiling.
6. Semantic clarification responses are rejected if they merely echo the request or are not recognizably interrogative.
7. Hinglish language markers were extended for `par`, `khojo`, `jankari`, `jaankari`, and common topic/research phrases.
8. ConfidenceVerificationBrain now catches unresolved “this/that topic” and Hinglish “is topic par / is par” references and asks for the missing subject before search/planning.

## Verification

- Focused regression: **86 passed**.
- Full repository regression: **2,251 passed in 201.40s**, exit 0.
- Changed Python modules/tests compileall: PASS.
- `bash -n scripts/start_sahibex_live.sh scripts/start_local_model.sh`: PASS.
- `git diff --check`: PASS.
- Live no-model MasterBrain smoke with local provider: `Is topic par latest jankari khojo` → language `hi-Latn`; `CLARIFICATION_REQUIRED`; answer “आप किस विषय पर जानकारी चाहते हैं?”; no permission, no plan.
- Offline local-provider smoke: semantic classification returned no result and contextual repair returned unchanged input in 0.0s; no model inference attempted.
- Guarded Qwen3-1.7B trial: started only via existing RAM guard (available RAM 2,323,076 kB; context 512). The model's outputs were inconsistent: one classification took 34.31s and returned invalid/empty schema; one live MasterBrain clarification contained an unrelated imperative (“Mujhe ye samjhao”) instead of a question. New validation rejects such output. The test model process was then stopped by verified PID/command line; port 8080 is offline and available RAM recovered to approximately 2.67 GiB.
- Qwen3-4B was not started because the 3 GiB guard was not met. No model was downloaded and no RAM guard was bypassed.

## Remaining blocker

The installed Qwen3-1.7B model is not reliable or fast enough to certify broad Hindi/Hinglish/English semantic understanding. A suitable, quality-tested multilingual model/runtime with adequate memory is still required. The deterministic ambiguity list is bounded and cannot cover every word, idiom, dialect, or conversational context. Physical phone microphone → ASR → transcript confidence → MasterBrain → audible TTS remains a separate acceptance gate.

## Safety

Semantic classification never grants permission. Constitution, PermissionGateway, user confirmation, verification, and audit remain authoritative. Invalid/offline model output falls back conservatively; it is never promoted to fact or action authority. No database records, credentials, protected files, or user data were modified by the model trial.

## 2026-10-31 — Latest live model and voice-quality recheck
- Qwen3-1.7B is currently online and text-only. A live SemanticIntentBrain → LocalLlamaProvider classification attempt returned no accepted structured result after 24.73s; model-backed broad semantic quality remains unaccepted. Available RAM was about 1.5 GiB; Qwen3-4B guard was not bypassed.
- Local Whisper CLI and tiny Q5 model are present; local Sherpa Supertonic-3 TTS and all configured model files are present. Hindi TTS generated a 2.771s sample. After conversion to the ASR-required 16 kHz mono PCM format, Whisper produced an incomplete transcript ("Namaste SAHIBEX, Main Brain,") for the full Hindi reference sentence.
- This synthetic loopback is not a human microphone/speaker test. Android still requires the user to review and confirm the transcript before sending it to Main Brain.
- No calibrated ASR confidence score is available; the system does not invent one. Confidence/uncertainty remain separate from factual truth and permission.
- Latest full repository regression: 2,262 passed in 174.89s, exit 0. No P-series gate promoted.
- Detailed evidence: docs/STATUS/UNDERSTANDING_INTELLIGENCE_ACCEPTANCE_2026-10-31.md.

## Final runtime snapshot after regression — 2026-10-31
- The Qwen3-1.7B server was online during the live semantic-provider smoke, but the final post-regression probe found port 8080 offline and no llama-server process. The reason for its exit was not established; I did not restart it.
- Media Bridge 38742 remained healthy (HTTP 200).
- Available RAM was approximately 2.3 GiB; the Qwen3-4B 3 GiB guard remains unmet. No guard was bypassed and no model was downloaded.
- Treat the semantic model as currently OFFLINE at the final snapshot. The earlier 24.73s None result remains evidence that it did not pass semantic acceptance while online.
