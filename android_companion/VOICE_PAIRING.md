# SAHIBEX Android Companion — Voice pairing and acceptance

## What is ready
- Android Companion voice build: `manual-build/SAHIBEX-Android-Companion-Voice-debug.apk`
- Version: `0.2.2` / versionCode `6` (installed Companion is currently versionCode `4` / versionName `0.2.0`; this is an in-place update with the same signing certificate).
- The native Android speech-recognition UI submits recognized text to SAHIBEX through the authenticated loopback relay. SAHIBEX response is displayed and read aloud using Android TextToSpeech.
- Local relay is `127.0.0.1:38742`; its real E2E request returned HTTP 200 / SUCCESS / VERIFIED.
- The relay calls `MasterBrain.process(..., user_confirmation=False)`. Voice cannot approve protected actions.

## One-time device activation (human tap required)
1. Open Android **Downloads** and install/update `SAHIBEX-Android-Companion-Voice-debug.apk`. If Android blocks installation from Termux/File Manager, enable **Allow from this source** only for the app you used to open the APK, then retry.
2. Open **SAHIBEX Android Companion**.
3. In Termux, run `cat ~/SAHIBEX/data/android_companion_media_token` and copy the token. Keep it private; do not send it to anyone.
4. Paste the token into **SAHIBEX media pairing token** and tap **Save Voice Pairing Token**.
5. Ensure the local bridge is running: `~/SAHIBEX/scripts/sahibex_health.sh` should report `ANDROID VOICE BRIDGE: PROCESS ONLINE`.
6. Tap **Speak to SAHIBEX**, speak a harmless test such as “Hello Sahibex, reply briefly”, and wait for the response. The response should appear in the app and be spoken aloud.
7. If Android asks for microphone/speech-recognition permission, grant it only if you want to enable voice input.

## If voice fails
- Run `~/SAHIBEX/scripts/sahibex_media_diagnostics.sh`; do not wait indefinitely on the old Termux:API commands.
- Check `tail -40 ~/SAHIBEX/logs/media_bridge.log` for local diagnostic errors. Do not share the pairing token.
- Check `curl -fsS http://127.0.0.1:38742/health`.

## Not yet complete
- This is voice input/output, not a wake-word always-listening system.
- Camera capture and visual understanding are not yet connected to the brain. The installed local Qwen3 model is text-only; do not claim image understanding until an OCR/multimodal pipeline passes real tests.
- The Companion Accessibility service still needs its own in-app real-device E2E acceptance if device control is to be marked live.


## P7 voice update — 2026-10-17
- New debug build: `manual-build/SAHIBEX-Android-Companion-P7-debug.apk` (also copied to Android Downloads as `SAHIBEX-Android-Companion-P7-debug.apk`). SHA-256: `750a8abc72c8b53087447ade391376dbb4d062d6c8b130ae06b766d46204b8cb`.
- The Speak button now asks the user to choose Hindi/Hinglish (`hi-IN`) or English (`en-IN`) before opening Android speech recognition. The user can cancel before recording or sending.
- The answer is spoken only when the relay returns HTTP 200 and `success=true`; the app selects Hindi or English TTS based on the response script and displays a clear message if that TTS language is unavailable.
- Android build: PASS with Gradle 8.13 + the device-compatible SDK `aapt2` override. Gradle 9.8 is incompatible with the installed Android Gradle Plugin 8.13; no project build configuration was changed to mask that environment issue.
- **Physical microphone → Main Brain → speaker acceptance remains PENDING.** The current Termux ADB session reports no connected devices, so compilation and relay tests are not being represented as a real acoustic round trip.
- To complete the device gate: install the APK from Downloads, open Companion, pair using the local Termux media token, ensure the media bridge is online, then run one harmless Hindi/Hinglish request and one English request. Confirm each recognized transcript before sending, confirm Main Brain response appears, and verify audible TTS. Also test Cancel, unavailable TTS language, and stopped bridge recovery. Never share the pairing token.
- After restarting the stale bridge process to load the current code, a live authenticated text-relay request returned HTTP 200, `success=true`, `intent=general_request`, and the relevant greeting `Hello SAHIBEX, I am here to assist you.` (`STRUCTURALLY_VALID`, appropriate for a greeting, not a factual-verification claim). This confirms the live text relay only; microphone capture and audible speaker output remain untested on-device.


## Offline speech recognition update (2026-10-25)

The Offline-ASR Companion build captures microphone PCM directly and posts only to the authenticated loopback SAHIBEX media bridge at `/transcribe`. It does not call Android `RecognizerIntent` or a cloud recognizer. Install `manual-build/SAHIBEX-Android-Companion-Offline-ASR-debug-20261025.apk`, ensure the Termux offline runtime/model are provisioned with `scripts/setup_offline_asr.sh`, and start/restart the local media bridge after code changes. Tap **Speak to SAHIBEX (local AI)** to start recording and tap again to stop; maximum capture is 20 seconds. The transcript is editable and must be confirmed before it reaches Main Brain. Cancel means nothing is sent.

The current output still uses Android `TextToSpeech`; custom output voice selection is deferred until an approved sample is supplied. Physical microphone-to-audible-TTS acceptance is not claimed complete in this document. Detailed evidence: `../logs/p6_offline_asr_implementation_20261025.md`.

## Voice quality correction — 2026-10-29
- Updated Companion: `manual-build/SAHIBEX-Frontend-v1.6-debug.apk` (version 0.3.3 / versionCode 11; SHA-256 `ad494426d1ea97062906e5dd4cf094208238d44feddb5307b89a4749345d22ad`).
- Local neural audio now has bounded peak normalization with headroom. Automatic Android TextToSpeech fallback has been removed so a neural-voice error will be shown rather than unexpectedly playing a different Android voice.
- Local Hindi/English WAV generation and APK build/signature checks passed. Physical speaker clarity and naturalness remain pending until this APK is installed and tested on the phone. The bundled voice is not a clone of a personal voice sample.
