# CareerPilot AI

A **local-first, privacy-respecting AI career agent** for desktop.
CareerPilot helps you discover jobs, tailor application documents with
a multi-agent AI system, prepare for interviews, and track your
applications — while keeping your career data on your own machine.

![Stack](https://img.shields.io/badge/stack-Electron%20%2B%20React%20%2B%20FastAPI-39FF14)
![Privacy](https://img.shields.io/badge/data-local--first-39FF14)

## Quick start

### Prerequisites
- Python 3.11+ and Node.js 20+
- (Optional) [Ollama](https://ollama.com) for local AI models

### 1. Start the backend

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
python -m uvicorn app.main:app --host 127.0.0.1 --port 8787
```

### 2. Start the frontend (development)

```bash
cd apps/desktop
npm install
npm run dev        # opens http://localhost:5173 (proxies /api → :8787)
```

### 3. Run the desktop app (Electron)

```bash
cd apps/desktop
npm run electron   # spawns the backend and opens the desktop window
```

The app also runs standalone in a browser (preview mode); Electron-only
features degrade gracefully.

## What it does

| Area | What works out of the box |
|------|---------------------------|
| **Onboarding** | 11-step guided profile setup with honest "unknown" states |
| **Career Profile** | Verified knowledge base: experience, education, skills, projects, credentials, preferences, writing style |
| **Job Discovery** | Manual entry, URL import (SSRF-safe), Greenhouse & Lever public boards |
| **Suitability Matching** | Structured, explainable per-dimension analysis — never a black-box score |
| **Application Studio** | 4-agent pipeline (Strategist → Drafter → Reviewer → Reviser) with quality gates |
| **Documents** | Master CV + tailored versions, 8 templates, PDF/DOCX/TXT/LaTeX export |
| **Interview Coach** | Job-specific questions, structured self-review, scored feedback |
| **Tracker** | Kanban pipeline, reminders, follow-ups, analytics |
| **Insights** | Trends computed from your real data only |
| **AI Providers** | Ollama (local) + OpenAI-compatible; **works fully offline** with the local engine |

## Honest capabilities

- **No AI provider configured?** The deterministic local engine
  implements all four agents. Drafts are template-based and
  evidence-grounded, not as fluent as LLM drafts, but fully functional.
- **Nothing is fabricated.** Facts come only from your verified
  profile. Unverified claims are flagged, never silently added.
- **Nothing is auto-submitted.** You review and approve every
  document; applications are submitted by you on the employer's site.
- **Matching is explainable.** Every score lists the dimensions,
  weights, and evidence behind it.

See [docs/capabilities.md](docs/capabilities.md) for the full
what-works / what-needs-configuration breakdown.

## Documentation

- [Getting started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [Honest capabilities](docs/capabilities.md)
- [Product rules](docs/product-rules.md)
- [Security model](docs/security.md)

## License

Proprietary. All rights reserved.
