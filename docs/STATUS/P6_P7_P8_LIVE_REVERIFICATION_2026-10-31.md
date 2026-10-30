# SAHIBEX P6/P7/P8 live re-verification — 2026-10-31

## Runtime correction and evidence
- The existing media bridge PID was inspected by exact command line and project working directory before restart. It was an old process using Termux system Python rather than the project virtual environment; the service source was not changed and no credentials were displayed.
- Restarted only that identified bridge process through `scripts/start_sahibex_media_bridge.sh`. The replacement inherited the project `.venv` environment. Loopback `/health` returned HTTP 200.
- Authenticated `/synthesize` returned HTTP 200, `Content-Type: audio/wav`, and 332,666 bytes for a short English phrase. WAV RIFF/WAVE header was valid. The previous HTTP 503 was caused by testing the stale process; it is not the current bridge result.
- Unauthenticated `/synthesize` and `/vision/ocr` requests both returned HTTP 401 before the restart; authentication remains required.
- Local ASR runtime readiness: `LocalWhisperCppRecognizer.is_ready()` returned true. Direct local transcription of the pinned whisper.cpp `samples/jfk.wav` fixture passed: 11.0-second English fixture, `whisper.cpp`, `local_offline`, language `en`, transcript matched the expected JFK sentence.
- TTS and ASR are software/runtime checks only. They do not prove physical microphone capture, Hindi/Hinglish real-speaker accuracy, transcript confirmation in the Android UI, Main Brain reply, or audible phone speaker playback.

## Android Companion build
- Ran `bash scripts/build_android_companion_termux.sh`.
- Gradle `:app:assembleDebug`: BUILD SUCCESSFUL (33 tasks up-to-date).
- APK metadata: package `com.sahibex.companion`, versionCode 13, versionName `0.3.5`, label `SAHIBEX — Master Brain`.
- APK v2 signature verification: PASS.
- SHA-256: `abcc35c794f693399ebd05aadc97e0f2dbe3a7019276b590d97c889f3ccd68b1`.
- Copied matching artifact to `$HOME/storage/downloads/SAHIBEX-Master-Brain-0.3.5-debug.apk`; source and Downloads hashes match.
- Package `com.sahibex.companion` is installed on the Android phone (`pm path` returned its base.apk). `adb devices -l` remains empty. Termux cannot read the enabled Accessibility service setting (Android denied cross-user settings access); no Accessibility enablement or live action is claimed.

## Full software regression
- `.venv/bin/python -m pytest -q tests/` — **2201 passed in 194.34s**, exit code 0.
- This is a full software regression PASS; it does not promote physical P6/P8 or semantic P7 gates.

## Gate disposition (unchanged)
- P6: SOFTWARE RUNTIME RE-VERIFIED; physical mic → ASR → user-confirmed transcript → Main Brain → audible TTS remains PARTIAL/PENDING. Real Hindi/Hinglish corpus and acoustic acceptance remain open.
- P7: PARTIAL/BLOCKED. OCR-only path remains honest; no semantic image-understanding model/provider or semantic accuracy dataset is installed/configured.
- P8: SOURCE/CONTRACT/BUILD PASS; physical Accessibility service enablement, UI action, persistent Emergency Stop and on-device resume acceptance remain BLOCKED/PENDING.
- P10: BLOCKED. The historical 417-item original is still not recovered. Do not fabricate or relabel a reconstructed list as historical; a new reconstructed baseline requires explicit user approval.
- P11: BLOCKED by the unresolved acceptance/provenance gates above.

## Safety and preservation
- No reset, git clean, backup deletion, database deletion, permission grant, token rotation, or constitution change was performed.
- The bridge remains loopback-only; pairing/control tokens were not displayed or committed.
- Android microphone, camera and Accessibility permissions were not granted by automation.
