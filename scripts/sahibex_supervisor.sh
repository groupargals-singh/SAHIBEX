#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/SAHIBEX"
cd "$ROOT"
export SAHIBEX_MODEL_PROVIDER=local
export SAHIBEX_SEARCH_BACKEND=duckduckgo_html
mkdir -p logs

if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock || true
fi

while true; do
  if ! curl -fsS --max-time 2 http://127.0.0.1:8080/health >/dev/null 2>&1; then
    ./scripts/start_local_model.sh >> logs/supervisor.log 2>&1 || true
  fi

  # Keep the optional native Companion voice relay alive by PID, not by HTTP
  # health probes: a single Brain request can legitimately take tens of seconds.
  MEDIA_PID_FILE="logs/media_bridge.pid"
  MEDIA_PID=""
  if [ -f "$MEDIA_PID_FILE" ]; then
    MEDIA_PID="$(cat "$MEDIA_PID_FILE" 2>/dev/null || true)"
  fi
  if [ -z "$MEDIA_PID" ] || ! kill -0 "$MEDIA_PID" 2>/dev/null; then
    nohup python -m tools.android_companion_media_server >> logs/media_bridge.log 2>&1 &
    echo $! > "$MEDIA_PID_FILE"
    echo "SAHIBEX media bridge restarted (PID $(cat "$MEDIA_PID_FILE"))." >> logs/supervisor.log
  fi
  sleep 10
done
