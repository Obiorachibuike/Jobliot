#!/usr/bin/env bash
# Start both the backend and the frontend dev server.
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Starting CareerPilot backend on http://127.0.0.1:8787"
cd "$ROOT/backend"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -e .
else
  . .venv/bin/activate
fi
python -m uvicorn app.main:app --host 127.0.0.1 --port 8787 &
BACKEND_PID=$!

echo "==> Starting frontend dev server on http://localhost:5173"
cd "$ROOT/apps/desktop"
npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
