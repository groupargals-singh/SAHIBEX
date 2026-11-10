#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/SAHIBEX"
PROJECT_ROOT="$HOME/SAHIBEX"
PID_FILE="logs/media_bridge.pid"
LOG_FILE="logs/media_bridge.log"
TOKEN_FILE="data/android_companion_media_token"
mkdir -p logs data
umask 077

bridge_pid_matches() {
  local pid="$1" cmd cwd
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  [[ -r "/proc/$pid/cmdline" ]] || return 1
  cmd="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
  cwd="$(readlink "/proc/$pid/cwd" 2>/dev/null || true)"
  [[ "$cmd" == *"tools.android_companion_media_server"* ]] || return 1
  [[ "$cwd" == "$PROJECT_ROOT" ]] || return 1
}

runtime_smoke() {
  local token session tmp status
  [[ -s "$TOKEN_FILE" ]] || { echo "Media token file missing; pairing is not configured." >&2; return 1; }
  token="$(cat "$TOKEN_FILE")"
  session="$(curl --noproxy '*' -fsS --max-time 4 -H "Authorization: Bearer $token" http://127.0.0.1:38742/session)" || {
    echo "Media bridge authentication/session check failed." >&2; return 1;
  }
  printf '%s' "$session" | "$PROJECT_ROOT/.venv/bin/python" -c 'import json,sys; d=json.load(sys.stdin); assert d.get("authenticated") is True'
  tmp="$(mktemp "$PROJECT_ROOT/data/.media-tts-smoke.XXXXXX.wav")"
  status="$(printf '%s' '{"text":"SAHIBEX local voice check.","language":"en"}' | curl --noproxy '*' -sS --max-time 75 -o "$tmp" -w '%{http_code}' -H "Authorization: Bearer $token" -H 'Content-Type: application/json' --data-binary @- http://127.0.0.1:38742/synthesize || true)"
  if [[ "$status" != "200" ]]; then
    echo "Media bridge TTS smoke failed (HTTP $status); no cloud fallback was attempted." >&2
    rm -f "$tmp"
    return 1
  fi
  "$PROJECT_ROOT/.venv/bin/python" - "$tmp" <<'PY'
import pathlib, sys, wave
p = pathlib.Path(sys.argv[1])
with wave.open(str(p), "rb") as wav:
    assert wav.getnchannels() in (1, 2)
    assert wav.getsampwidth() in (1, 2, 3, 4)
    assert 8000 <= wav.getframerate() <= 48000
    assert wav.getnframes() > 0
assert p.read_bytes().startswith(b"RIFF")
PY
  rm -f "$tmp"
}

if curl --noproxy '*' -fsS --max-time 2 http://127.0.0.1:38742/health >/dev/null 2>&1; then
  pid=""
  [[ -f "$PID_FILE" ]] && pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if bridge_pid_matches "$pid"; then
    if runtime_smoke; then
      echo "SAHIBEX media bridge already healthy, PID identity verified, authenticated TTS smoke PASS."
      exit 0
    fi
    echo "Bridge PID is identified but runtime verification failed. Use the guarded stop script before restarting." >&2
    exit 1
  fi
  echo "Port 38742 responds, but its PID file does not identify the expected SAHIBEX process." >&2
  echo "Refusing to report healthy or kill an unrelated/reused PID. Inspect the listener first." >&2
  exit 1
fi

# Never kill a PID merely because it appears in the file. Require both the
# exact module command and the SAHIBEX project working directory.
if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if bridge_pid_matches "$old_pid"; then
    kill -TERM "$old_pid"
    for _ in $(seq 1 10); do
      kill -0 "$old_pid" 2>/dev/null || break
      sleep 0.5
    done
    if kill -0 "$old_pid" 2>/dev/null; then
      echo "Verified old media bridge PID $old_pid did not stop; refusing duplicate start." >&2
      exit 1
    fi
  elif [[ "$old_pid" =~ ^[0-9]+$ ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "Stale PID file points to an unrelated live process ($old_pid); it will not be killed."
  fi
fi

source "$PROJECT_ROOT/.venv/bin/activate"
export SAHIBEX_MODEL_PROVIDER="${SAHIBEX_MODEL_PROVIDER:-local}"
export SAHIBEX_SEARCH_BACKEND="${SAHIBEX_SEARCH_BACKEND:-google_news_rss}"
export SAHIBEX_SELF_IMPROVEMENT_AUDIT_DB="${SAHIBEX_SELF_IMPROVEMENT_AUDIT_DB:-$PROJECT_ROOT/data/runtime/self_improvement_audit.sqlite3}"
export SAHIBEX_SELF_IMPROVEMENT_STATE_DB="${SAHIBEX_SELF_IMPROVEMENT_STATE_DB:-$PROJECT_ROOT/data/runtime/self_improvement_state.sqlite3}"
nohup "$PROJECT_ROOT/.venv/bin/python" -u -m tools.android_companion_media_server >>"$LOG_FILE" 2>&1 &
new_pid=$!
printf '%s\n' "$new_pid" > "$PID_FILE"

for _ in $(seq 1 20); do
  if curl --noproxy '*' -fsS --max-time 1 http://127.0.0.1:38742/health >/dev/null 2>&1; then
    if bridge_pid_matches "$new_pid" && runtime_smoke; then
      echo "SAHIBEX MEDIA BRIDGE: ONLINE (PID $new_pid; project .venv; authenticated TTS smoke PASS)"
      exit 0
    fi
    echo "SAHIBEX media bridge responded but process/runtime verification failed." >&2
    if bridge_pid_matches "$new_pid"; then kill -TERM "$new_pid" 2>/dev/null || true; fi
    exit 1
  fi
  sleep 1
done

echo "SAHIBEX MEDIA BRIDGE: FAILED TO START; inspect $LOG_FILE" >&2
if bridge_pid_matches "$new_pid"; then kill -TERM "$new_pid" 2>/dev/null || true; fi
exit 1
