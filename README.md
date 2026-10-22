# CareerPilot AI
**Your Career. Your Strategy. Your Next Opportunity.**

A privacy-conscious, local-first desktop career agent: guided onboarding → verified career profile → job discovery → explainable fit scoring → strategist/drafter/reviewer document pipeline → interview coaching → application tracking. Brand: neon green `#39FF14` on midnight black (dark) and deep green on clean white (light). No purple anywhere.

## Quick start
```bash
# 1) Backend
python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
.venv/bin/python backend/run.py            # http://127.0.0.1:8765  (API docs: /api/docs)
# 2) Desktop app
cd apps/desktop && npm install && npm run electron:dev
# Browser-only dev: npm run dev, then paste ~/.careerpilot/.api_token in Settings → General
# One-command: ./scripts/dev.sh
```

## Tests
```bash
.venv/bin/python -m pytest backend/tests -q     # 13 backend tests
cd apps/desktop && npm test && npm run build    # 3 frontend tests + production build
```

## Features
11-step onboarding with CV import (PDF/DOCX/TXT, approve-before-save) · verified career knowledge base with provenance statuses · live job sources (Remotive/Greenhouse/Lever public APIs) + SSRF-safe URL import + manual entry · explainable structured matching · Application Studio with separate Strategist/Drafter/Independent Reviewer/Revision stages and quality gates · 8 CV templates · PDF/DOCX/TXT/LaTeX exports (validated) · mock Interview Coach · Kanban/table/calendar tracker with reminders · data-driven Insights · Ollama + OpenAI-compatible providers with offline built-in fallback · backup/restore/export/delete · light/dark/system themes.

Data: `~/.careerpilot/careerpilot.db` (SQLite). Packaging: see `DEPLOYMENT.md`. Architecture/security/providers/sources: `docs/`.

## Honest limitations
Live job APIs need internet and were code-verified + gracefully error-handled; egress-restricted sandboxes can't reach them. LinkedIn/Indeed are not scraped (ToS) — paste those descriptions manually. Scheduled searches need the app open. Packaged builds spawn system Python (PyInstaller freeze is a documented next step). Reviewer checks are evidence-based heuristics — always read documents yourself before approving. CareerPilot never applies on your behalf and never fabricates qualifications.
