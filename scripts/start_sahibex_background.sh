#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/SAHIBEX"
cd "$ROOT"
mkdir -p logs
if pgrep -f 'scripts/sahibex_supervisor.sh' >/dev/null 2>&1; then
  echo "SAHIBEX SUPERVISOR: ALREADY RUNNING"
  exit 0
fi
nohup ./scripts/sahibex_supervisor.sh >> logs/supervisor.log 2>&1 &
echo $! > logs/supervisor.pid
sleep 2
./scripts/sahibex_health.sh
printf '%s\n' 'SAHIBEX SUPERVISOR: ONLINE'
