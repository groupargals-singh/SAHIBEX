#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

if [[ -z "${PREFIX:-}" || ! -d "$PREFIX" ]]; then
  echo "Run this script inside Termux; PREFIX is not set." >&2
  exit 2
fi
pkg install -y tesseract curl coreutils
tessdata="$PREFIX/share/tessdata"
mkdir -p "$tessdata"
tmp="$(mktemp "$tessdata/.hin.traineddata.XXXXXX")"
trap 'rm -f "$tmp"' EXIT
curl -fL --retry 2 --connect-timeout 10 --max-time 90 \
  "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/hin.traineddata" \
  -o "$tmp"
expected="4c73ffc59d497c186b19d1e90f5d721d678ea6b2e277b719bee4e2af12271825"
actual="$(sha256sum "$tmp" | awk '{print $1}')"
if [[ "$actual" != "$expected" ]]; then
  echo "Hindi traineddata checksum mismatch; refusing installation." >&2
  exit 3
fi
chmod 644 "$tmp"
mv "$tmp" "$tessdata/hin.traineddata"
trap - EXIT
tesseract --list-langs
echo "OCR runtime ready: Tesseract + verified eng/hin language data."
