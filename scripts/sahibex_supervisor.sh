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

  # A responsive health endpoint is authoritative. Never start a duplicate
  # server just because a PID file is stale while an existing bridge is healthy.
  MEDIA_PID_FILE="logs/media_bridge.pid"
  if ! curl -fsS --max-time 2 http://127.0.0.1:38742/health >/dev/null 2>&1; then
    MEDIA_PID=""
    if [ -f "$MEDIA_PID_FILE" ]; then
      MEDIA_PID="$(cat "$MEDIA_PID_FILE" 2>/dev/null || true)"
    fi
    MEDIA_CMD=""
    if [[ "$MEDIA_PID" =~ ^[0-9]+$ ]] && kill -0 "$MEDIA_PID" 2>/dev/null; then
      MEDIA_CMD="$(ps -p "$MEDIA_PID" -o args= 2>/dev/null || true)"
    fi
    if [[ "$MEDIA_CMD" == *"tools.android_companion_media_server"* ]]; then
      # Process exists but health is not responding. Do not spawn another
      # server against the same port; report degraded state and retry later.
      echo "SAHIBEX media bridge process alive but health check failed (PID $MEDIA_PID)." >> logs/supervisor.log
    else
      nohup python -m tools.android_companion_media_server >> logs/media_bridge.log 2>&1 </dev/null &
      NEW_PID=$!
      echo "$NEW_PID" > "$MEDIA_PID_FILE"
      echo "SAHIBEX media bridge start requested (PID $NEW_PID)." >> logs/supervisor.log
    fi
  fi
  sleep 10
done
