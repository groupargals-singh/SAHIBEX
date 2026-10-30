#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/SAHIBEX"
cd "$ROOT"
export SAHIBEX_MODEL_PROVIDER=local
# Prefer the 4B model when RAM allows. On a constrained phone, select the
# installed 1.7B model before launch so the API model ID matches the loaded model.
# An explicit SAHIBEX_LOCAL_MODEL_PATH always takes precedence.
if [[ -z "${SAHIBEX_LOCAL_MODEL_PATH:-}" ]]; then
  AVAILABLE_KB="$(awk '/^MemAvailable:/ {print $2; exit}' /proc/meminfo)"
  if [[ "$AVAILABLE_KB" =~ ^[0-9]+$ ]] && (( AVAILABLE_KB < 3145728 && AVAILABLE_KB >= 1800000 )) && [[ -f "$HOME/models/Qwen3-1.7B-Q4_K_M.gguf" ]]; then
    export SAHIBEX_LOCAL_MODEL_PATH="$HOME/models/Qwen3-1.7B-Q4_K_M.gguf"
    export SAHIBEX_LOCAL_CTX_SIZE=512
    export SAHIBEX_MODEL_MIN_AVAILABLE_KB=1800000
  else
    export SAHIBEX_LOCAL_MODEL_PATH="$HOME/models/Qwen3-4B-Q4_K_M.gguf"
  fi
fi
export SAHIBEX_LOCAL_LLM_MODEL="${SAHIBEX_LOCAL_LLM_MODEL:-$(basename "$SAHIBEX_LOCAL_MODEL_PATH")}"
# Use the local model as a conservative semantic fallback when keyword intent is uncertain.
# It never grants permission; the existing classifier and permission gateway remain authoritative.
export SAHIBEX_SEMANTIC_INTENT_ENABLED="${SAHIBEX_SEMANTIC_INTENT_ENABLED:-1}"
export SAHIBEX_SEARCH_BACKEND=google_news_rss
export SAHIBEX_CHILD_REGISTRY_DB="${SAHIBEX_CHILD_REGISTRY_DB:-$ROOT/data/runtime/child_instances.sqlite3}"
export SAHIBEX_CHILD_MEMORY_DB="${SAHIBEX_CHILD_MEMORY_DB:-$ROOT/data/runtime/child_memory.sqlite3}"
# Persistent ledger for isolated managed child-worker tasks (P4).
export SAHIBEX_MANAGED_WORKER_DB="${SAHIBEX_MANAGED_WORKER_DB:-$ROOT/data/runtime/managed_worker_tasks.sqlite3}"
export SAHIBEX_SELF_IMPROVEMENT_AUDIT_DB="${SAHIBEX_SELF_IMPROVEMENT_AUDIT_DB:-$ROOT/data/runtime/self_improvement_audit.sqlite3}"
export SAHIBEX_SELF_IMPROVEMENT_STATE_DB="${SAHIBEX_SELF_IMPROVEMENT_STATE_DB:-$ROOT/data/runtime/self_improvement_state.sqlite3}"
./scripts/start_local_model.sh
exec python -m app.main
