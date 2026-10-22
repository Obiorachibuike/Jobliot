// Typed API service functions for each backend resource.

import { api } from "./api";
import type {
  AIProvider,
  AIUsageRecord,
  Achievement,
  AppSettings,
  Application,
  ApplicationEvent,
  ApplicationStatus,
  BackgroundTask,
  CareerDocument,
  CareerPreference,
  Certification,
  CVImportResult,
  DocTemplate as DocumentTemplate,
  DocumentVersion,
  Education,
  ExportResult,
  HealthInfo,
  Insight,
  InsightsResponse,
  InterviewAnswer,
  InterviewSession,
  JobListing,
  JobSearch,
  JobSource,
  MatchCategory,
  MatchReport,
  MatchWeights,
  MasterCV,
  Notification,
  Project,
  ProviderTestResult,
  Reminder,
  ReviewResult,
  Skill,
  Strategy,
  UserProfile,
  WritingStyleProfile,
  WorkExperience,
} from "../types/api";

export type { MatchReport, MatchCategory, MasterCV, DocumentTemplate };

// ------------------------------- health / profile
export const healthApi = {
  get: () => api.get<HealthInfo>("/api/v1/health"),
};

export const profileApi = {
  get: () => api.get<UserProfile>("/api/v1/profile"),
  update: (data: Partial<UserProfile>) =>
    api.patch<UserProfile>("/api/v1/profile", data),
  onboardingState: () => api.get<import("../types/api").OnboardingState>("/api/v1/onboarding/state"),
  saveStep: (step: number, data: Record<string, unknown>) =>
    api.post("/api/v1/onboarding/step", { step, data }),
  complete: () => api.post("/api/v1/onboarding/complete", {}),
};

// ------------------------------- profile entities
const entityEndpoints = {
  experience: "/api/v1/experience",
  education: "/api/v1/education",
  skills: "/api/v1/skills",
  projects: "/api/v1/projects",
  certifications: "/api/v1/certifications",
  achievements: "/api/v1/achievements",
} as const;

type Entity =
  | WorkExperience
  | Education
  | Skill
  | Project
  | Certification
  | Achievement;

function entityService<T extends Entity>(key: keyof typeof entityEndpoints) {
  const base = entityEndpoints[key];
  return {
    list: () => api.get<T[]>(base),
    create: (payload: Record<string, unknown>) => api.post<T>(base, payload),
    update: (id: number, payload: Record<string, unknown>) =>
      api.patch<T>(`${base}/${id}`, payload),
    remove: (id: number) => api.del(`${base}/${id}`),
  };
}

export const experienceApi = entityService<WorkExperience>("experience");
export const educationApi = entityService<Education>("education");
export const skillsApi = entityService<Skill>("skills");
export const projectsApi = entityService<Project>("projects");
export const certificationsApi = entityService<Certification>("certifications");
export const achievementsApi = entityService<Achievement>("achievements");

export const preferencesApi = {
  get: () => api.get<CareerPreference | null>("/api/v1/preferences"),
  upsert: (data: Partial<CareerPreference>) =>
    api.put<CareerPreference>("/api/v1/preferences", data),
};

export const writingStyleApi = {
  get: () => api.get<WritingStyleProfile | null>("/api/v1/writing-style"),
  upsert: (data: Partial<WritingStyleProfile>) =>
    api.put<WritingStyleProfile>("/api/v1/writing-style", data),
};

export const cvImportApi = {
  importFile: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.postForm<CVImportResult>("/api/v1/cv-import", formData);
  },
  confirm: (approved: Record<string, unknown>) =>
    api.post("/api/v1/cv-import/confirm", { approved }),
};

