# Deployment / Packaging

## Run in development
```bash
# terminal 1 — backend
python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
.venv/bin/python backend/run.py        # listens on 127.0.0.1:8765 only
# terminal 2 — desktop UI
cd apps/desktop && npm install && npm run electron:dev
```
Or `./scripts/dev.sh` (starts both). Browser-only dev: `npm run dev` then paste the token from `~/.careerpilot/.api_token` into Settings → General.

## Package installers (must run on the target OS)
```bash
cd apps/desktop
npm install
npm run package   # vite build + electron-builder
# Windows (on Windows) -> release/*.exe (NSIS)   macOS (on Mac) -> release/*.dmg   Linux -> AppImage/.deb
```
Notes: the packaged app bundles the Python backend source and spawns `python3`/`python` (set `CAREERPILOT_PYTHON` to override). For a fully self-contained binary, freeze the backend with PyInstaller and point the spawn path at it — documented as a next step, not required for local use. Electron binary download requires network access to GitHub at install time. Code signing/notarization are not configured; unsigned builds trigger OS "unknown developer" warnings.

## Troubleshooting
- **UI says backend offline** → start backend, check `curl http://127.0.0.1:8765/api/v1/health`, verify token.
- **Port in use** → set `CAREERPILOT_PORT` and update `VITE_API_BASE`/proxy.
- **PDF fonts** → exports use reportlab's built-in Helvetica, so no system fonts needed. LaTeX export is source-only unless you compile it yourself.
- **Ollama test fails** → ensure Ollama is running (`ollama serve`) and the model is pulled (`ollama pull llama3.1`).
