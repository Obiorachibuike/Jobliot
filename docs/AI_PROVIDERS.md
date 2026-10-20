# AI Providers
1. **None (default)** — deterministic built-in strategy/drafting/review. Fully offline, $0. Documents are assembled from verified profile data.
2. **Ollama** — install Ollama, `ollama pull llama3.1`, set provider=Ollama, model=llama3.1, endpoint=http://localhost:11434. Test with "Test connection". Data never leaves the machine.
3. **OpenAI-compatible** — set endpoint + model + API key (stored in OS keyring). Works with OpenAI and compatible gateways. Profile/job text is sent for generation — the UI discloses this.
Controls: temperature, max tokens, timeout, bounded retries with exponential backoff, per-task model overrides (strategy/drafting), usage history with rough token estimates (chars/4; exact cost = provider dashboard). Failures fall back to built-in generation and are surfaced, never hidden.
