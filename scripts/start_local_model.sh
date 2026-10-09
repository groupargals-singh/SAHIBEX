#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/SAHIBEX"
MODEL="$HOME/models/Qwen3-1.7B-Q4_K_M.gguf"
SERVER="$HOME/llama.cpp/build/bin/llama-server"
LOG="$ROOT/logs/llama-server.log"
PIDFILE="$ROOT/logs/llama-server.pid"

if [ ! -x "$SERVER" ]; then echo "ERROR: llama-server not found: $SERVER"; exit 1; fi
if [ ! -f "$MODEL" ]; then echo "ERROR: model not found: $MODEL"; exit 1; fi

if curl -fsS --max-time 2 http://127.0.0.1:8080/health >/dev/null 2>&1; then
  echo "SAHIBEX LOCAL MODEL: ONLINE (127.0.0.1:8080)"
  exit 0
fi

nohup "$SERVER" -m "$MODEL" --host 127.0.0.1 --port 8080 -c 2048 --parallel 1 --threads 4 --threads-batch 4 >>"$LOG" 2>&1 &
echo $! > "$PIDFILE"

for _ in $(seq 1 30); do
  if curl -fsS --max-time 2 http://127.0.0.1:8080/health >/dev/null 2>&1; then
    echo "SAHIBEX LOCAL MODEL: ONLINE (127.0.0.1:8080)"
    exit 0
  fi
  sleep 1
done

echo "ERROR: local model did not become healthy; see $LOG"
exit 1
