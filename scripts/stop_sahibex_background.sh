#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/SAHIBEX"
if [ -f "$ROOT/logs/supervisor.pid" ]; then
  PID="$(cat "$ROOT/logs/supervisor.pid")"
  kill "$PID" 2>/dev/null || true
  rm -f "$ROOT/logs/supervisor.pid"
fi
pkill -f 'scripts/sahibex_supervisor.sh' 2>/dev/null || true
echo 'SAHIBEX SUPERVISOR: STOPPED'
