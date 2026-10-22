import { describe, it, expect, vi, beforeEach } from "vitest";
import { api, ApiError, setStoredToken } from "./api";

describe("API client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("throws ApiError with backend detail on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: "Invalid input" }),
      })
    );
    await expect(api.get("/api/v1/jobs")).rejects.toMatchObject({
      status: 400,
      detail: "Invalid input",
    });
  });

  it("throws ApiError (not raw) so UI can show friendly text", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error("no json")),
      })
    );
    try {
      await api.get("/api/v1/jobs");
      expect.unreachable("should throw");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
    }
  });

  it("parses JSON responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 1, title: "Engineer" }),
      })
    );
    const result = await api.get<{ id: number; title: string }>("/api/v1/jobs");
    expect(result.title).toBe("Engineer");
  });

  it("sends the stored bearer token when present", async () => {
    setStoredToken("test-token");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal("fetch", fetchMock);
    await api.get("/api/v1/profile");
    const headers = fetchMock.mock.calls[0][1].headers;
    expect(headers["Authorization"]).toBe("Bearer test-token");
    setStoredToken(null);
  });

  it("omits the Authorization header when no token exists", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal("fetch", fetchMock);
    await api.get("/api/v1/profile");
    const headers = fetchMock.mock.calls[0][1].headers;
    expect(headers["Authorization"]).toBeUndefined();
  });
});
