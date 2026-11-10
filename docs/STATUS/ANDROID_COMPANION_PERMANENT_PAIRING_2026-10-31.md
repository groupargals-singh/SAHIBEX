# SAHIBEX Android Companion — permanent pairing and reconnect update

Date: 2026-10-31

## Problem found
- The Companion required a media bearer token before typed chat and voice could start.
- The v0.3.5 app stored that token as a plaintext SharedPreferences value and did not verify the authenticated media session on app resume. The user could see a pairing prompt without a clear live connection state.
- The app's separate `token` used by the Accessibility/control bridge is not the media pairing token. The two credentials serve different services and must not be mixed.

## Changes
- Added AES-256-GCM token encryption using Android Keystore; the encryption key is non-exportable and generated on-device.
- Added a one-time migration path: an existing v0.3.5 plaintext `media_token` is read once, encrypted, and removed from plaintext preferences. Existing token is preserved; no rotation occurs.
- All Companion media requests now read through the encrypted-token accessor.
- Once pairing exists, the token entry and Save button are hidden; the user is not asked to paste it again on normal app restarts or in-place updates.
- Added authenticated `GET /session` endpoint. It returns only service/session state, never the token.
- Companion checks `/session` on app resume and retries every 15 seconds while foregrounded. If Termux bridge is temporarily offline, the saved credential remains and the app retries when the bridge returns.
- The bridge remains loopback-only (`127.0.0.1:38742`). No external network exposure, permission grants, token rotation, or destructive action was introduced.
- Bumped Android Companion to versionCode 14 / versionName 0.3.6. Build script now copies `SAHIBEX-Master-Brain-0.3.6-debug.apk`.

## Verification
- Media bridge targeted tests: 19 passed, including authenticated session success and unauthenticated 401 rejection.
- Live `/session` probe: no Authorization header -> HTTP 401; correct local token -> HTTP 200 and `authenticated=true`. Token value was not printed.
- Live `/health`: HTTP 200.
- Java compile and Gradle package: BUILD SUCCESSFUL; 33 tasks, exit code 0.
- APK metadata: `com.sahibex.companion`, versionCode 14, versionName `0.3.6`, label `SAHIBEX — Master Brain`.
- APK v2 signature verification: PASS. SHA-256: `055dd0f0e434b14f413682172a1c74e56717ba834e4f51444a0af9de9293bdca`.
- Build artifact and Downloads copy hashes match: `$HOME/storage/downloads/SAHIBEX-Master-Brain-0.3.6-debug.apk`.
- Full repository regression: `.venv/bin/python -m pytest -q tests/` — **2202 passed in 213.89s**, exit code 0.
- `compileall` for changed Python files, `bash -n scripts/build_android_companion_termux.sh`, and `git diff --check`: PASS.
- The Android installer was opened for the user-authorized in-place update. Physical installation and on-device token migration/reopen acceptance are not yet confirmed; do not report them as PASS.

## Acceptance boundaries
- Software auto-connect and 15-second foreground retry are implemented. This does not silently launch Termux or execute commands from the Android app; if the Termux bridge process is stopped, it must be started by the authorized Termux runtime, after which Companion reconnects automatically.
- Physical Android UI acceptance is still required to prove that the installed v0.3.6 app migrates the existing preference, displays CONNECTED, survives app close/reopen, and does not request the token again.
- Physical microphone -> offline ASR -> transcript confirmation -> Main Brain -> neural TTS -> speaker is still not accepted by this code change alone.
- P6 remains PARTIAL pending physical audio acceptance. P7 semantic image understanding and P8 physical Accessibility/Emergency Stop acceptance remain separate open gates. P10 historical 417-item source and P11 release dependencies remain unchanged.

## Preservation
- Backups created before edits: `backups/android_companion_20261031/MainActivity.java.pre_permanent_pairing`, `backups/android_companion_20261031/android_companion_media_server.py.pre_permanent_pairing`, and `backups/android_companion_20261031/test_android_companion_media_server.py.pre_permanent_pairing`.
- Existing untracked `.fix_research_multi_finding.py` and `backups/` content were preserved. No `git clean`, reset, database deletion, permission grant, or credential rotation.

## Additional live Main Brain/TTS probe
- Authenticated `/voice` request `Namaste` returned HTTP 200, `success=true`, `STRUCTURALLY_VALID`, with the expected Hindi greeting. This exercises the deterministic greeting path only.
- A broader conversational request returned HTTP 200 with `success=false`, `verification_status=FAILED`, message `Mother Brain operational processing failed.` The local model endpoint `127.0.0.1:8080/health` was connection-refused, and no local model server process was running. This is the current reason model-dependent app questions cannot be answered; no weak 1.7B fallback or RAM guard bypass was started.
- Authenticated `/synthesize` returned HTTP 200, `audio/wav`, 295,104 bytes with a valid RIFF header. Neural TTS software path is available; this is not proof of audible phone speaker playback.
- Therefore the pairing/session software fix is PASS, deterministic greeting and TTS backend probes PASS, but general Main Brain chat and physical voice round-trip remain BLOCKED/PENDING until an approved model runtime is available and actual phone testing passes.

## Local model resource gate
- Read-only memory snapshot after the failed general chat probe: 7.3 GiB total, 1.7 GiB available, 4.3 GiB swap free. `scripts/start_local_model.sh` requires 3 GiB available for the default Qwen3-4B; its low-RAM 1.7B fallback requires at least 1.8 GB available. The current snapshot is below both thresholds.
- Local model was deliberately NOT started. No RAM guard was bypassed and the known weak 1.7B fallback was not launched. General model-dependent responses remain blocked until memory is safely available or an approved alternate model endpoint is configured.


## Later runtime correction — 2026-10-31
- A later live check supersedes the earlier offline snapshot in this report: `127.0.0.1:8080/health` returned HTTP 200 and `/v1/models` reported `Qwen3-1.7B-Q4_K_M.gguf`. The model was already running; this fix did not start or change it.
- Latest available RAM snapshot was approximately 1.2 GiB. Do not infer that the 4B model can safely start, or that general answer quality is accepted, from the 1.7B health response.
- The identity numbered-format acceptance above is a deterministic curated fast path and does not depend on this model. General model quality and broader verified-evidence retrieval remain separately unaccepted.
