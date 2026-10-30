#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/SAHIBEX"
cd "$ROOT"
mkdir -p logs
PID_FILE="logs/supervisor.pid"
# Do not implicitly start a public tunnel: it changes network exposure.
if [ -f "$PID_FILE" ]; then
  PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ "$PID" =~ ^[0-9]+$ ]] && kill -0 "$PID" 2>/dev/null; then
    CMD="$(ps -p "$PID" -o args= 2>/dev/null || true)"
    if [[ "$CMD" == *"scripts/sahibex_supervisor.sh"* ]]; then
      echo "SAHIBEX SUPERVISOR: ALREADY RUNNING (PID $PID)"
      ./scripts/sahibex_health.sh || true
      exit 0
    fi
  fi
fi
nohup ./scripts/sahibex_supervisor.sh >> logs/supervisor.log 2>&1 </dev/null &
PID=$!
echo "$PID" > "$PID_FILE"
READY=0
for _ in $(seq 1 60); do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "SAHIBEX SUPERVISOR: EXITED DURING STARTUP; inspect logs/supervisor.log"
    exit 1
  fi
  if curl -fsS --max-time 2 http://127.0.0.1:8080/health >/dev/null 2>&1; then READY=1; break; fi
  sleep 1
done
if [ "$READY" -ne 1 ]; then
  echo "SAHIBEX STARTUP: TIMEOUT waiting for local model; inspect logs/supervisor.log and logs/llama-server.log"
  exit 1
fi
./scripts/sahibex_health.sh
printf 'SAHIBEX SUPERVISOR: ONLINE (PID %s)\n' "$PID"
echo "PUBLIC TUNNEL WATCHDOG: NOT STARTED (requires separate explicit opt-in)"
