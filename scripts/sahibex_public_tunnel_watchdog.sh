#!/data/data/com.termux/files/usr/bin/bash
set -uo pipefail
ROOT="$HOME/SAHIBEX"
cd "$ROOT" || exit 1
mkdir -p logs
PID_FILE="logs/public_tunnel.pid"
URL_FILE="logs/public_tunnel.url"
LOG_FILE="logs/public_tunnel.log"
LOCK_FILE="logs/public_tunnel_watchdog.pid"
ONCE=0
[[ "${1:-}" == "--once" ]] && ONCE=1

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*" >> logs/public_tunnel_watchdog.log; }
get_url() {
  if [[ -s "$URL_FILE" ]]; then
    tr -d '\r\n ' < "$URL_FILE"
    return
  fi
  grep -Eo 'https://[A-Za-z0-9.-]+\.lhr\.life' "$LOG_FILE" 2>/dev/null | tail -n 1 || true
}
valid_ssh_pid() {
  local p="$1" cmd
  [[ "$p" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$p" 2>/dev/null || return 1
  cmd="$(ps -p "$p" -o args= 2>/dev/null || true)"
  [[ "$cmd" == *"ssh"* && "$cmd" == *"localhost.run"* ]]
}
health_ok() {
  local url="$1" code
  [[ "$url" =~ ^https://[A-Za-z0-9.-]+\.lhr\.life$ ]] || return 1
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 7 "$url/health" 2>/dev/null || true)"
  [[ "$code" == "200" ]]
}
start_tunnel() {
  local attempt url
  # Only stop a process we can positively identify from our PID file.
  if [[ -f "$PID_FILE" ]]; then
    local old_pid
    old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if valid_ssh_pid "$old_pid"; then
      kill "$old_pid" 2>/dev/null || true
      sleep 1
      kill -0 "$old_pid" 2>/dev/null && kill -TERM "$old_pid" 2>/dev/null || true
    fi
  fi
  : > "$LOG_FILE"
  rm -f "$URL_FILE"
  nohup ssh -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -o ConnectTimeout=15 -R 80:127.0.0.1:38742 nokey@localhost.run >> "$LOG_FILE" 2>&1 </dev/null &
  echo "$!" > "$PID_FILE"
  for attempt in $(seq 1 30); do
    sleep 1
    if ! kill -0 "$(cat "$PID_FILE" 2>/dev/null || echo 0)" 2>/dev/null; then
      log "SSH tunnel process exited while starting; check $LOG_FILE"
      return 1
    fi
    url="$(grep -Eo 'https://[A-Za-z0-9.-]+\.lhr\.life' "$LOG_FILE" 2>/dev/null | tail -n 1 || true)"
    if [[ -n "$url" ]]; then
      printf '%s\n' "$url" > "$URL_FILE"
      if health_ok "$url"; then
        log "Tunnel connected and public health passed: $url"
        return 0
      fi
    fi
  done
  log "Tunnel URL/health did not become ready within 30 seconds"
  return 1
}
ensure_tunnel() {
  local pid url
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  url="$(get_url)"
  if valid_ssh_pid "$pid" && [[ -n "$url" ]] && health_ok "$url"; then
    printf '%s\n' "$url" > "$URL_FILE"
    return 0
  fi
  log "Tunnel missing or unhealthy; attempting recovery"
  start_tunnel
}

if [[ "$ONCE" -eq 1 ]]; then
  ensure_tunnel
  exit $?
fi

# Prevent duplicate watchdogs. The background starter owns this PID file.
if [[ -f "$LOCK_FILE" ]]; then
  existing="$(cat "$LOCK_FILE" 2>/dev/null || true)"
  if [[ "$existing" =~ ^[0-9]+$ ]] && kill -0 "$existing" 2>/dev/null && [[ "$existing" != "$$" ]]; then
    cmd="$(ps -p "$existing" -o args= 2>/dev/null || true)"
    if [[ "$cmd" == *"sahibex_public_tunnel_watchdog.sh"* ]]; then
      log "Watchdog already running as PID $existing"
      exit 0
    fi
  fi
fi
echo "$$" > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT INT TERM
while true; do
  ensure_tunnel || true
  sleep 30
done
