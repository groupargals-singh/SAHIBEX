#!/data/data/com.termux/files/usr/bin/bash
set -u

printf 'SAHIBEX ANDROID MEDIA DIAGNOSTICS\n'
printf '===============================\n'

for command_name in termux-speech-to-text termux-tts-speak termux-tts-engines termux-camera-photo termux-camera-info termux-microphone-record; do
  if command -v "$command_name" >/dev/null 2>&1; then
    printf 'CLI %-28s PRESENT\n' "$command_name"
  else
    printf 'CLI %-28s MISSING\n' "$command_name"
  fi
done

if command -v pm >/dev/null 2>&1; then
  packages="$(pm list packages 2>/dev/null || true)"
  if printf '%s\n' "$packages" | grep -qx 'package:com.termux.api'; then
    echo 'API companion package: com.termux.api PRESENT'
  else
    echo 'API companion package: com.termux.api NOT FOUND'
  fi
else
  echo 'Package manager CLI unavailable; cannot confirm API app package.'
fi

if command -v timeout >/dev/null 2>&1 && command -v termux-tts-engines >/dev/null 2>&1; then
  echo 'Checking TTS engine service (max 4 seconds; no utterance is spoken)...'
  output="$(timeout 4 termux-tts-engines 2>&1)"
  code=$?
  if [ "$code" -eq 0 ]; then
    echo 'TTS engine query: PASS'
    printf '%s\n' "$output" | head -20
  elif [ "$code" -eq 124 ]; then
    echo 'TTS engine query: TIMEOUT — Android API service is not responding.'
  else
    echo "TTS engine query: FAIL (exit $code)"
    printf '%s\n' "$output" | head -10
  fi
else
  echo 'Cannot run bounded TTS engine query.'
fi

echo
echo 'No microphone recording or photo capture was initiated by this diagnostic.'
echo 'Do not mark voice/camera LIVE until explicit-consent hardware tests pass.'
