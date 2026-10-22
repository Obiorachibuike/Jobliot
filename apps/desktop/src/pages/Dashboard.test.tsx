import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "./Dashboard";
import { ToastProvider } from "../components/ui/Toast";

// Mock the backend service module.
vi.mock("../services/backend", () => ({
  profileApi: {
    onboardingState: () =>
      Promise.resolve({
        profile_exists: true,
        onboarding_completed: true,
        onboarding_step: 11,
        completed_steps: [1, 2, 3],
        has_profile_data: true,
        objectives: [],
      }),
  },
  applicationsApi: {
    list: () => Promise.resolve([]),
    reminders: () => Promise.resolve([]),
  },
  jobsApi: { list: () => Promise.resolve([]) },
  insightsApi: {
    get: () =>
      Promise.resolve({
        generated_at: "2026-01-01",
        insights: [
          {
            id: "skill-demand",
            title: "Python is in demand",
            description: "Python appears in 5 listings.",
            kind: "trend",
            how_calculated: "Counted per listing.",
          },
        ],
        stats: { applications: 0, interviews: 0, strong_matches: 0 },
      }),
  },
  notificationsApi: { list: () => Promise.resolve([]) },
  tasksApi: { list: () => Promise.resolve([]), stats: () => Promise.resolve({}) },
  aiApi: { providers: () => Promise.resolve([]) },
}));

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <ToastProvider>
      <MemoryRouter>{ui}</MemoryRouter>
    </ToastProvider>
  );
}

describe("Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the greeting and KPI section", async () => {
    renderWithProviders(<Dashboard />);
    expect(
      await screen.findByText(/Good (morning|afternoon|evening)/i)
    ).toBeInTheDocument();
  });

  it("shows the empty-state CTA when there are no jobs", async () => {
    renderWithProviders(<Dashboard />);
    const heading = await screen.findByText(/No jobs yet/i);
    expect(heading).toBeInTheDocument();
  });

  it("renders the AI status panel", async () => {
    renderWithProviders(<Dashboard />);
    expect(await screen.findByText(/AI status/i)).toBeInTheDocument();
    expect(
      await screen.findByText(/deterministic local engine handles/i)
    ).toBeInTheDocument();
  });
});
