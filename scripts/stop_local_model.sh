#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/SAHIBEX"
PIDFILE="$ROOT/logs/llama-server.pid"
if [ -f "$PIDFILE" ]; then
  PID="$(cat "$PIDFILE")"
  if kill -0 "$PID" 2>/dev/null; then kill "$PID"; fi
  rm -f "$PIDFILE"
fi
pkill -f 'llama-server.*127.0.0.1.*8080' 2>/dev/null || true
echo "SAHIBEX LOCAL MODEL: STOPPED"
