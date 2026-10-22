// API client for the local CareerPilot backend.
//
// The backend binds to 127.0.0.1 and requires a per-installation
// bearer token.  In Electron the main process reads the token file
// and injects it through the preload bridge; in browser/dev mode
// the Vite proxy forwards /api and the backend may be configured
// with CAREERPILOT_API_REQUIRE_AUTH=false for local development.

const BASE = "";

class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function getToken(): Promise<string | null> {
  // Electron preload bridge (production desktop build).
  const w = window as unknown as { careerpilot?: { getApiToken?: () => Promise<string | null> } };
  if (w.careerpilot?.getApiToken) {
    try {
      return await w.careerpilot.getApiToken();
    } catch {
      return null;
    }
  }
  // Browser/dev mode: token may be stored locally for testing.
  return localStorage.getItem("careerpilot.api_token");
}

export async function setStoredToken(token: string | null) {
  if (token === null) {
    localStorage.removeItem("careerpilot.api_token");
  } else {
    localStorage.setItem("careerpilot.api_token", token);
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  headers: Record<string, string> = {}
): Promise<T> {
  const token = await getToken();
  const init: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  };
  if (body !== undefined && !(body instanceof FormData)) {
    init.body = JSON.stringify(body);
  } else if (body instanceof FormData) {
    init.body = body;
    delete (init.headers as Record<string, string>)["Content-Type"];
  }

  const response = await fetch(`${BASE}${path}`, init);
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      if (data && typeof data.detail === "string") detail = data.detail;
      else if (data && typeof data.detail === "object") {
        detail = JSON.stringify(data.detail);
      }
    } catch {
      // keep generic detail
    }
    throw new ApiError(response.status, detail);
  }
  // 204 No Content
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  del: <T>(path: string) => request<T>("DELETE", path),
  postForm: <T>(path: string, formData: FormData) =>
    request<T>("POST", path, formData),
};

export { ApiError };
