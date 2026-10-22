/**
 * CareerPilot AI - Electron main process.
 *
 * Responsibilities:
 *  - Serve the built frontend over http://127.0.0.1 with a
 *    same-origin /api proxy to the Python backend (mirrors
 *    the Vite dev proxy), so relative API paths work in
 *    production without weakening CORS.
 *  - Spawn (or attach to) the local FastAPI backend.
 *  - Expose the per-installation API token to the renderer
 *    through a secure, minimal preload bridge.
 *
 * The backend binds to 127.0.0.1 only; the frontend server
 * also binds to 127.0.0.1 only.
 */

const { app, BrowserWindow, ipcMain, shell } = require("electron");
const path = require("node:path");
const fs = require("node:fs");
const http = require("node:http");
const { spawn } = require("node:child_process");

const isDev = process.env.NODE_ENV === "development" || !app.isPackaged;
const BACKEND_PORT = process.env.CAREERPILOT_PORT || "8787";
const FRONTEND_PORT = process.env.CAREERPILOT_FRONTEND_PORT || "4173";

let mainWindow = null;
let backendProcess = null;
let staticServer = null;

function getDataDir() {
  return path.join(app.getPath("userData"), "data");
}

function getTokenPath() {
  return path.join(getDataDir(), "api_token");
}

function getToken() {
  try {
    return fs.readFileSync(getTokenPath(), "utf8").trim();
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Static file server + /api reverse proxy (production only)
// ---------------------------------------------------------------------------

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".map": "application/json",
  ".txt": "text/plain; charset=utf-8",
};

function serveStatic(distDir) {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, `http://127.0.0.1:${FRONTEND_PORT}`);

    // Reverse-proxy API requests to the Python backend.
    if (url.pathname.startsWith("/api/")) {
      proxyToBackend(req, res, url);
      return;
    }

    // SPA fallback to index.html for non-file routes.
    let pathname = decodeURIComponent(url.pathname);
    if (pathname === "/") pathname = "/index.html";
    let filePath = path.join(distDir, pathname);
    if (!filePath.startsWith(distDir)) {
      res.writeHead(403).end("Forbidden");
      return;
    }
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      filePath = path.join(distDir, "index.html");
    }
    const ext = path.extname(filePath).toLowerCase();
    const type = MIME[ext] || "application/octet-stream";
    try {
      const data = fs.readFileSync(filePath);
      res.writeHead(200, { "Content-Type": type });
      res.end(data);
    } catch {
      res.writeHead(404).end("Not found");
    }
  });

  return new Promise((resolve) => {
    server.listen(Number(FRONTEND_PORT), "127.0.0.1", () => resolve(server));
  });
}

function proxyToBackend(req, res, url) {
  const options = {
    hostname: "127.0.0.1",
    port: BACKEND_PORT,
    path: url.pathname + url.search,
    method: req.method,
    headers: { ...req.headers, host: `127.0.0.1:${BACKEND_PORT}` },
  };
  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });
  proxyReq.on("error", () => {
    res.writeHead(502, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ detail: "Backend unavailable." }));
  });
  req.pipe(proxyReq, { end: true });
}

// ---------------------------------------------------------------------------
// Backend process
// ---------------------------------------------------------------------------

function startBackend() {
  if (backendProcess) return;
  const pythonCmd = process.env.CAREERPILOT_PYTHON || "python3";
  const backendDir = isDev
    ? path.join(__dirname, "..", "..", "..", "backend")
    : path.join(process.resourcesPath, "backend");

  const env = {
    ...process.env,
    CAREERPILOT_HOST: "127.0.0.1",
    CAREERPILOT_PORT: BACKEND_PORT,
    CAREERPILOT_DATA_DIR: getDataDir(),
  };

  backendProcess = spawn(
    pythonCmd,
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", BACKEND_PORT],
    { cwd: backendDir, env, stdio: ["ignore", "pipe", "pipe"] }
  );
  backendProcess.stderr.on("data", (d) => console.error("[backend]", d.toString()));
  backendProcess.stdout.on("data", (d) => console.log("[backend]", d.toString().trim()));
  backendProcess.on("exit", (code) => {
    console.log("Backend exited with code", code);
    backendProcess = null;
  });
}

// ---------------------------------------------------------------------------
// Window
// ---------------------------------------------------------------------------

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: "#080B09",
    title: "CareerPilot AI",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
    },
  });

  if (isDev) {
    mainWindow.loadURL("http://127.0.0.1:5173");
    mainWindow.webContents.openDevTools({ mode: "detach" });
  } else {
    mainWindow.loadURL(`http://127.0.0.1:${FRONTEND_PORT}/`);
  }

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("http")) shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

app.whenReady().then(async () => {
  fs.mkdirSync(getDataDir(), { recursive: true });

  if (!isDev) {
    const distDir = path.join(__dirname, "..", "dist");
    staticServer = await serveStatic(distDir);
    console.log(`Frontend server on http://127.0.0.1:${FRONTEND_PORT}`);
  }

  createWindow();
  startBackend();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (backendProcess) backendProcess.kill("SIGTERM");
  if (staticServer) staticServer.close();
});

// Secure IPC: expose only what the renderer needs.
ipcMain.handle("careerpilot:getApiToken", () => getToken());
ipcMain.handle("careerpilot:getVersion", () => app.getVersion());
