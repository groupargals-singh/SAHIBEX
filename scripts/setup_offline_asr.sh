#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# Installs the pinned, open-source whisper.cpp CPU runtime and multilingual
# quantized model outside the repository so large binaries do not pollute git.
ROOT="$HOME/.local/share/sahibex"
SRC="$ROOT/whisper.cpp"
MODEL_DIR="$ROOT/asr-models"
MODEL="$MODEL_DIR/ggml-tiny-q5_1.bin"
PIN="231638a0717b7822784297e5980965ffcec05810"

for tool in git cmake clang curl sha256sum; do
  command -v "$tool" >/dev/null 2>&1 || {
    printf 'Missing tool: %s. Install Termux packages git cmake clang curl first.\n' "$tool" >&2
    exit 2
  }
done
mkdir -p "$ROOT" "$MODEL_DIR" "$HOME/.local/bin"
if [ ! -d "$SRC/.git" ]; then
  git clone --filter=blob:none https://github.com/ggml-org/whisper.cpp.git "$SRC"
fi
git -C "$SRC" fetch --depth 1 origin "$PIN"
git -C "$SRC" checkout --detach "$PIN"
cmake -S "$SRC" -B "$SRC/build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DWHISPER_BUILD_TESTS=OFF \
  -DWHISPER_BUILD_EXAMPLES=ON \
  -DWHISPER_BUILD_SERVER=OFF \
  -DGGML_OPENMP=OFF \
  -DGGML_NATIVE=OFF
cmake --build "$SRC/build" --target whisper-cli -j 2
BIN="$SRC/build/bin/whisper-cli"
test -x "$BIN"

# A wrapper preserves the binary's $ORIGIN lookup for the shared libraries
# that CMake places alongside whisper-cli.
WRAPPER="$HOME/.local/bin/whisper-cli"
if [ -L "$WRAPPER" ] && [ "$(readlink -f "$WRAPPER")" = "$(readlink -f "$BIN")" ]; then
  rm -f "$WRAPPER"  # Remove only the known symlink made by the previous setup.
elif [ -e "$WRAPPER" ] && ! grep -q 'SAHIBEX managed whisper.cpp wrapper' "$WRAPPER"; then
  printf 'Refusing to overwrite an existing non-SAHiBEX executable: %s\n' "$WRAPPER" >&2
  exit 4
fi
WRAPPER_TMP="$WRAPPER.tmp"
cat > "$WRAPPER_TMP" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
# SAHIBEX managed whisper.cpp wrapper
exec "$BIN" "\$@"
EOF
chmod 700 "$WRAPPER_TMP"
mv "$WRAPPER_TMP" "$WRAPPER"

if [ ! -s "$MODEL" ] || [ "$(wc -c < "$MODEL")" -lt 20000000 ]; then
  rm -f "$MODEL.part"
  curl -fL --retry 3 --connect-timeout 20 --max-time 600 \
    'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny-q5_1.bin?download=true' \
    -o "$MODEL.part"
  test "$(wc -c < "$MODEL.part")" -ge 20000000
  mv "$MODEL.part" "$MODEL"
fi

"$HOME/.local/bin/whisper-cli" -h >/dev/null 2>&1 || {
  printf 'whisper-cli failed its smoke check.\n' >&2
  exit 3
}
printf 'Offline ASR runtime ready.\n'
printf 'whisper.cpp commit: %s\n' "$(git -C "$SRC" rev-parse HEAD)"
printf 'runtime sha256: %s\n' "$(sha256sum "$BIN" | awk '{print $1}')"
printf 'model sha256: %s\n' "$(sha256sum "$MODEL" | awk '{print $1}')"
printf 'model bytes: %s\n' "$(wc -c < "$MODEL")"
printf 'binary: %s\nmodel: %s\n' "$HOME/.local/bin/whisper-cli" "$MODEL"
