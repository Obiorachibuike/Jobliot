// TypeScript contracts mirroring the backend Pydantic schemas.
// These are the shapes the UI consumes from /api/v1.

export type VerificationStatus =
  | "user_confirmed"
  | "imported_pending"
  | "extracted"
  | "ai_suggested"
  | "unverified"
  | "outdated";

export interface UserProfile {
  id: number;
  full_name?: string | null;
  preferred_name?: string | null;
  headline?: string | null;
  summary?: string | null;
  email?: string | null;
  phone?: string | null;
  location_city?: string | null;
  location_country?: string | null;
  website?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  other_profiles?: unknown;
  objectives?: string[] | null;
  onboarding_completed: boolean;
  onboarding_step: number;
  timezone?: string | null;
  locale?: string | null;
}

export interface WorkExperience {
  id: number;
  organization: string;
  job_title: string;
  employment_type?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  responsibilities?: string[] | null;
  achievements?: string[] | null;
  technologies?: string[] | null;
  team_leadership?: string | null;
  outcomes?: string | null;
  related_projects?: string[] | null;
  verification_status: VerificationStatus;
  provenance?: string | null;
}

export interface Education {
  id: number;
  institution: string;
  qualification?: string | null;
  field_of_study?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  relevant_coursework?: string[] | null;
  academic_achievements?: string[] | null;
  notes?: string | null;
  verification_status: VerificationStatus;
  provenance?: string | null;
}

export interface Skill {
  id: number;
  name: string;
  category?: string | null;
  proficiency?: string | null;
  years_experience?: number | null;
  last_used?: string | null;
  supporting_project?: string | null;
  confidence?: string | null;
  evidence?: string | null;
  verification_status: VerificationStatus;
  provenance?: string | null;
}

export interface Project {
  id: number;
  name: string;
  description?: string | null;
  problem_solved?: string | null;
  technologies?: string[] | null;
  responsibilities?: string[] | null;
  outcomes?: string | null;
  repository_url?: string | null;
  live_demo_url?: string | null;
  is_public: boolean;
  verification_status: VerificationStatus;
  provenance?: string | null;
}

export interface Certification {
  id: number;
  name: string;
  issuing_organization?: string | null;
  issue_date?: string | null;
  expiry_date?: string | null;
  credential_url?: string | null;
  credential_id?: string | null;
  verification_status: VerificationStatus;
  provenance?: string | null;
}

export interface Achievement {
  id: number;
  kind: string;
  title: string;
  description?: string | null;
  date?: string | null;
  organization?: string | null;
  url?: string | null;
  verification_status: VerificationStatus;
  provenance?: string | null;
}

export interface CareerPreference {
  id: number;
  desired_job_titles?: string[] | null;
  target_industries?: string[] | null;
  preferred_countries?: string[] | null;
  preferred_cities?: string[] | null;
  workplace_types?: string[] | null;
  employment_types?: string[] | null;
  experience_level?: string | null;
  salary_expectation_min?: number | null;
  salary_expectation_max?: number | null;
  minimum_acceptable_salary?: number | null;
  currency?: string | null;
  work_authorization?: string | null;
  relocation_preference?: string | null;
  company_sizes?: string[] | null;
  preferred_technologies?: string[] | null;
  avoid_technologies?: string[] | null;
  avoid_industries?: string[] | null;
  preferred_sources?: string[] | null;
  max_daily_recommendations?: number | null;
}

export interface WritingStyleProfile {
  id: number;
  formality?: string | null;
  detail_level?: string | null;
  confidence_tone?: string | null;
  explanation_style?: string | null;
  cv_style?: string | null;
  cover_letter_length?: string | null;
  uses_first_person: boolean;
  disliked_phrases?: string[] | null;
  directness?: string | null;
  chosen_examples?: string[] | null;
  writing_samples?: string[] | null;
  extracted_preferences?: Record<string, unknown> | null;
}

export interface OnboardingState {
  profile_exists: boolean;
  onboarding_completed: boolean;
  onboarding_step: number;
  completed_steps: number[];
  has_profile_data: boolean;
  objectives: string[];
}

// ------------------------------- jobs
export interface JobListing {
  id: number;
  title: string;
  company: string;
  location?: string | null;
  workplace_type?: string | null;
  employment_type?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency?: string | null;
  description?: string | null;
  requirements?: string[] | null;
  preferred_qualifications?: string[] | null;
  publication_date?: string | null;
  closing_date?: string | null;
  source_name?: string | null;
  url?: string | null;
  application_url?: string | null;
  date_discovered: string;
  last_verified?: string | null;
  status: string;
  has_match: boolean;
  match_score?: number | null;
  match_category?: string | null;
}

