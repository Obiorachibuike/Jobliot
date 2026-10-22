# Architecture
- **Desktop**: Electron (contextIsolation, sandbox, no nodeIntegration, narrow preload bridge) loads React+TypeScript+Vite UI; spawns the Python backend on 127.0.0.1:8765 and passes a per-install token via IPC. Dev mode can run the same UI in a browser (Vite proxies /api).
- **Backend**: FastAPI, versioned `/api/v1` routes (see /api/docs), Pydantic validation, token middleware on every non-health route, localhost-only bind.
- **Persistence**: SQLAlchemy + SQLite (WAL, FK on) at `~/.careerpilot/careerpilot.db`; Alembic migrations (`backend/migrations`); backup/restore/export/delete-all endpoints. Models are DB-agnostic → PostgreSQL later via connection string.
- **AI layer**: `app/ai/provider.py` adapter — Ollama (local) or any OpenAI-compatible endpoint; bounded retries with backoff, timeouts, per-task model overrides, usage logging. Every AI feature has a deterministic built-in fallback so the app works fully offline.
- **Agents**: `app/services/agents.py` — Strategist (JSON strategy), Drafter (structured CV content + cover letter), Independent Reviewer (profile cross-checks: unverified skills, invented metrics, placeholders, ATS keyword gaps) with verdict gates, Revision (safe fixes only; factual fixes require the user).
- **Matching**: `app/services/matching.py` — structured weighted scoring over verified skills/experience/projects/education/preferences with full evidence breakdown. Missing data = "unknown", not mismatch.
- **Job sources**: `app/jobs/sources.py` — common adapter interface; Remotive, Greenhouse, Lever public APIs; SSRF-safe URL fetch; SHA-256 fingerprint dedup.
- **Documents**: structured content → reportlab PDF / python-docx DOCX / TXT / LaTeX source; exports validated (magic bytes) before download.
