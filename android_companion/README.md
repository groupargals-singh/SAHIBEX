# SAHIBEX Android Companion Bridge

Additive source/protocol stage for #15 Real Computer/UI Control.

Security boundary: loopback-only transport, per-session random token, HMAC request signing on the Python side, and human-granted Android Accessibility permission. SAHIBEX remains the authority; the companion never grants permission itself.

Build status: Android SDK 35, javac, aapt2, d8, apksigner, and Gradle are available on this device. Android Gradle Plugin 8.13.0 is not compatible with the installed Gradle 9.8, so the companion can be built on-device through the SDK toolchain directly. The manual debug APK is compiled, signed, and signature-verified successfully.

Device activation boundary: installing/replacing the companion APK and enabling the Accessibility service are Android user/system actions that this Termux UID is not authorized to perform programmatically. After installation, enable the SAHIBEX Accessibility service manually, open the companion, then run the secure screenshot test. Real screenshot/UI-tree/tap/type/key and emergency-stop/audit E2E must be marked PASS only after that device-side verification.

## Voice companion bridge (v0.2.0, versionCode 4)

The updated Companion includes native Android speech recognition and Android TextToSpeech playback. It sends the recognized transcript to the SAHIBEX Master Brain through a loopback-only HTTP bridge on `127.0.0.1:38742`. The phone app must be installed/updated and paired before voice can be called live.

Termux setup: `scripts/start_sahibex_media_bridge.sh` starts the authenticated local bridge. The random pairing token is stored in `data/android_companion_media_token` with mode `0600`; never commit or share it. Enter that token into the Companion app and save it locally. The server accepts only bearer-authenticated requests, limits input size, and always calls `MasterBrain.process(..., user_confirmation=False)`: spoken words never count as authorization for protected actions.

APK: `manual-build/SAHIBEX-Android-Companion-Voice-debug.apk`. It is signed with the same Android Debug certificate as the currently installed Companion and has versionCode 4, versionName 0.2.0. Build verified through javac, D8, AAPT2 link, and apksigner.

The voice relay's real localhost E2E smoke test returned HTTP 200 / SUCCESS / VERIFIED using the local model. This validates the Termux server route, not yet physical microphone/TTS operation in the updated Android UI. User must approve the Android app update and grant any requested permissions.

The old Termux:API CLI path remains unresponsive on this phone. The official F-Droid Termux:API APK has a different signing certificate from the installed Termux app and must not be installed over this setup. The native Companion bridge is the safe alternative. Camera capture and image understanding are still not implemented in this v0.2.0 Companion; vision remains pending.
