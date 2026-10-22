import { createBrowserRouter, Navigate } from "react-router-dom";
import AppShell from "./layouts/AppShell";
import Dashboard from "./pages/Dashboard";
import Onboarding from "./pages/Onboarding";
import DiscoverJobs from "./pages/DiscoverJobs";
import JobDetails from "./pages/JobDetails";
import Studio from "./pages/Studio";
import CareerProfile from "./pages/CareerProfile";
import MasterCV from "./pages/MasterCV";
import DocumentsLibrary from "./pages/DocumentsLibrary";
import InterviewCoach from "./pages/InterviewCoach";
import ApplicationTracker from "./pages/ApplicationTracker";
import CareerInsights from "./pages/CareerInsights";
import SettingsPage from "./pages/Settings";
import AiProvidersPage from "./pages/AiProviders";
import PrivacyPage from "./pages/Privacy";

export const router = createBrowserRouter([
  {
    path: "/onboarding",
    element: <Onboarding />,
  },
  {
    element: <AppShell />,
    children: [
      { path: "/", element: <Dashboard /> },
      { path: "/jobs", element: <DiscoverJobs /> },
      { path: "/jobs/:id", element: <JobDetails /> },
      { path: "/studio", element: <Studio /> },
      { path: "/studio/:jobId", element: <Studio /> },
      { path: "/profile", element: <CareerProfile /> },
      { path: "/profile/master-cv", element: <MasterCV /> },
      { path: "/documents", element: <DocumentsLibrary /> },
      { path: "/interviews", element: <InterviewCoach /> },
      { path: "/applications", element: <ApplicationTracker /> },
      { path: "/insights", element: <CareerInsights /> },
      { path: "/settings", element: <SettingsPage /> },
      { path: "/settings/ai", element: <AiProvidersPage /> },
      { path: "/settings/privacy", element: <PrivacyPage /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