export interface JobSource {
  id: number;
  name: string;
  source_type: string;
  config?: Record<string, unknown> | null;
  enabled: boolean;
  health_status?: string | null;
  last_checked?: string | null;
  error_message?: string | null;
  requires_api_key: boolean;
}

export interface DimensionResult {
  name: string;
  label: string;
  score: number;
  weight: number;
  status: string;
  evidence: string[];
  details?: string | null;
}

export interface MatchReport {
  job_listing_id: number;
  overall_score: number;
  category: string;
  dimensions: DimensionResult[];
  strong_matches: string[];
  partial_matches: string[];
  missing_requirements: string[];
  potential_disqualifiers: string[];
  unknown_items: string[];
  factors: string[];
  narrative: string;
  weights?: Record<string, number> | null;
}

export interface SavedSearch {
  id: number;
  name: string;
  query?: string | null;
  filters?: Record<string, unknown> | null;
  source_ids?: number[] | null;
  schedule_enabled: boolean;
  schedule_cron?: string | null;
  is_active: boolean;
  last_run?: string | null;
  next_run?: string | null;
  min_match_score?: number | null;
}

export type JobSearch = SavedSearch;

// ------------------------------- documents
export interface DocumentBlock {
  type: string;
  text?: string | null;
  title?: string | null;
  organization?: string | null;
  date_range?: string | null;
  items?: string[] | null;
  lines?: string[] | null;
  meta?: string | null;
}

export interface DocumentSection {
  id: string;
  heading: string;
  blocks: DocumentBlock[];
}

export interface StructuredDocument {
  title: string;
  subtitle?: string | null;
  contact_line?: string | null;
  template_id: string;
  sections: DocumentSection[];
  kind?: string;
}

export interface DocTemplate {
  id: string;
  name: string;
  description: string;
  layout: string;
  best_for: string[];
  ats_safe: boolean;
}

export type DocumentTemplate = DocTemplate;

export interface MasterCV {
  id: number;
  title: string;
  template_id: string;
  content: StructuredDocument;
  auto_generate_from_profile: boolean;
  version: number;
  updated_at: string;
}

export interface ExportResult {
  filename: string;
  mime_type: string;
  size_bytes: number;
  content_b64: string;
  validator?: Record<string, unknown> | null;
}

export interface ProviderTestResult {
  ok: boolean;
  provider: string;
  model?: string | null;
  latency_ms?: number | null;
  error?: string | null;
  sample?: string | null;
}

export interface MatchWeights {
  required_skills: number;
  preferred_skills: number;
  experience: number;
  education: number;
  certifications: number;
  projects: number;
  seniority: number;
  location: number;
  employment_type: number;
  salary: number;
  portfolio: number;
}

export type MatchCategory = "strong_match" | "worth_considering" | "stretch_opportunity" | "low_match";

export interface CVImportResult {
  extracted: Record<string, unknown>;
  uncertain_fields: string[];
  warnings: string[];
}

