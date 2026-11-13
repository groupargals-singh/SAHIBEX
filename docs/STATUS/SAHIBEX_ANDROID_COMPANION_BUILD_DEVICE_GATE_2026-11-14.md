# Android Companion Build and Device Gate Check — 2026-11-14

## Build result
- Ran `bash scripts/build_android_companion_termux.sh`.
- Gradle `:app:assembleDebug`: BUILD SUCCESSFUL (33 tasks, 29s; tasks up-to-date).
- APK v2 signature verification: PASS.
- SHA-256: `055dd0f0e434b14f413682172a1c74e56717ba834e4f51444a0af9de9293bdca`.
- Copied APK to `$HOME/storage/downloads/SAHIBEX-Master-Brain-0.3.6-debug.apk`.
- This build revalidated the existing 0.3.6 artifact; it did not modify app code or silently install/update the app.

## Live device checks
- `adb devices -l`: no authorized/connected ADB device was listed.
- Termux ports 38741 and 38742: no listener.
- Termux:API microphone recording, speech-to-text, TTS and media-player commands are installed.
- Android source includes SahibexAccessibilityService, permission-bound accessibility declaration, local Emergency Stop controls, and bridge server source.
- Because no ADB device and no live bridge listeners were available, installed package state, Accessibility enabled-state, token migration, real pairing, UI-tree response, permitted action and Emergency Stop persistence cannot be physically verified.

## Acceptance boundary
- APK build/signature PASS is software packaging evidence only.
- P8 remains PARTIAL/BLOCKED pending physical app installation/reopen, authenticated bridge pairing, enabled Accessibility service and Emergency Stop acceptance.
- P6 remains PARTIAL pending an explicitly authorized live microphone recording, human transcript review, Main Brain handling and audible speaker playback.
