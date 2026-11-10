#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/android-sdk}}"
if [[ ! -f "$SDK/platforms/android-35/android.jar" ]]; then
  echo "Android SDK platform 35 not found under: $SDK" >&2
  exit 2
fi

AAPT2_ARGS=()
if [[ -n "${PREFIX:-}" && -x "$PREFIX/bin/aapt2" ]]; then
  # Termux's Android-native aapt2 works where the Maven Linux ELF does not.
  AAPT2_ARGS+=("-Pandroid.aapt2FromMavenOverride=$PREFIX/bin/aapt2")
fi

ANDROID_HOME="$SDK" ANDROID_SDK_ROOT="$SDK" \
  "$ROOT/android_companion/gradlew" -p "$ROOT/android_companion" \
  :app:assembleDebug --no-daemon "${AAPT2_ARGS[@]}"

APK="$ROOT/android_companion/app/build/outputs/apk/debug/app-debug.apk"
test -s "$APK"
sha256sum "$APK"
if command -v apksigner >/dev/null 2>&1; then
  apksigner verify --verbose "$APK"
fi

DOWNLOADS="$HOME/storage/downloads"
if [[ -d "$DOWNLOADS" && -w "$DOWNLOADS" ]]; then
  cp "$APK" "$DOWNLOADS/SAHIBEX-Master-Brain-0.3.6-debug.apk"
  sha256sum "$DOWNLOADS/SAHIBEX-Master-Brain-0.3.6-debug.apk"
  echo "APK copied to: $DOWNLOADS/SAHIBEX-Master-Brain-0.3.6-debug.apk"
else
  echo "Downloads folder unavailable; APK remains at: $APK"
fi
