# SAHIBEX Voice Backend Readiness Correction — 2026-11-13

## Scope
Correct the Voice Brain readiness inspection so it checks the backend SAHIBEX actually selects. The configured default is sherpa-onnx Supertonic-3, but the previous readiness handler inspected Piper only and incorrectly reported TTS unavailable.

## Changes
- Voice readiness now reads `SAHIBEX_TTS_BACKEND` and checks the selected backend.
- For sherpa-onnx Supertonic, it verifies the Python runtime is import-discoverable and all seven required model/config files exist and are non-empty.
- Piper readiness remains supported when explicitly selected.
- Unknown backend values fail closed.
- Output now reports backend, per-language model readiness and aggregate local TTS readiness.
- No microphone recording, speaker playback, cloud upload, model download or permission change was performed.

## Termux evidence
- Local Whisper CLI wrapper exists and passes `whisper-cli -h`.
- Whisper tiny-q5_1 model file exists.
- `sherpa_onnx` is installed in the project virtual environment.
- All seven Supertonic-3 model/config files exist.
- Live Voice Brain readiness result:
  - ASR ready: true
  - TTS engine ready: true
  - Hindi model ready: true
  - English model ready: true
  - status: `LOCAL_VOICE_COMPONENTS_CONFIGURED_ROUND_TRIP_UNVERIFIED`
- Actual local TTS synthesis completed for one Hindi and one English phrase; both returned valid RIFF/WAV bytes at 44.1 kHz.
- No speaker playback was performed. No live microphone recording/ASR round-trip was performed.

## Tests
- Focused voice/internal-brain tests: **116 passed**.
- Full repository regression after the final code and documentation edits: **2,372 passed in 175.05s**, exit 0.
- `compileall -q core app tools scripts tests`: PASS.
- All repository shell scripts pass `bash -n`; `git diff --check`: PASS.
- Common credential-pattern scan: `NO_COMMON_SECRET_PATTERN_MATCH`.

## Acceptance boundary
This corrects a false-negative readiness report and verifies local synthesis output. P6 remains OPEN until the user-authorized physical microphone recording, ASR transcript review, Main Brain processing, and speaker playback round-trip are completed on the phone.
