#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/SAHIBEX"
cd "$ROOT"
export SAHIBEX_MODEL_PROVIDER=local
export SAHIBEX_SEARCH_BACKEND=duckduckgo_html
./scripts/start_local_model.sh
exec python -m app.main
