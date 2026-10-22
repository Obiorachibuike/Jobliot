#!/usr/bin/env bash
set -e; cd "$(dirname "$0")/.."
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r backend/requirements.txt
.venv/bin/python backend/run.py &
BACK=$!; trap "kill $BACK" EXIT
sleep 2
TOKEN=$(cat ~/.careerpilot/.api_token)
echo "Local API token: $TOKEN (Electron gets it automatically; for browser dev, paste it in Settings > General)"
cd apps/desktop && npm run electron:dev
