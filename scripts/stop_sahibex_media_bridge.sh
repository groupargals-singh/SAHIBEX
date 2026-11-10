#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/SAHIBEX"
PROJECT_ROOT="$HOME/SAHIBEX"
PID_FILE="logs/media_bridge.pid"
if [[ ! -f "$PID_FILE" ]]; then
  echo "SAHIBEX media bridge PID file not found; no process was stopped."
  exit 0
fi
pid="$(cat "$PID_FILE" 2>/dev/null || true)"
if [[ ! "$pid" =~ ^[0-9]+$ ]]; then
  echo "Invalid or empty media bridge PID file; refusing to kill anything." >&2
  exit 1
fi
if ! kill -0 "$pid" 2>/dev/null; then
  echo "Recorded media bridge PID is no longer running; no process was killed."
  : > "$PID_FILE"
  exit 0
fi
cmd="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
cwd="$(readlink "/proc/$pid/cwd" 2>/dev/null || true)"
if [[ "$cmd" != *"tools.android_companion_media_server"* || "$cwd" != "$PROJECT_ROOT" ]]; then
  echo "PID $pid is not the SAHIBEX media bridge in $PROJECT_ROOT; refusing to kill it." >&2
  exit 1
fi
kill -TERM "$pid"
for _ in $(seq 1 10); do
  kill -0 "$pid" 2>/dev/null || break
  sleep 0.5
done
if kill -0 "$pid" 2>/dev/null; then
  echo "Verified media bridge PID $pid did not stop; no further signal sent." >&2
  exit 1
fi
: > "$PID_FILE"
echo "Stopped verified SAHIBEX media bridge PID $pid. PID file retained empty."
