#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/SAHIBEX"
cd "$ROOT/android_companion"
SDK="$HOME/android-sdk"
BT="$SDK/build-tools/35.0.0"
ANDROID_JAR="$SDK/platforms/android-35/android.jar"
BUILD="$PWD/build-media"
OUT="$PWD/manual-build/SAHIBEX-Android-Companion-Voice-debug.apk"
VERSION_CODE="${SAHIBEX_COMPANION_VERSION_CODE:-6}"
VERSION_NAME="${SAHIBEX_COMPANION_VERSION_NAME:-0.2.2}"

for path in "$ANDROID_JAR" "$BT/aapt2" "$BT/d8" "$BT/apksigner" "$HOME/.android/debug.keystore"; do
  [ -f "$path" ] || { echo "Required build input missing: $path" >&2; exit 1; }
done
command -v javac >/dev/null
command -v zip >/dev/null
rm -rf "$BUILD"
mkdir -p "$BUILD/classes" "$BUILD/dex" "$BUILD/gen"

javac -Xlint:-options -source 8 -target 8 -classpath "$ANDROID_JAR" -d "$BUILD/classes" \
  app/src/main/java/com/sahibex/companion/MainActivity.java \
  app/src/main/java/com/sahibex/companion/SahibexAccessibilityService.java \
  app/src/main/java/com/sahibex/companion/BridgeServer.java

# The SDK's d8/apksigner files have a /bin/bash shebang, which Android/Termux
# does not provide; invoke these wrappers explicitly through Termux bash.
bash "$BT/d8" --min-api 30 --lib "$ANDROID_JAR" --output "$BUILD/dex" \
  $(find "$BUILD/classes" -name '*.class')
"$BT/aapt2" compile --dir app/src/main/res -o "$BUILD/resources.zip"
"$BT/aapt2" link -o "$BUILD/unsigned.apk" \
  --manifest app/src/main/AndroidManifest.xml -I "$ANDROID_JAR" \
  --min-sdk-version 30 --target-sdk-version 35 \
  --version-code "$VERSION_CODE" --version-name "$VERSION_NAME" \
  -R "$BUILD/resources.zip" --auto-add-overlay --java "$BUILD/gen"
zip -q -j "$BUILD/unsigned.apk" "$BUILD/dex/classes.dex"
bash "$BT/apksigner" sign --v4-signing-enabled false \
  --ks "$HOME/.android/debug.keystore" --ks-key-alias androiddebugkey \
  --ks-pass pass:android --key-pass pass:android --out "$OUT" "$BUILD/unsigned.apk"
bash "$BT/apksigner" verify --print-certs "$OUT"
"$BT/aapt2" dump badging "$OUT" | grep '^package:'
echo "APK_BUILD=PASS output=$OUT"