// ------------------------------- jobs
export const jobsApi = {
  list: (params?: Record<string, string | number | undefined>) => {
    const query = new URLSearchParams();
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v !== undefined && v !== "") query.set(k, String(v));
    });
    const qs = query.toString();
    return api.get<JobListing[]>(`/api/v1/jobs${qs ? `?${qs}` : ""}`);
  },
  createManual: (payload: Record<string, unknown>) =>
    api.post<JobListing>("/api/v1/jobs/manual", payload),
  importUrl: (url: string) =>
    api.post<{ ok: boolean; extracted?: Record<string, unknown> | null; error?: string | null; partial?: boolean }>(
      "/api/v1/jobs/import-url",
      { url }
    ),
  get: (id: number) => api.get<JobListing>(`/api/v1/jobs/${id}`),
  remove: (id: number) => api.del(`/api/v1/jobs/${id}`),
  verify: (id: number) => api.post(`/api/v1/jobs/${id}/verify`),
  match: (id: number) => api.post<MatchReport>(`/api/v1/jobs/${id}/match`),
  sources: () => api.get<JobSource[]>("/api/v1/jobs/sources"),
  availableSourceTypes: () =>
    api.get<Record<string, { search: boolean; url_import: boolean; requires_key: boolean }>>("/api/v1/jobs/sources/available"),
  createSource: (payload: Record<string, unknown>) =>
    api.post<JobSource>("/api/v1/jobs/sources", payload),
  deleteSource: (id: number) => api.del(`/api/v1/jobs/sources/${id}`),
  testSource: (id: number) => api.post(`/api/v1/jobs/sources/${id}/health`),
  discover: (filters?: Record<string, unknown>) =>
    api.post<{ discovered: number; errors: string[] }>("/api/v1/jobs/discover", filters || {}),
  searches: () => api.get<JobSearch[]>("/api/v1/jobs/searches"),
  createSearch: (payload: Record<string, unknown>) =>
    api.post<JobSearch>("/api/v1/jobs/searches", payload),
  deleteSearch: (id: number) => api.del(`/api/v1/jobs/searches/${id}`),
};

// ------------------------------- documents
export const documentsApi = {
  templates: () => api.get<DocumentTemplate[]>("/api/v1/documents/templates"),
  list: (kind?: string) =>
    api.get<CareerDocument[]>(`/api/v1/documents${kind ? `?kind=${kind}` : ""}`),
  get: (id: number) => api.get<CareerDocument>(`/api/v1/documents/${id}`),
  update: (id: number, payload: Record<string, unknown>) =>
    api.patch<CareerDocument>(`/api/v1/documents/${id}`, payload),
  remove: (id: number) => api.del(`/api/v1/documents/${id}`),
  versions: (id: number) =>
    api.get<DocumentVersion[]>(`/api/v1/documents/${id}/versions`),
  approve: (id: number) => api.post(`/api/v1/documents/${id}/approve`),
  setStatus: (id: number, status: string) =>
    api.post(`/api/v1/documents/${id}/status?status=${encodeURIComponent(status)}`),
  exportDocument: (id: number, format: string) =>
    api.post<ExportResult>(`/api/v1/documents/${id}/export`, { format }),
  masterCv: () => api.get<MasterCV>("/api/v1/documents/master-cv"),
  updateMasterCv: (content: unknown) =>
    api.put<MasterCV>("/api/v1/documents/master-cv", content),
  masterCvVersions: () =>
    api.get<DocumentVersion[]>("/api/v1/documents/master-cv/versions"),
  restoreMasterCvVersion: (versionId: number) =>
    api.post<MasterCV>(`/api/v1/documents/master-cv/versions/${versionId}/restore`),
};

// ------------------------------- studio (multi-agent workflow)
export const studioApi = {
  generate: (payload: {
    job_listing_id: number;
    kind: string;
    template_id: string;
    cover_letter_length?: string;
  }) =>
    api.post<{
      document_id: number;
      document: CareerDocument;
      strategy: Strategy;
      review: ReviewResult;
      status: string;
      readiness: string;
    }>("/api/v1/studio/generate", payload),
};

// ------------------------------- applications
export const applicationsApi = {
  list: (status?: string) =>
    api.get<Application[]>(`/api/v1/applications${status ? `?status=${status}` : ""}`),
  get: (id: number) => api.get<Application>(`/api/v1/applications/${id}`),
  create: (payload: Record<string, unknown>) =>
    api.post<Application>("/api/v1/applications", payload),
  update: (id: number, payload: Record<string, unknown>) =>
    api.patch<Application>(`/api/v1/applications/${id}`, payload),
  remove: (id: number) => api.del(`/api/v1/applications/${id}`),
  setStatus: (id: number, status: ApplicationStatus, notes?: string) =>
    api.post<Application>(`/api/v1/applications/${id}/status`, { status, notes }),
  events: (id: number) =>
    api.get<ApplicationEvent[]>(`/api/v1/applications/${id}/events`),
  addNote: (id: number, notes: string) =>
    api.post(`/api/v1/applications/${id}/notes`, notes),
  reminders: () => api.get<Reminder[]>("/api/v1/applications/reminders"),
  createReminder: (payload: Record<string, unknown>) =>
    api.post<Reminder>("/api/v1/applications/reminders", payload),
  updateReminder: (id: number, payload: Record<string, unknown>) =>
    api.patch<Reminder>(`/api/v1/applications/reminders/${id}`, payload),
  deleteReminder: (id: number) => api.del(`/api/v1/applications/reminders/${id}`),
  analytics: () =>
    api.get<{
      total_applications: number;
      by_status: Record<string, number>;
      by_source: Record<string, number>;
      top_companies: [string, number][];
      interviews: number;
      offers: number;
      response_rate: number;
      weekly_activity: Record<string, number>;
      data_note: string;
    }>("/api/v1/applications/analytics"),
};

