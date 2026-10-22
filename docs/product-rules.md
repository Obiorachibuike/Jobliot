# Product rules

These rules are binding for every feature.

1. **Never fabricate.** No invented experience, skills,
   metrics, job availability, or statistics. Uncertain data is
   labeled uncertain.
2. **Never expose secrets.** API keys live in the OS credential
   store (or encrypted local file), never in the frontend
   bundle, logs, source control, or ordinary database records.
3. **Works offline.** Every feature functions with no AI
   provider configured, via the deterministic local engine.
4. **Explainable matching.** Every suitability score lists its
   dimensions, weights, and evidence. No black boxes.
5. **Human-in-the-loop.** Documents require explicit approval.
   Applications are never auto-submitted. Destructive actions
   require confirmation.
6. **Honest documentation.** State what works, what is a
   simplification, and what needs configuration.
7. **No purple.** The palette is neon green (#39FF14), charcoal,
   and white. Status is never conveyed by color alone.
8. **SSRF protection.** URL imports are validated and fetched
   through a allowlist-based, private-IP-blocking client.
9. **Local-first.** Data stays on the machine by default.
10. **Simple architecture.** SQLite, APScheduler, no Redis or
    Celery.
