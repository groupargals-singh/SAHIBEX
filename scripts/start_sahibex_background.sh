#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/SAHIBEX"
cd "$ROOT"
mkdir -p logs
PID_FILE="logs/supervisor.pid"

# Trust the PID file only when it points to the expected supervisor script.
if [ -f "$PID_FILE" ]; then
  PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ "$PID" =~ ^[0-9]+$ ]] && kill -0 "$PID" 2>/dev/null; then
    CMD="$(ps -p "$PID" -o args= 2>/dev/null || true)"
    if [[ "$CMD" == *"/scripts/sahibex_supervisor.sh"* ]]; then
      echo "SAHIBEX SUPERVISOR: ALREADY RUNNING (PID $PID)"
      ./scripts/sahibex_health.sh
      exit 0
    fi
  fi
fi

nohup ./scripts/sahibex_supervisor.sh >> logs/supervisor.log 2>&1 </dev/null &
PID=$!
echo "$PID" > "$PID_FILE"
sleep 2
if ! kill -0 "$PID" 2>/dev/null; then
  echo "SAHIBEX SUPERVISOR: FAILED TO START; inspect logs/supervisor.log"
  exit 1
fi
./scripts/sahibex_health.sh
printf 'SAHIBEX SUPERVISOR: ONLINE (PID %s)\n' "$PID"
