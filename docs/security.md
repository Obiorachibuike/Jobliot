# Security model

## Threat model

CareerPilot runs locally and handles sensitive career data.
The primary threats are:

- Unauthorized local access to the API.
- Server-side request forgery via job-URL import.
- Secret leakage (API keys, tokens).
- Prompt injection via imported job content.

## Controls

### Local API security
- The backend binds to **127.0.0.1** only.
- Every endpoint except `/api/v1/health` requires a
  per-installation bearer token stored in a `0600` file
  and compared in constant time.
- CORS is restricted to configured origins.
- Request bodies are size-limited.
- Errors are sanitized; internal details never reach the client.

### SSRF protection (URL import)
`validate_outbound_url` + `safe_fetch` enforce:
- Scheme allowlist (`http`, `https` only).
- Port allowlist (80, 443, 8000–8999 for local boards).
- Blocking of private, loopback, link-local, and cloud
  metadata IPs — **before** the request and again **after**
  DNS resolution (re-resolution check).
- Redirect re-validation.
- Response size caps and timeouts.

Imported page content is treated as **untrusted data**: it is
parsed for facts, never executed, and never allowed to
influence application behavior.

### Secrets
- AI provider API keys are stored in the OS keyring when
  available, otherwise an encrypted local file (Fernet) with a
  machine-local key.
- Keys are referenced by opaque IDs, never stored in the
  database, never logged, never returned by the API.
- The local API token is stored in a `0600` file.

### Data privacy
- Export includes every user-owned table but **excludes**
  secrets and tokens.
- Deletion is explicit and confirmed; "delete everything"
  wipes the profile data.
- Backups are local file copies with an integrity check.

## AI-specific
- Provider adapters send only the current task payload to the
  configured endpoint. Local (Ollama) models keep everything
  on-machine.
- LLM outputs are parsed into structured schemas; on any
  parse failure the pipeline falls back to the deterministic
  engine rather than trusting malformed output.
- The reviewer and fabricator guard check drafts against the
  verified profile so an LLM cannot silently invent facts.

## Limitations
- The local API token is a single shared secret per
  installation; there is no multi-user model.
- APScheduler runs in-process; scheduled tasks only run while
  the app is open.