export interface CareerDocument {
  id: number;
  profile_id: number;
  job_listing_id?: number | null;
  application_id?: number | null;
  kind: string;
  title: string;
  template_id: string;
  status: string;
  content?: StructuredDocument | null;
  strategy?: Record<string, unknown> | null;
  match_data?: MatchReport | null;
  approved_by_user: boolean;
  current_version: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentVersion {
  id: number;
  version_number: number;
  content: StructuredDocument;
  status?: string | null;
  change_summary?: string | null;
  agent_stage?: string | null;
  findings: ReviewFinding[];
  created_at: string;
}

export interface ReviewFinding {
  id: string;
  severity: "critical" | "major" | "minor" | "suggestion";
  category: string;
  location?: string | null;
  message: string;
  evidence?: string | null;
  recommendation?: string | null;
  requires_user_confirmation: boolean;
  resolved: boolean;
}

export interface ReviewResult {
  findings: ReviewFinding[];
  critical_count: number;
  major_count: number;
  minor_count: number;
  suggestion_count: number;
  overall_assessment?: string | null;
  readiness: string;
}

export interface Strategy {
  positioning?: string | null;
  selected_experience: Record<string, unknown>[];
  selected_projects: Record<string, unknown>[];
  selected_skills: string[];
  key_messages: string[];
  gaps: string[];
  gap_mitigations: string[];
  keyword_targets: string[];
  evidence_refs: Record<string, unknown>[];
}

// ------------------------------- applications
export type ApplicationStatus =
  | "saved"
  | "planning"
  | "documents_in_progress"
  | "ready_to_apply"
  | "applied"
  | "assessment"
  | "interview"
  | "offer"
  | "rejected"
  | "withdrawn"
  | "closed";

export interface ApplicationEvent {
  id: number;
  application_id: number;
  event_type: string;
  from_status?: string | null;
  to_status?: string | null;
  notes?: string | null;
  occurred_at: string;
}

export interface Application {
  id: number;
  job_listing_id?: number | null;
  company: string;
  job_title: string;
  location?: string | null;
  application_url?: string | null;
  source_name?: string | null;
  status: ApplicationStatus;
  match_score?: number | null;
  deadline?: string | null;
  date_applied?: string | null;
  follow_up_dates?: string[] | null;
  interview_dates?: string[] | null;
  notes?: string | null;
  outcome?: string | null;
  user_feedback?: string | null;
  recruiter_name?: string | null;
  recruiter_email?: string | null;
  created_at: string;
  updated_at: string;
  events?: ApplicationEvent[];
}

export interface Reminder {
  id: number;
  application_id?: number | null;
  kind: string;
  title: string;
  description?: string | null;
  due_at: string;
  timezone?: string | null;
  recurrence?: string | null;
  is_done: boolean;
  reminded_at?: string | null;
}

// ------------------------------- interviews
export interface InterviewAnswer {
  id: number;
  question_id: number;
  answer_text: string;
  duration_seconds?: number | null;
  scores?: Record<string, number> | null;
  feedback?: string | null;
  suggested_improvements?: string[] | null;
  evidence_used?: string[] | null;
}

export interface CVVersion {
  id: number;
  version_number: number;
  content: StructuredDocument;
  note?: string | null;
  created_at: string;
}

export interface InterviewQuestion {
  id: number;
  category: string;
  question: string;
  order_index: number;
  follow_ups?: string[] | null;
  answer?: InterviewAnswer | null;
}

export interface InterviewSession {
  id: number;
  title: string;
  job_listing_id?: number | null;
  application_id?: number | null;
  started_at?: string | null;
  completed_at?: string | null;
  overall_score?: number | null;
  summary?: string | null;
  feedback?: Record<string, unknown> | null;
  questions: InterviewQuestion[];
}

// ------------------------------- AI providers
export interface AIProvider {
  id: number;
  name: string;
  provider: string;
  base_url?: string | null;
  model?: string | null;
  models?: string[] | null;
  is_local: boolean;
  temperature?: number | null;
  max_tokens?: number | null;
  timeout_seconds?: number | null;
  retries?: number | null;
  task_models?: Record<string, string> | null;
  is_default: boolean;
  enabled: boolean;
  status?: string | null;
  last_tested?: string | null;
  error_message?: string | null;
  has_api_key: boolean;
  disclosure_acknowledged: boolean;
}

export interface AIUsageRecord {
  id: number;
  provider?: string | null;
  model?: string | null;
  task?: string | null;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  total_tokens?: number | null;
  estimated_cost?: number | null;
  duration_ms?: number | null;
  status?: string | null;
  error?: string | null;
  created_at: string;
}

// ------------------------------- tasks & notifications
export interface BackgroundTask {
  id: number;
  task_type: string;
  name: string;
  status: string;
  progress?: number | null;
  progress_label?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  error_details?: string | null;
  result_summary?: Record<string, unknown> | null;
  cancellable: boolean;
  cancel_requested: boolean;
  attempts: number;
}

export interface Notification {
  id: number;
  title: string;
  body?: string | null;
  kind?: string | null;
  is_read: boolean;
  related_type?: string | null;
  related_id?: number | null;
}

// ------------------------------- insights
export interface Insight {
  id: string;
  title: string;
  description: string;
  kind: string;
  metric?: string | null;
  evidence?: Record<string, unknown> | null;
  how_calculated: string;
  dismissed?: boolean;
}

export interface InsightsResponse {
  generated_at: string;
  insights: Insight[];
  stats: Record<string, number>;
}

// ------------------------------- settings
export interface AppSettings {
  theme: string;
  review_rounds: number;
  match_weights: Record<string, number>;
  scheduler_enabled: boolean;
  max_daily_recommendations: number;
  notifications_enabled: boolean;
  default_template_id: string;
  match_category_thresholds: Record<string, number>;
}

export interface HealthInfo {
  status: string;
  app: string;
  version: string;
  environment: string;
  auth_required: boolean;
  database: string;
}
