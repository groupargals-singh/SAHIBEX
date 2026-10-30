#!/data/data/com.termux/files/usr/bin/bash
set -u
ROOT="$HOME/SAHIBEX"
cd "$ROOT" || exit 1
export SAHIBEX_MODEL_PROVIDER=local
export SAHIBEX_SEARCH_BACKEND=google_news_rss
export SAHIBEX_SELF_IMPROVEMENT_AUDIT_DB="${SAHIBEX_SELF_IMPROVEMENT_AUDIT_DB:-$ROOT/data/runtime/self_improvement_audit.sqlite3}"
export SAHIBEX_SELF_IMPROVEMENT_STATE_DB="${SAHIBEX_SELF_IMPROVEMENT_STATE_DB:-$ROOT/data/runtime/self_improvement_state.sqlite3}"
mkdir -p logs
LOCK_DIR="logs/supervisor.lock"
PID_FILE="logs/supervisor.pid"
LOG_FILE="logs/supervisor.log"
MODEL_RETRY_SECONDS=45
MODEL_AUTOSTART="${SAHIBEX_SUPERVISOR_MODEL_AUTOSTART:-1}" # Set to 0 to recover the bridge without silently selecting a low-RAM model.
MODEL_RESTART_ATTEMPTED=0 # Do not repeatedly relaunch the memory-heavy 4B model in one supervisor session.
BRIDGE_RETRY_SECONDS=60
LOOP_SECONDS=5
LAST_MODEL_ATTEMPT=0
LAST_BRIDGE_ATTEMPT=0
LAST_MODEL_WARNING=0
LAST_BRIDGE_WARNING=0
log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG_FILE"; }
model_healthy() { curl -fsS --max-time 2 http://127.0.0.1:8080/health >/dev/null 2>&1; }
bridge_healthy() { curl -fsS --max-time 2 http://127.0.0.1:38742/health >/dev/null 2>&1; }
# Match full command arguments while excluding awk/grep and their parent test shell.
find_model_pid() { ps -A -o pid=,comm=,args= | awk '$0 ~ /llama-server/ && $0 ~ /--port 8080/ && $0 !~ /awk/ && $0 !~ /grep/ { print $1; exit }' || true; }
find_bridge_pid() { ps -A -o pid=,comm=,args= | awk '$2 == "python" && $0 ~ /tools.android_companion_media_server/ { print $1; exit }' || true; }

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  OLD_PID="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
  if [[ "$OLD_PID" =~ ^[0-9]+$ ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    OLD_CMD="$(ps -p "$OLD_PID" -o args= 2>/dev/null || true)"
    if [[ "$OLD_CMD" == *"scripts/sahibex_supervisor.sh"* ]]; then
      echo "SAHIBEX SUPERVISOR: ALREADY RUNNING (PID $OLD_PID)"
      exit 0
    fi
  fi
  if [[ ! "$OLD_PID" =~ ^[0-9]+$ ]] || ! kill -0 "$OLD_PID" 2>/dev/null; then
    rm -f "$LOCK_DIR/pid"
    rmdir "$LOCK_DIR" 2>/dev/null || true
    if ! mkdir "$LOCK_DIR" 2>/dev/null; then
      echo "SAHIBEX SUPERVISOR: LOCK BUSY; refusing duplicate start"
      exit 1
    fi
  else
    echo "SAHIBEX SUPERVISOR: LOCK OWNER UNCLEAR; refusing duplicate start"
    exit 1
  fi
fi
echo "$$" > "$LOCK_DIR/pid"
echo "$$" > "$PID_FILE"
cleanup() {
  local owner
  owner="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
  if [[ "$owner" == "$$" ]]; then
    rm -f "$LOCK_DIR/pid"
    rmdir "$LOCK_DIR" 2>/dev/null || true
    if [[ "$(cat "$PID_FILE" 2>/dev/null || true)" == "$$" ]]; then rm -f "$PID_FILE"; fi
  fi
}
trap cleanup EXIT
trap 'exit 0' INT TERM
if command -v termux-wake-lock >/dev/null 2>&1; then termux-wake-lock >/dev/null 2>&1 || true; fi
log "Supervisor started (PID $$). Recovery has cooldowns; no public tunnel is started."

while true; do
  NOW="$(date +%s)"
  if model_healthy; then
    LAST_MODEL_WARNING=0
  else
    MODEL_PID="$(find_model_pid)"
    if [[ -n "$MODEL_PID" ]]; then
      if (( NOW - LAST_MODEL_WARNING >= 60 )); then
        log "Model health failed but llama-server process PID $MODEL_PID exists; refusing duplicate start."
        LAST_MODEL_WARNING="$NOW"
      fi
    elif [[ "$MODEL_AUTOSTART" != "1" ]]; then
      if (( NOW - LAST_MODEL_WARNING >= 300 )); then
        log "Model remains offline; automatic model start is disabled by SAHIBEX_SUPERVISOR_MODEL_AUTOSTART=0. Bridge recovery remains enabled."
        LAST_MODEL_WARNING="$NOW"
      fi
    elif (( MODEL_RESTART_ATTEMPTED == 0 && NOW - LAST_MODEL_ATTEMPT >= MODEL_RETRY_SECONDS )); then
      LAST_MODEL_ATTEMPT="$NOW"
      MODEL_RESTART_ATTEMPTED=1
      log "Model is offline and no llama-server process exists; making the single bounded recovery attempt for this supervisor session."
      if ./scripts/start_local_model.sh >> "$LOG_FILE" 2>&1; then
        log "Model recovery command succeeded."
        LAST_MODEL_WARNING=0
      else
        log "Model recovery attempt failed; automatic model retries are disabled for this supervisor session to prevent repeated memory pressure. Start manually after checking RAM."
      fi
    elif (( MODEL_RESTART_ATTEMPTED == 1 && NOW - LAST_MODEL_WARNING >= 300 )); then
      log "Model remains offline; automatic restart is disabled after the one recovery attempt."
      LAST_MODEL_WARNING="$NOW"
    fi
  fi

  if bridge_healthy; then
    LAST_BRIDGE_WARNING=0
  else
    BRIDGE_PID="$(find_bridge_pid)"
    if [[ -n "$BRIDGE_PID" ]]; then
      if (( NOW - LAST_BRIDGE_WARNING >= 60 )); then
        log "Bridge health failed but bridge process PID $BRIDGE_PID exists; refusing duplicate start."
        LAST_BRIDGE_WARNING="$NOW"
      fi
    elif (( NOW - LAST_BRIDGE_ATTEMPT >= BRIDGE_RETRY_SECONDS )); then
      LAST_BRIDGE_ATTEMPT="$NOW"
      log "Bridge is offline and no bridge process exists; attempting one start."
      nohup python -m tools.android_companion_media_server >> logs/media_bridge.log 2>&1 </dev/null &
      BRIDGE_PID=$!
      echo "$BRIDGE_PID" > logs/media_bridge.pid
      sleep 2
      if bridge_healthy; then
        log "Bridge health check passed after start (PID $BRIDGE_PID)."
        LAST_BRIDGE_WARNING=0
      else
        log "Bridge did not become healthy within 2s; no duplicate will be launched for ${BRIDGE_RETRY_SECONDS}s."
      fi
    fi
  fi
  sleep "$LOOP_SECONDS"
done
