#!/usr/bin/env bash
# Start both INN-SIGHT dev servers (api :8000, web :3000).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fuser -k 8000/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true
sleep 1

"$ROOT/.venv/bin/uvicorn" app.main:app --app-dir "$ROOT/api" --port 8000 &
# WATCHPACK_POLLING is required on WSL /mnt/c; inotify misses file changes there.
(cd "$ROOT/web" && WATCHPACK_POLLING=true npm run dev) &

echo "api  -> http://localhost:8000/health"
echo "web  -> http://localhost:3000"
wait
