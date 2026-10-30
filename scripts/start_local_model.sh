#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/SAHIBEX"
DEFAULT_MODEL="$HOME/models/Qwen3-4B-Q4_K_M.gguf"
SMALL_MODEL="$HOME/models/Qwen3-1.7B-Q4_K_M.gguf"
MODEL_EXPLICIT=0
if [[ -n "${SAHIBEX_LOCAL_MODEL_PATH:-}" ]]; then MODEL_EXPLICIT=1; fi
MODEL="${SAHIBEX_LOCAL_MODEL_PATH:-$DEFAULT_MODEL}"
SERVER="$HOME/llama.cpp/build/bin/llama-server"
LOG="$ROOT/logs/llama-server.log"
PIDFILE="$ROOT/logs/llama-server.pid"
LOCKDIR="$ROOT/logs/model-start.lock"
CTX_SIZE="${SAHIBEX_LOCAL_CTX_SIZE:-1024}"
MIN_AVAILABLE_KB="${SAHIBEX_MODEL_MIN_AVAILABLE_KB:-3145728}" # 3 GiB
cd "$ROOT"
mkdir -p logs

if [ ! -x "$SERVER" ]; then echo "ERROR: llama-server not found/executable: $SERVER"; exit 1; fi
if [ ! -f "$MODEL" ]; then echo "ERROR: model not found: $MODEL"; exit 1; fi
if ! [[ "$CTX_SIZE" =~ ^[0-9]+$ ]] || (( CTX_SIZE < 512 || CTX_SIZE > 8192 )); then
  echo "ERROR: invalid context size '$CTX_SIZE' (allowed: 512..8192)."
  exit 1
fi

if curl -fsS --max-time 2 http://127.0.0.1:8080/health >/dev/null 2>&1; then
  ACTIVE_MODELS="$(curl -fsS --max-time 2 http://127.0.0.1:8080/v1/models || true)"
  if grep -Fq "$(basename "$MODEL")" <<<"$ACTIVE_MODELS"; then
    echo "SAHIBEX LOCAL MODEL: ONLINE (127.0.0.1:8080; $(basename "$MODEL"))"
    exit 0
  fi
  if (( MODEL_EXPLICIT == 0 )) && grep -Fq "$(basename "$SMALL_MODEL")" <<<"$ACTIVE_MODELS"; then
    echo "SAHIBEX LOCAL MODEL: ONLINE (127.0.0.1:8080; existing low-RAM fallback $(basename "$SMALL_MODEL"))"
    exit 0
  fi
  echo "ERROR: a different model is already serving on port 8080; refusing duplicate launch."
  exit 1
fi

EXISTING_PID="$(ps -A -o pid=,comm=,args= | awk '$0 ~ /llama-server/ && $0 ~ /--port 8080/ && $0 !~ /awk/ && $0 !~ /grep/ { print $1; exit }' || true)"
if [[ -n "$EXISTING_PID" ]]; then
  echo "ERROR: llama-server PID $EXISTING_PID exists but health is offline; refusing a duplicate launch. Inspect logs/llama-server.log."
  exit 1
fi

if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "ERROR: another model startup is in progress (lock: $LOCKDIR); refusing duplicate launch."
  exit 1
fi
cleanup_lock() { rmdir "$LOCKDIR" 2>/dev/null || true; }
trap cleanup_lock EXIT INT TERM

AVAILABLE_KB="$(awk '/^MemAvailable:/ {print $2; exit}' /proc/meminfo)"
if [[ ! "$AVAILABLE_KB" =~ ^[0-9]+$ ]]; then
  echo "ERROR: cannot read MemAvailable from /proc/meminfo; refusing to start heavy model."
  exit 1
fi
# On memory-constrained phones, safely fall back only when the default model was
# selected implicitly. An explicitly requested model never gets silently changed.
if (( AVAILABLE_KB < MIN_AVAILABLE_KB )) && (( MODEL_EXPLICIT == 0 )) && [[ -f "$SMALL_MODEL" ]] && (( AVAILABLE_KB >= 1800000 )); then
  MODEL="$SMALL_MODEL"
  CTX_SIZE=512
  MIN_AVAILABLE_KB=1800000
  echo "SAHIBEX LOCAL MODEL: LOW-RAM FALLBACK selected $(basename "$MODEL") with context=$CTX_SIZE."
fi
if (( AVAILABLE_KB < MIN_AVAILABLE_KB )); then
  echo "SAHIBEX LOCAL MODEL: BLOCKED (available RAM ${AVAILABLE_KB} kB; need at least ${MIN_AVAILABLE_KB} kB). Close other apps and retry manually."
  exit 2
fi

if [ ! -f "$MODEL" ]; then echo "ERROR: model not found: $MODEL"; exit 1; fi
echo "Starting $(basename "$MODEL") with context=$CTX_SIZE, parallel=1, threads=2; available RAM=${AVAILABLE_KB} kB."
nohup "$SERVER" -m "$MODEL" --host 127.0.0.1 --port 8080 -c "$CTX_SIZE" --parallel 1 --threads 2 --threads-batch 2 >>"$LOG" 2>&1 </dev/null &
SERVER_PID=$!
echo "$SERVER_PID" > "$PIDFILE"
for _ in $(seq 1 35); do
  if curl -fsS --max-time 2 http://127.0.0.1:8080/health >/dev/null 2>&1; then
    if curl -fsS --max-time 2 http://127.0.0.1:8080/v1/models | grep -Fq "$(basename "$MODEL")"; then
      echo "SAHIBEX LOCAL MODEL: ONLINE (127.0.0.1:8080; PID $SERVER_PID; context=$CTX_SIZE)"
      exit 0
    fi
    echo "ERROR: port 8080 health responded but loaded model did not match expected file."
    exit 1
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "ERROR: llama-server exited during startup; see $LOG. No automatic retry was started."
    exit 1
  fi
  sleep 1
done
echo "ERROR: local model did not become healthy within 35s; no duplicate restart will be attempted. See $LOG"
exit 1
