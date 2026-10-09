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
