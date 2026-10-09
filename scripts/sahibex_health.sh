#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/SAHIBEX"
cd "$ROOT"
export SAHIBEX_MODEL_PROVIDER=local
export SAHIBEX_SEARCH_BACKEND=duckduckgo_html

if curl -fsS --max-time 2 http://127.0.0.1:8080/health >/dev/null 2>&1; then
  echo "LOCAL MODEL: ONLINE"
else
  echo "LOCAL MODEL: OFFLINE"
  exit 1
fi

PYTHONPATH=. python - <<'PY'
from core.research.runtime_providers import build_default_research_acquisition_engine
from app.config import settings
_, status = build_default_research_acquisition_engine(project_root=settings.project_root)
print('WEB SEARCH:', 'ACTIVE' if status.search_backend else 'NOT CONFIGURED')
print('ACTIVE PROVIDERS:', ', '.join(status.providers))
PY

MEDIA_PID_FILE="logs/media_bridge.pid"
if curl -fsS --max-time 2 http://127.0.0.1:38742/health >/dev/null 2>&1; then
  echo "ANDROID VOICE BRIDGE: HTTP HEALTHY"
else
  echo "ANDROID VOICE BRIDGE: HTTP OFFLINE"
  if [ -f "$MEDIA_PID_FILE" ]; then
    MEDIA_PID="$(cat "$MEDIA_PID_FILE" 2>/dev/null || true)"
    if [ -n "$MEDIA_PID" ] && kill -0 "$MEDIA_PID" 2>/dev/null; then
      echo "STALE/UNHEALTHY BRIDGE PID FILE: $MEDIA_PID"
    fi
  fi
fi
