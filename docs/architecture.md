# Architecture

## Overview

```
┌─────────────────────────────────────────────┐
│  Electron shell (apps/desktop/electron)     │
│  - window, backend process, token bridge    │
├─────────────────────────────────────────────┤
│  React + TypeScript + Vite + Tailwind       │
│  - 14 pages, Zustand stores, lucide icons   │
├─────────────────────────────────────────────┤
│  FastAPI backend (backend/app)              │
│  - REST API, auth via per-install token     │
│  - matching engine, multi-agent studio      │
│  - job adapters, document renderers         │
├─────────────────────────────────────────────┤
│  SQLite (WAL) + Alembic migrations          │
│  ~/.careerpilot/careerpilot.db              │
└─────────────────────────────────────────────┘
```

## Backend structure

```
backend/app/
├── api/            FastAPI routers (versioned /api/v1)
├── core/           config, database, security (SSRF, tokens)
├── models/         SQLAlchemy ORM models
├── schemas/        Pydantic request/response schemas
├── services/
│   ├── agents/     Strategist, Drafter, Reviewer, Reviser
│   │               (each has an AI path + a local engine)
│   ├── ai/         provider adapters (Ollama, OpenAI-compatible)
│   ├── jobs/       source adapters (manual, URL, Greenhouse, Lever)
│   ├── documents/  templates + renderers (PDF/DOCX/TXT/LaTeX)
│   └── tasks/      background task manager + APScheduler
└── utils/          text, format, validation helpers
```

## The four agents

The Application Studio runs four distinct stages, each a separate
call with its own prompt and structured output:

1. **Strategist** — selects verified evidence, positioning,
   keyword targets, and flags gaps.
2. **Drafter** — writes the CV/cover letter from the strategy.
3. **Reviewer** — independently checks the draft (factual accuracy,
   relevance, ATS, tone, grammar) and returns findings.
4. **Reviser** — applies safe, deterministic fixes; escalates
   anything that would require inventing facts.

A document can only reach `ready_for_approval` when no **critical**
findings remain unresolved. Approval is always manual.

### Local vs. AI

When no provider is configured, every agent runs its deterministic
local implementation. When a provider is configured, each stage
*tries* the LLM and falls back to the local engine on any failure,
so the pipeline never hard-depends on the network.

## Matching engine

Matching is **not** an LLM judgment. It is a weighted, per-dimension
comparison of structured data:

- required/preferred skills (normalized + alias-aware)
- experience years, education level, seniority
- certifications, projects, portfolio
- location, employment type, salary compatibility

Unknown dimensions (missing data) are **excluded** from the weighted
average — missing data is never treated as a deficiency. Every
dimension carries its evidence so the user can see exactly why.

## Job sources

| Source | Auth | Notes |
|--------|------|-------|
| Manual entry | none | Always available |
| URL import | none | SSRF-safe fetch + JSON-LD/HTML extraction |
| Greenhouse | none | Public board JSON API |
| Lever | none | Public postings JSON API |
| LinkedIn, Indeed, ... | — | Not supported without official API credentials; documented as a limitation |

## Data model (key entities)

UserProfile · WorkExperience · Education · Skill · Project ·
Certification · Achievement · CareerPreference · WritingStyleProfile ·
MasterCV · CVVersion · Document · DocumentVersion · JobSource ·
JobListing · JobMatch · JobSearch · Application · ApplicationEvent ·
InterviewSession · InterviewQuestion · InterviewAnswer · Reminder ·
BackgroundTask · AIProviderConfiguration · AIUsageRecord ·
Notification · AppSetting

Every fact carries a `verification_status`
(`user_confirmed`, `imported_pending`, `extracted`, `ai_suggested`,
`unverified`, `outdated`) and a `provenance` tag.

## Security

- Backend binds to **127.0.0.1** only.
- Per-installation bearer token (except `/health`).
- CORS restricted to configured origins.
- Request-size limits; sanitized error messages.
- SSRF protection on URL import: scheme/port allowlist, private /
  loopback / link-local / metadata IP blocking, DNS re-resolution,
  redirect re-validation, size caps, timeouts.
- API keys stored in the OS credential store (or encrypted local
  file fallback); never in the database, logs, or frontend bundle.

See [security.md](security.md).