// ------------------------------- interviews
export const interviewsApi = {
  listSessions: () => api.get<InterviewSession[]>("/api/v1/interviews/sessions"),
  createSession: (payload: { job_listing_id?: number; application_id?: number; title?: string }) =>
    api.post<InterviewSession>("/api/v1/interviews/sessions", payload),
  getSession: (id: number) => api.get<InterviewSession>(`/api/v1/interviews/sessions/${id}`),
  answer: (sessionId: number, questionId: number, answer_text: string, duration_seconds?: number) =>
    api.post<InterviewAnswer>(`/api/v1/interviews/sessions/${sessionId}/answer/${questionId}`, {
      answer_text,
      duration_seconds,
    }),
  saveNotes: (sessionId: number, notes: string) =>
    api.post(`/api/v1/interviews/sessions/${sessionId}/notes`, notes),
};

// ------------------------------- insights
export const insightsApi = {
  get: () => api.get<InsightsResponse>("/api/v1/insights"),
  dismiss: (id: string) => api.post(`/api/v1/insights/${id}/dismiss`),
  dismissed: () => api.get<{ dismissed: string[] }>("/api/v1/insights/dismissed"),
};

// ------------------------------- AI providers
export const aiApi = {
  providers: () => api.get<AIProvider[]>("/api/v1/ai/providers"),
  createProvider: (payload: Record<string, unknown>) =>
    api.post<AIProvider>("/api/v1/ai/providers", payload),
  updateProvider: (id: number, payload: Record<string, unknown>) =>
    api.patch<AIProvider>(`/api/v1/ai/providers/${id}`, payload),
  deleteProvider: (id: number) => api.del(`/api/v1/ai/providers/${id}`),
  testProvider: (id: number) =>
    api.post<ProviderTestResult>(`/api/v1/ai/providers/${id}/test`),
  usage: () => api.get<AIUsageRecord[]>("/api/v1/ai/usage"),
  usageSummary: () =>
    api.get<{
      total_requests: number;
      total_tokens: number;
      total_estimated_cost_usd: number | null;
      cost_note: string | null;
      by_task: Record<string, number>;
    }>("/api/v1/ai/usage/summary"),
};

// ------------------------------- tasks & notifications
export const tasksApi = {
  list: () => api.get<BackgroundTask[]>("/api/v1/tasks"),
  cancel: (id: number) => api.post(`/api/v1/tasks/${id}/cancel`),
  stats: () => api.get<Record<string, number>>("/api/v1/tasks/stats"),
};

export const notificationsApi = {
  list: () => api.get<Notification[]>("/api/v1/notifications"),
  markRead: (id: number) => api.post(`/api/v1/notifications/${id}/read`),
  markAllRead: () => api.post("/api/v1/notifications/read-all"),
};

// ------------------------------- settings & privacy
export const settingsApi = {
  get: () => api.get<AppSettings>("/api/v1/settings"),
  update: (data: Partial<AppSettings>) =>
    api.patch<AppSettings>("/api/v1/settings", data),
};

export const privacyApi = {
  exportData: () => api.get<{ filename: string; content_b64: string; size_bytes: number }>("/api/v1/privacy/export"),
  backup: () => api.post<{ ok: boolean; path: string; size_bytes: number }>("/api/v1/privacy/backup"),
  restore: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.postForm<{ ok: boolean; detail: string }>("/api/v1/privacy/restore", formData);
  },
  deleteScope: (payload: Record<string, unknown>) =>
    api.post("/api/v1/privacy/delete", payload),
  integrity: () => api.get<{ ok: boolean; detail?: string }>("/api/v1/privacy/integrity"),
};

export type { Insight, Notification, BackgroundTask };
