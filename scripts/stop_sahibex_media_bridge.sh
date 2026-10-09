#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/SAHIBEX"
PID_FILE="logs/media_bridge.pid"
if [ ! -f "$PID_FILE" ]; then echo 'SAHIBEX media bridge is not running (no PID file).'; exit 0; fi
pid="$(cat "$PID_FILE")"
case "$pid" in ''|*[!0-9]*) echo 'Invalid media bridge PID file; refusing to kill.' >&2; exit 1;; esac
if kill -0 "$pid" 2>/dev/null; then kill "$pid"; echo "Stopped SAHIBEX media bridge PID $pid."; else echo 'SAHIBEX media bridge process already stopped.'; fi
rm -f "$PID_FILE"
