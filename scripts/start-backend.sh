#!/usr/bin/env bash
# Start the CareerPilot backend.
set -e
cd "$(dirname "$0")/../backend"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv && . .venv/bin/activate && pip install -e .
else
  . .venv/bin/activate
fi
exec python -m uvicorn app.main:app --host 127.0.0.1 --port 8787
