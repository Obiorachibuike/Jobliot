# Getting started

## Installation

CareerPilot is a desktop application with a local Python backend and
a React/Electron frontend. Everything runs on your machine.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e .
```

The backend stores data in `~/.careerpilot/` by default (SQLite).

### Frontend

```bash
cd apps/desktop
npm install
```

### Run

**Development (browser):**

```bash
# terminal 1 - backend
cd backend && python -m uvicorn app.main:app --port 8787

# terminal 2 - frontend
cd apps/desktop && npm run dev
```

Open http://localhost:5173.

**Desktop (Electron):**

```bash
cd apps/desktop
npm run electron
```

## First run

1. The app opens onboarding. Complete as much as you can — skipping
   steps only limits future recommendations, never blocks the app.
2. Add your experience, skills, and projects in **Career Profile**.
3. Discover jobs in **Discover Jobs** (import a URL or add a public
   board source).
4. Open **Application Studio**, pick a job, and generate a tailored
   CV or cover letter. Review the strategy and findings, then
   approve and export.

## Configuring AI (optional)

The app works fully offline. To enable model-powered drafting:

**Local (Ollama):**
1. Install [Ollama](https://ollama.com) and pull a model
   (e.g. `ollama pull llama3.1`).
2. Settings → AI Providers → Add provider → Ollama.
3. Test the connection.

**OpenAI-compatible API:**
1. Settings → AI Providers → Add provider → OpenAI-compatible.
2. Enter the base URL, model, and API key.
3. The key is stored in your OS credential store (or an encrypted
   local file) and never appears in the UI, logs, or source control.

## Running tests

```bash
# backend
cd backend && python -m pytest

# frontend
cd apps/desktop && npm test
```
