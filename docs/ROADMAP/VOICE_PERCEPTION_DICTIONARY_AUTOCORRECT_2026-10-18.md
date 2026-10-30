# SAHIBEX Voice Perception, Word Knowledge and Auto-correction

Date: 2026-10-18

## Implemented in this pass

- Added `core/brain/perception_language_brain.py`.
- Preserves the raw transcript and produces a separately normalized transcript.
- Applies only curated high-confidence spelling fixes and known SAHIBEX name aliases.
- Leaves uncertain spelling untouched and reports dictionary-based suggestions separately.
- Identifies basic language/script clues and known vocabulary.
- Provides a bounded word-profile helper with script, letter units and optional meaning.
- Persists only explicitly remembered vocabulary in `data/knowledge/voice_word_library.json`; it never evaluates stored content.
- Integrated the perception layer before `MasterBrain.process` in the Android media bridge.
- The bridge response includes raw/processed text, corrections, suggestions, known terms, input language and answer language.
- Android speech recognition now receives biasing vocabulary for SAHIBEX and common Hindi/Hinglish terms.
- Expanded the closed, explicit SAHIBEX name-alias dictionary for common English/Devanagari ASR variants (including “sahibeks”, “sahibax”, “sahib e x”, “साहिब एक्स” and Brain variants); unrelated words are not fuzzy-rewritten.
- Added regression cases for name variants and a non-name guard.
- Added `ContextualInputUnderstandingBrain`: when the lexical layer finds uncertain typo candidates, it can ask SAHIBEX's configured non-mock model to repair the text in context. The model never answers or executes the utterance.
- Contextual repair fails closed on provider/schema errors, low confidence, numeric mismatch, explicit negation mismatch, or low text similarity; original transcript remains available.
- Added targeted corrections for common Romanized Hindi/Hinglish typos such as `galt`, `samjh`, `jese`, `pahle`, and `kro`.
- The Android bridge returns bounded contextual-repair status and summary alongside raw and processed transcript.
- Android TTS considers both Devanagari script and the detected answer language when choosing Hindi vs English.

## Safety rules

- The original transcript remains available for traceability.
- Only explicit curated corrections are auto-applied.
- Fuzzy dictionary candidates are suggestions, not automatic replacements.
- Numbers, negation and unknown words are not rewritten by a generic fuzzy matcher.
- Voice input never grants confirmation or permission for protected actions.
- The word library is bounded and stores plain text only; corrupted library data is ignored rather than blocking input.

## Verification

- Targeted Python syntax compilation: PASS.
- Latest targeted voice/perception/contextual-repair/bridge/language tests: 36 passed in 2.25s; targeted compileall and git diff --check: PASS.
- Full Python suite: running at time of this note; final result must be recorded after process completion.
- Android Java source compilation: PASS using the installed Android 35 `android.jar` and `javac` (exit code 0).
- Android APK build: BLOCKED. The system Gradle 9.8.1 is incompatible with Android Gradle Plugin 8.13.0; retrying with cached Gradle 8.13 passed Gradle configuration and Java compilation but failed at Android resource linking because the SDK AAPT2 Linux binary cannot execute correctly in this Termux runtime. No APK was rebuilt or claimed to be verified.
- Physical microphone-to-Main-Brain-to-speaker test: PENDING because no Android device was attached through ADB in this session.

## Important remaining work

1. The app still relies on the Android-installed speech recognition service. Vocabulary biasing helps only when that service supports it; it does not install an independent SAHIBEX ASR model.
2. Add a selectable/automatic mixed-language recognition path and test real Hindi, Romanized Hindi, Hinglish, names, numbers and negation on the actual phone.
3. Contextual repair is currently wired into the Android media bridge; connect the same verified perception/interpretation path to other Main Brain text entry points without double-correction or losing raw input provenance.
4. Test correction feedback, persistent user vocabulary, restart recovery and concurrent access.
5. Rebuild the APK with a compatible Gradle version, install it, and complete a real microphone → transcript → corrected transcript → Main Brain → TTS acceptance test.
6. Evaluate actual configured local-model repairs against a bilingual typo benchmark; unit fixtures prove the guards and integration path, not that the current model reliably corrects arbitrary user speech.

## Status

This is a partial, test-backed improvement—not a declaration that SAHIBEX now hears or understands at ChatGPT level. Final PASS requires real-device voice acceptance and verified Main Brain interpretation, not just unit tests.


## 2026-10-25 update — local speech-to-text replaces Android recognition intent

- Android Companion captures PCM audio directly with `AudioRecord`; it no longer calls `RecognizerIntent` / Android `SpeechRecognizer` for transcription.
- The authenticated loopback media bridge exposes `/transcribe`, which accepts bounded WAV audio, invokes SAHIBEX's local `whisper.cpp` runtime, and deletes temporary audio after processing. No cloud or Android-recognizer fallback is used.
- The result appears in an editable review dialog; Main Brain processing happens only after explicit user confirmation. A bounded initial prompt includes common SAHIBEX/Hindi/Hinglish vocabulary; offline model inference never calls a network recognizer.
- Model and native CLI are installed outside the repository. Setup: `scripts/setup_offline_asr.sh`. Runtime path and hashes are recorded in `logs/p6_offline_asr_implementation_20261025.md`.
- Dictionary expansion adds high-confidence curated corrections and a wider Hindi/Hinglish/voice vocabulary. Ambiguous spellings stay suggestions, not silent replacements.
- Software tests and APK build pass, and one English speech fixture was transcribed by the actual local engine. Hindi/Hinglish physical microphone acceptance remains pending. This update does not close P6.

## 2026-10-25 update — Neural TTS integration slice
- Added a local Piper adapter and authenticated `/synthesize` WAV endpoint; Android Companion now prefers local neural WAV playback and visibly labels compatibility fallback.
- Focused tests: 18 passed; Python compile and diff checks passed; APK build and v2 signature verification passed.
- **Still pending:** Piper executable + Hindi/English voice model installation/configuration, real WAV generation on device, physical audio playback/listening acceptance, and user-approved custom voice sample. Do not mark P6 complete yet. See `logs/p6_neural_tts_integration_20261025.md`.

## 2026-10-25 — local neural TTS runtime integration
- Added Sherpa-ONNX Supertonic-3 multilingual backend for Hindi/English, installed Android ARM64/Python 3.14 runtime and model outside the repository, and wired the authenticated `/synthesize` bridge to the backend.
- Direct synthesis and live authenticated bridge both returned valid WAVs for Hindi and English; live latency was about 4.8–4.9 seconds for the short acceptance prompts. Focused voice suite: 28 passed; APK rebuilt and v2 signature verified.
- Model terms are OpenRAIL-M (sample code MIT); licensing review is required before redistribution/commercial deployment.
- Physical Android speaker playback and full microphone-to-audible-response acceptance remain pending. See `logs/p6_sherpa_supertonic_runtime_20261025.md`.
- Follow-up hardening: resident Supertonic engine cache, serialized bounded admission to avoid parallel inference memory spikes, explicit busy response (HTTP 429), and additional fail-closed tests. Latest focused voice suite: 31 passed. Live bridge recheck returned valid Hindi/English WAV. See `logs/p6_sherpa_supertonic_runtime_20261025.md`.
