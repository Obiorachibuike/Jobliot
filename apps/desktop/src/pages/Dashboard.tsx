import { Link } from "react-router-dom";
import {
  Briefcase,
  FileText,
  Send,
  MessageSquare,
  TrendingUp,
  Sparkles,
  Clock,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Plus,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import {
  aiApi,
  applicationsApi,
  insightsApi,
  jobsApi,
  notificationsApi,
  tasksApi,
  profileApi,
} from "../services/backend";
import { Card, CardHeader, Badge, EmptyState, Spinner } from "../components/ui";
import { cx } from "../components/ui";
import { useEffect } from "react";
import { useToast } from "../components/ui/Toast";
import { matchCategoryMeta, scoreToCategory } from "../theme/match";

export default function Dashboard() {
  const profile = useApi(() => profileApi.onboardingState(), []);
  const applications = useApi(() => applicationsApi.list(), []);
  const jobs = useApi(() => jobsApi.list({ limit: 6 }), []);
  const insights = useApi(() => insightsApi.get(), []);
  const reminders = useApi(() => applicationsApi.reminders(), []);
  const tasks = useApi(() => tasksApi.list(), []);
  const notifications = useApi(() => notificationsApi.list(), []);
  const toast = useToast();

  useEffect(() => {
    const unread = (notifications.data || []).filter((n) => !n.is_read).length;
    if (unread > 0) toast.info(`${unread} unread notification${unread > 1 ? "s" : ""}`);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loading =
    profile.loading || applications.loading || jobs.loading;

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner className="h-6 w-6" />
      </div>
    );
  }

  const apps = applications.data || [];
  const activeJobs = jobs.data || [];
  const stats = insights.data?.stats || {};
  const dueReminders = (reminders.data || []).filter(
    (r) => !r.is_done
  );
  const runningTasks = (tasks.data || []).filter(
    (t) => t.status === "running" || t.status === "queued"
  );
  const needsConfirmation = apps.filter(
    (a) => a.status === "ready_to_apply"
  );

  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-primary">
            {greeting} 👋
          </h1>
          <p className="mt-1 text-sm text-muted">
            {new Date().toLocaleDateString(undefined, {
              weekday: "long",
              month: "long",
              day: "numeric",
            })}
            {" · "}Your career command center
          </p>
        </div>
        <Link to="/jobs">
          <button className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-black hover:bg-accent-hover">
            <Plus className="h-4 w-4" /> Find jobs
          </button>
        </Link>
      </div>

      {/* KPI cards */}
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          icon={<Send className="h-4 w-4" />}
          label="Applications"
          value={String(stats.applications ?? apps.length)}
          to="/applications"
        />
        <StatCard
          icon={<CheckCircle2 className="h-4 w-4" />}
          label="Interviews"
          value={String((stats.interview_sessions ?? 0))}
          to="/interviews"
        />
        <StatCard
          icon={<Briefcase className="h-4 w-4" />}
          label="Jobs tracked"
          value={String(stats.job_listings ?? activeJobs.length)}
          to="/jobs"
        />
        <StatCard
          icon={<TrendingUp className="h-4 w-4" />}
          label="Strong matches"
          value={String(stats.strong_matches ?? 0)}
          to="/jobs"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column */}
        <div className="space-y-6 lg:col-span-2">
          {/* Next actions */}
          <Card>
            <CardHeader title="Next actions" subtitle="What needs your attention now" />
            <div className="space-y-3">
              {runningTasks.length > 0 && (
                <div className="flex items-center gap-3 rounded-lg border border-border bg-elevated px-3 py-2">
                  <Spinner className="h-4 w-4" />
                  <span className="text-sm text-primary">
                    Background task running ({runningTasks.length})
                  </span>
                  <Link to="/settings" className="ml-auto text-xs text-accent hover:underline">
                    View
                  </Link>
                </div>
              )}
              {needsConfirmation.length > 0 && (
                <ActionItem
                  icon={<FileText className="h-4 w-4 text-warning" />}
                  title={`${needsConfirmation.length} application(s) ready to submit`}
                  body="Review and confirm before applying - CareerPilot never auto-submits."
                  to="/applications"
                  cta="Review"
                />
              )}
              {dueReminders.length > 0 && (
                <ActionItem
                  icon={<Clock className="h-4 w-4 text-warning" />}
                  title={`${dueReminders.length} reminder${dueReminders.length > 1 ? "s" : ""} due soon`}
                  body="Follow-ups, deadlines, and interview prep."
                  to="/applications"
                  cta="View reminders"
                />
              )}
              {!profile.data?.onboarding_completed && (
                <ActionItem
                  icon={<AlertCircle className="h-4 w-4 text-accent" />}
                  title="Finish setting up your profile"
                  body="Complete onboarding to unlock tailored matching and drafting."
                  to="/onboarding"
                  cta="Continue setup"
                />
              )}
              {(runningTasks.length === 0 &&
                needsConfirmation.length === 0 &&
                dueReminders.length === 0 &&
                profile.data?.onboarding_completed) && (
                <p className="px-1 py-4 text-sm text-muted">
                  All caught up. Discover jobs or prepare an interview.
                </p>
              )}
            </div>
          </Card>

          {/* Recent jobs */}
          <Card>
            <CardHeader
              title="Recent opportunities"
              subtitle="Newest listings across your sources"
              action={
                <Link to="/jobs" className="flex items-center text-xs text-accent hover:underline">
                  View all <ArrowRight className="ml-1 h-3 w-3" />
                </Link>
              }
            />
            {activeJobs.length === 0 ? (
              <EmptyState
                icon={<Briefcase className="h-8 w-8" />}
                title="No jobs yet"
                description="Discover opportunities from your sources, import a URL, or add one manually."
                action={
                  <Link to="/jobs">
                    <button className="rounded-lg bg-accent px-3 py-1.5 text-xs font-semibold text-black">
                      Discover jobs
                    </button>
                  </Link>
                }
              />
            ) : (
              <ul className="divide-y divide-border">
                {activeJobs.slice(0, 5).map((job) => {
                  const cat = job.match_category || scoreToCategory(job.match_score ?? 0);
                  const meta = matchCategoryMeta[cat] || matchCategoryMeta.low_match;
                  return (
                    <li key={job.id}>
                      <Link
                        to={`/jobs/${job.id}`}
                        className="flex items-center gap-3 px-2 py-2.5 hover:bg-elevated"
                      >
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-medium text-primary">
                            {job.title}
                          </div>
                          <div className="truncate text-xs text-muted">
                            {job.company}
                            {job.location ? ` · ${job.location}` : ""}
                          </div>
                        </div>
                        {job.has_match && job.match_score != null && (
                          <Badge tone={meta.tone as never}>
                            {Math.round(job.match_score)}
                          </Badge>
                        )}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
          </Card>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          <Card>
            <CardHeader title="AI status" subtitle="Provider & engine state" />
            <AiStatusPanel />
          </Card>

          <Card>
            <CardHeader title="Today's focus" subtitle="Suggested next step" />
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent/10">
                <Sparkles className="h-4 w-4 text-accent" />
              </div>
              <div>
                <p className="text-sm font-medium text-primary">
                  {apps.length === 0 ? "Set up your first application" : "Tailor your next application"}
                </p>
                <p className="mt-1 text-xs text-muted">
                  {apps.length === 0
                    ? "Find a job in Discover, then generate a tailored CV and cover letter."
                    : "Open the Application Studio to draft with the multi-agent reviewer."}
                </p>
                <Link
                  to="/studio"
                  className="mt-2 inline-flex items-center text-xs font-medium text-accent hover:underline"
                >
                  Open Studio <ArrowRight className="ml-1 h-3 w-3" />
                </Link>
              </div>
            </div>
          </Card>

          {insights.data && insights.data.insights.length > 0 && (
            <Card>
              <CardHeader title="Quick insight" subtitle="From your real data" />
              <InsightCard insight={insights.data.insights[0]} />
              <Link to="/insights" className="mt-2 inline-flex items-center text-xs text-accent hover:underline">
                All insights <ArrowRight className="ml-1 h-3 w-3" />
              </Link>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  to,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  to: string;
}) {
  return (
    <Link to={to}>
      <Card className="h-full transition-colors hover:border-accent/40">
        <div className="flex items-center gap-2 text-muted">
          {icon}
          <span className="text-xs font-medium">{label}</span>
        </div>
        <div className="mt-2 text-2xl font-bold text-primary">{value}</div>
      </Card>
    </Link>
  );
}

function ActionItem({
  icon,
  title,
  body,
  cta,
  to,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
  cta: string;
  to: string;
}) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border bg-elevated px-3 py-2.5">
      <div className="mt-0.5 shrink-0">{icon}</div>
      <div className="min-w-0 flex-1">
        <div className="text-sm font-medium text-primary">{title}</div>
        <div className="mt-0.5 text-xs text-muted">{body}</div>
      </div>
      <Link
        to={to}
        className="shrink-0 rounded-lg border border-border px-2.5 py-1 text-xs text-secondary hover:border-accent/50 hover:text-primary"
      >
        {cta}
      </Link>
    </div>
  );
}

function AiStatusPanel() {
  const { data } = useApi(() => aiApi.providers(), []);
  const list = data || [];
  const configured = list.length > 0;
  const anyOk = list.some((p) => p.status === "ok");
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span
          className={cx(
            "h-2 w-2 rounded-full",
            configured ? (anyOk ? "bg-success" : "bg-warning") : "bg-muted"
          )}
        />
        <span className="text-sm text-primary">
          {configured ? (anyOk ? "AI provider connected" : "AI provider needs attention") : "No AI provider configured"}
        </span>
      </div>
      <p className="text-xs text-muted">
        {configured
          ? "Documents will be drafted with your configured provider."
          : "The deterministic local engine handles strategy, drafting, review, and revision offline."}
      </p>
      <Link to="/settings/ai" className="inline-flex items-center text-xs text-accent hover:underline">
        Configure providers <ArrowRight className="ml-1 h-3 w-3" />
      </Link>
    </div>
  );
}

function InsightCard({ insight }: { insight: { title: string; description: string; kind: string } }) {
  return (
    <div className="rounded-lg border border-border bg-elevated p-3">
      <div className="flex items-center gap-2">
        <Badge tone="neutral">{insight.kind}</Badge>
        <span className="text-sm font-medium text-primary">{insight.title}</span>
      </div>
      <p className="mt-1.5 text-xs text-secondary">{insight.description}</p>
    </div>
  );
}
