# SAHIBEX Android Companion Bridge

Additive source/protocol stage for #15 Real Computer/UI Control.

Security boundary: loopback-only transport, per-session random token, HMAC request signing on the Python side, and human-granted Android Accessibility permission. SAHIBEX remains the authority; the companion never grants permission itself.

Build status: Android SDK 35, javac, aapt2, d8, apksigner, and Gradle are available on this device. Android Gradle Plugin 8.13.0 is not compatible with the installed Gradle 9.8, so the companion can be built on-device through the SDK toolchain directly. The manual debug APK is compiled, signed, and signature-verified successfully.

Device activation boundary: installing/replacing the companion APK and enabling the Accessibility service are Android user/system actions that this Termux UID is not authorized to perform programmatically. After installation, enable the SAHIBEX Accessibility service manually, open the companion, then run the secure screenshot test. Real screenshot/UI-tree/tap/type/key and emergency-stop/audit E2E must be marked PASS only after that device-side verification.

## Voice companion bridge (v0.2.2, versionCode 6)

The updated Companion includes native Android speech recognition and Android TextToSpeech playback. It sends the recognized transcript to the SAHIBEX Master Brain through a loopback-only HTTP bridge on `127.0.0.1:38742`. The phone app must be installed/updated and paired before voice can be called live.

Termux setup: `scripts/start_sahibex_media_bridge.sh` starts the authenticated local bridge. The random pairing token is stored in `data/android_companion_media_token` with mode `0600`; never commit or share it. Enter that token into the Companion app and save it locally. The server accepts only bearer-authenticated requests, limits input size, and always calls `MasterBrain.process(..., user_confirmation=False)`: spoken words never count as authorization for protected actions.

APK: `manual-build/SAHIBEX-Android-Companion-Voice-debug.apk`. It is signed with the same Android Debug certificate as the currently installed Companion and has versionCode 6, versionName 0.2.2. The installed app is currently versionCode 4 / versionName 0.2.0; update it from Downloads to enable the current voice UI. Build verified through javac, D8, AAPT2 link, and apksigner.

The voice relay's real localhost E2E smoke test returned HTTP 200 / SUCCESS / VERIFIED using the local model. This validates the Termux server route, not yet physical microphone/TTS operation in the updated Android UI. User must approve the Android app update and grant any requested permissions.

The old Termux:API CLI path remains unresponsive on this phone. The official F-Droid Termux:API APK has a different signing certificate from the installed Termux app and must not be installed over this setup. The native Companion bridge is the safe alternative. Camera capture and image understanding are still not implemented in this v0.2.2 Companion; vision remains pending.


## SAHIBEX Brain Frontend v0.3.2 (2026-10-29)

- Dark Master Brain screen, animated neural-core visualization, chat transcript, typing composer, Send, VOICE and CAM controls; custom brain launcher icon.
- Typing and voice use the authenticated local `/voice` endpoint; protected actions remain subject to Master Brain permission checks. Pairing, emergency-stop and device-test controls remain.
- Front-camera preview and generic local frame-difference motion meter. A deliberate `ANALYZE CURRENT FRAME (LOCAL OCR)` action sends one still to the new authenticated `/vision/ocr` endpoint. Requests and images are bounded; OCR images are held in a private temporary directory and removed after processing. Text is explicitly untrusted. OCR only—not semantic scene understanding, identity recognition, pose or gesture understanding.
- Build output: `manual-build/SAHIBEX-Frontend-v1.5-debug.apk` (versionCode 10, versionName 0.3.2). Full repository regression: 2172 passed; Java, D8, AAPT2 and APK signature checks passed.
- Physical-device and live-bridge acceptance remains pending. True 3D avatar, simultaneous face-to-face voice/video and lip-sync remain future work; no P6/P7/P8 gate is promoted.

## Latest voice build (2026-10-29)
- `manual-build/SAHIBEX-Frontend-v1.6-debug.apk`, version 0.3.3 / versionCode 11, SHA-256 `ad494426d1ea97062906e5dd4cf094208238d44feddb5307b89a4749345d22ad`.
- Local neural output is peak-normalized with headroom. Automatic Android TTS fallback is disabled; synthesis/playback failure is surfaced rather than switching to another voice. Physical device listening and custom-voice acceptance remain pending.
