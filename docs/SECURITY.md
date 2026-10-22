# Security
- Electron: contextIsolation + sandbox on, nodeIntegration off, navigation restricted, external links via OS browser, preload exposes only token + openExternal.
- Backend: 127.0.0.1 only, per-install token (`x-careerpilot-token`, file mode 0600) so random web pages cannot call the local API; CORS allowlist; Pydantic validation; sanitized errors; 10MB upload / 2MB page-fetch limits.
- SSRF: URL import allows only http/https on ports 80/443, resolves and rejects private/loopback/link-local/metadata IPs, revalidates redirect targets, no content execution. Job text is treated as untrusted data in every AI prompt.
- Secrets: AI keys go to OS keyring (keyring lib) when available, else a 0600 file in the data dir — never DB, frontend bundle, logs, or git (`.gitignore` covers `.env`, tokens, DBs).
- Privacy: local-first, no telemetry. Cloud AI only when user configures it (disclosed in UI). Destructive actions require confirmation; delete-all requires typing DELETE.
