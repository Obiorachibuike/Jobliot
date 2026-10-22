# CareerPilot AI - convenience commands

.PHONY: help backend frontend electron install install-all test test-backend test-frontend

help:
	@echo "CareerPilot AI"
	@echo "  make install-backend   - create Python venv and install deps"
	@echo "  make install-frontend  - npm install (apps/desktop)"
	@echo "  make backend           - run the FastAPI backend on :8787"
	@echo "  make frontend          - run the Vite dev server on :5173"
	@echo "  make electron          - run the Electron desktop app"
	@echo "  make test-backend      - run backend pytest suite"
	@echo "  make test-frontend     - run frontend vitest suite"
	@echo "  make build-frontend    - production build of the frontend"

install-backend:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -e .

install-frontend:
	cd apps/desktop && npm install

backend:
	cd backend && .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8787

frontend:
	cd apps/desktop && npm run dev

electron:
	cd apps/desktop && npm run electron

test-backend:
	cd backend && PYTHONPATH=. .venv/bin/python -m pytest -q

test-frontend:
	cd apps/desktop && npm test

test: test-backend test-frontend

build-frontend:
	cd apps/desktop && npm run build
