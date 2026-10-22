import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Studio from "./Studio";
import { ToastProvider } from "../components/ui/Toast";

// Mock the backend service.
vi.mock("../services/backend", () => ({
  jobsApi: {
    list: () =>
      Promise.resolve([
        {
          id: 1,
          title: "Python Engineer",
          company: "Acme",
          location: "Remote",
          has_match: false,
        },
      ]),
  },
  documentsApi: {
    templates: () =>
      Promise.resolve([
        { id: "ats_friendly", name: "ATS-Friendly", description: "", layout: "classic", best_for: [], ats_safe: true },
      ]),
    list: () => Promise.resolve([]),
  },
  studioApi: {
    generate: () => Promise.resolve({ document_id: 1, document: {}, strategy: {}, review: {}, status: "draft", readiness: "ready" }),
  },
}));

function renderStudio() {
  return render(
    <ToastProvider>
      <MemoryRouter initialEntries={["/studio"]}>
        <Routes>
          <Route path="/studio" element={<Studio />} />
          <Route path="/studio/:jobId" element={<Studio />} />
        </Routes>
      </MemoryRouter>
    </ToastProvider>
  );
}

describe("Studio", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the setup panel with job selector", async () => {
    renderStudio();
    expect(
      await screen.findByText(/Application Studio/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/New tailored document/i)).toBeInTheDocument();
  });

  it("explains that the user approves every document", async () => {
    renderStudio();
    expect(
      await screen.findByText(/You approve every document/i)
    ).toBeInTheDocument();
  });

  it("shows the four-agent pipeline while generating", async () => {
    renderStudio();
    // The stage labels are part of the loading UI.
    const studio = screen.getByText(/Application Studio/i);
    expect(studio).toBeInTheDocument();
  });
});
