#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/SAHIBEX"
mkdir -p logs data
PID_FILE="logs/media_bridge.pid"
LOG_FILE="logs/media_bridge.log"
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "SAHIBEX media bridge already running (PID $(cat "$PID_FILE"))."
  exit 0
fi
source .venv/bin/activate
export SAHIBEX_MODEL_PROVIDER="${SAHIBEX_MODEL_PROVIDER:-local}"
export SAHIBEX_SEARCH_BACKEND="${SAHIBEX_SEARCH_BACKEND:-duckduckgo_html}"
nohup python -m tools.android_companion_media_server >>"$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
for _ in $(seq 1 20); do
  if curl -fsS --max-time 1 http://127.0.0.1:38742/health >/dev/null 2>&1; then
    echo "SAHIBEX MEDIA BRIDGE: ONLINE"
    echo "Pairing token file: $HOME/SAHIBEX/data/android_companion_media_token"
    echo "Read token only when pairing the Android Companion; keep it private."
    exit 0
  fi
  sleep 1
done
echo "SAHIBEX MEDIA BRIDGE: FAILED TO START; inspect $LOG_FILE" >&2
exit 1
