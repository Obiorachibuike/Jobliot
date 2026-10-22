# Honest capabilities

This document states exactly what works, what is a
simplification, and what requires configuration. We would
rather under-promise than overstate.

## Works out of the box (no AI provider, no network)

- **Onboarding** and the full career-profile editor.
- **Manual job entry** and **job URL import** (public pages
  with JSON-LD or readable HTML).
- **Greenhouse and Lever public boards** (no key required;
  depends on those companies' public APIs being reachable).
- **Structured suitability matching** with per-dimension
  evidence and explicit weights.
- **The full 4-agent document pipeline** via the deterministic
  local engine: strategy, drafting, review, and revision.
- **CV/cover-letter export** to PDF (ReportLab), DOCX, TXT,
  and LaTeX source.
- **Interview coach** with job-specific questions and
  heuristic scoring.
- **Application tracker** with kanban, reminders, follow-ups,
  and analytics.
- **Insights** computed from your stored data.
- **Data export, backup, restore, and deletion.**

## Requires configuration

- **AI-powered drafting** needs a provider: Ollama (local,
  free) or an OpenAI-compatible endpoint (may incur cost).
  Without one, the local engine runs instead.
- **Scheduled job searches** run only while the app is open
  (APScheduler in-process). There is no background service —
  a closed desktop app cannot fetch jobs. This is a deliberate
  simplicity/architecture choice.
- **More job sources** (LinkedIn, Indeed, etc.) require official
  API credentials that are not publicly available; they are
  not implemented and are not implied to work.

## Known simplifications and limitations

- **CV import is heuristic.** Extraction of name, contact,
  skills, and sections is conservative; every imported field
  is marked *uncertain* and requires your confirmation.
- **The local engine** is template- and rule-based. Drafts are
  correct and grounded but less fluent than LLM drafts.
- **Review checks** are deterministic heuristics (fabrication
  guard, keyword coverage, repetition, filler, length, ATS
  basics, tone). They catch common issues but are not a
  substitute for human review.
- **Interview evaluation** scores relevance, structure,
  evidence, and conciseness via transparent heuristics — it
  does not judge content quality the way a human would.
- **Seniority and experience** are estimates inferred from
  titles and dates.
- **PDF export** uses ReportLab (no LaTeX toolchain required).
  LaTeX *source* export is available if you have a TeX
  distribution installed.
- **Match scores** reflect the evidence in your profile; an
  incomplete profile yields "unknown" dimensions, not low
  scores.
- **No audio recording** in the interview coach yet; the
  timer is manual.

## What we never do

- Never fabricate experience, skills, metrics, or job
  availability.
- Never auto-submit an application or document.
- Never expose API keys to the frontend, logs, or source
  control.
- Never send your data anywhere unless you explicitly
  configure a cloud AI provider.
- Never present a correlation as causation.
