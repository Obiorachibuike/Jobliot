import { useEffect, useMemo, useState } from "react";
import {
  Plus,
  Calendar,
  DollarSign,
  TrendingUp,
  PieChart as PieIcon,
  Activity,
  ExternalLink,
  Clock,
} from "lucide-react";
import { useApi, useAsync } from "../hooks/useApi";
import { applicationsApi, jobsApi } from "../services/backend";
import type { Application, ApplicationStatus } from "../types/api";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  ConfirmDialog,
  EmptyState,
  Input,
  Modal,
  Progress,
  Select,
  Spinner,
  Textarea,
} from "../components/ui";
import { useToast } from "../components/ui/Toast";
import { applicationStatusMeta } from "../theme/match";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from "recharts";
import { cx } from "../components/ui";

const COLUMNS: ApplicationStatus[] = [
  "saved",
  "planning",
  "documents_in_progress",
  "ready_to_apply",
  "applied",
  "assessment",
  "interview",
  "offer",
  "rejected",
];

// Non-purple palette for charts (product rule: no purple anywhere).
const PIE_COLORS = ["#39FF14", "#4ADE80", "#FACC15", "#F97316", "#38BDF8", "#F87171", "#94A3B8"];

export default function ApplicationTracker() {
  const applications = useApi(() => applicationsApi.list(), []);
  const jobs = useApi(() => jobsApi.list({ limit: 200 }), []);
  const analytics = useApi(() => applicationsApi.analytics(), []);
  const [view, setView] = useState<"board" | "list">("board");
  const [createOpen, setCreateOpen] = useState(false);
  const [selected, setSelected] = useState<Application | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const move = useAsync<Application, []>();
  const del = useAsync<unknown, []>();
  const toast = useToast();

  const apps = applications.data || [];

  const byStatus = useMemo(() => {
    const map: Record<string, Application[]> = {};
    COLUMNS.forEach((c) => (map[c] = []));
    apps.forEach((a) => {
      const col = COLUMNS.includes(a.status) ? a.status : "saved";
      map[col].push(a);
    });
    return map;
  }, [apps]);

  const moveStatus = async (id: number, status: ApplicationStatus) => {
    try {
      await move.run(() => applicationsApi.setStatus(id, status));
      toast.success(`Moved to ${applicationStatusMeta[status]?.label || status}`);
      applications.refetch();
    } catch {
      toast.error("Could not update status");
    }
  };

  return (
    <div className="mx-auto max-w-7xl p-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-primary">Application Tracker</h1>
          <p className="mt-1 text-sm text-muted">
            Your pipeline, from saved to offer. Drag cards or use the menu.
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={view} onChange={(e) => setView(e.target.value as "board" | "list")} options={[{ value: "board", label: "Board" }, { value: "list", label: "List" }]} className="w-32" />
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" /> New application
          </Button>
        </div>
      </div>

      {/* Analytics strip */}
      {analytics.data && (
        <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-5">
          <MiniStat label="Total" value={analytics.data.total_applications} />
          <MiniStat label="Applied" value={(analytics.data.by_status.applied || 0) + (analytics.data.by_status.interview || 0) + (analytics.data.by_status.offer || 0)} />
          <MiniStat label="Interviews" value={analytics.data.interviews} />
          <MiniStat label="Offers" value={analytics.data.offers} />
          <MiniStat label="Response rate" value={`${analytics.data.response_rate}%`} />
        </div>
      )}

      {applications.loading ? (
        <div className="flex justify-center py-16"><Spinner /></div>
      ) : apps.length === 0 ? (
        <EmptyState
          icon={<TrendingUp className="h-8 w-8" />}
          title="No applications yet"
          description="Track a job from Discover, or add one manually. CareerPilot never applies on your behalf."
          action={<Button onClick={() => setCreateOpen(true)}>Add application</Button>}
        />
      ) : view === "board" ? (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {COLUMNS.map((col) => (
            <div key={col} className="w-64 shrink-0">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wide text-secondary">
                  {applicationStatusMeta[col]?.label || col}
                </span>
                <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] text-muted">
                  {byStatus[col].length}
                </span>
              </div>
              <div className="space-y-2 rounded-xl border border-dashed border-border p-2 min-h-[120px]">
                {byStatus[col].map((a) => (
                  <ApplicationCard
                    key={a.id}
                    application={a}
                    onOpen={() => setSelected(a)}
                    onMove={(status) => moveStatus(a.id, status)}
                    onDelete={() => setDeleteId(a.id)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Card>
          <ul className="divide-y divide-border">
            {apps.map((a) => (
              <li key={a.id} className="flex items-center gap-3 px-3 py-2.5">
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium text-primary">{a.job_title}</div>
                  <div className="text-xs text-muted">{a.company}</div>
                </div>
                {a.match_score != null && <Badge tone="accent">{Math.round(a.match_score)}</Badge>}
                <Select
                  value={a.status}
                  onChange={(e) => moveStatus(a.id, e.target.value as ApplicationStatus)}
                  options={Object.entries(applicationStatusMeta).map(([v, m]) => ({ value: v, label: m.label }))}
                  className="w-44"
                />
                <Button size="sm" variant="ghost" onClick={() => setSelected(a)}>Open</Button>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Charts */}
      {analytics.data && apps.length > 0 && (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader title="Status distribution" subtitle="Applications by stage" />
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={Object.entries(analytics.data.by_status).map(([name, value]) => ({ name, value }))}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={70}
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {Object.keys(analytics.data.by_status).map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
          <Card>
            <CardHeader title="Weekly activity" subtitle="Applications created per week" />
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={Object.entries(analytics.data.weekly_activity || {}).map(([week, count]) => ({ week: week.split("-W")[1], count }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border))" />
                  <XAxis dataKey="week" tick={{ fontSize: 10, fill: "rgb(var(--text-muted))" }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: "rgb(var(--text-muted))" }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="rgb(var(--accent))" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      )}

      {createOpen && (
        <CreateApplicationModal
          jobs={jobs.data || []}
          onClose={() => setCreateOpen(false)}
          onCreated={() => {
            applications.refetch();
            analytics.refetch();
          }}
        />
      )}

      {selected && (
        <ApplicationDetail
          application={selected}
          onClose={() => {
            setSelected(null);
            applications.refetch();
            analytics.refetch();
          }}
          onDelete={() => setDeleteId(selected.id)}
        />
      )}

      <ConfirmDialog
        open={deleteId !== null}
        title="Delete application"
        message="Delete this application and its history? This cannot be undone."
        confirmLabel="Delete"
        onCancel={() => setDeleteId(null)}
        onConfirm={async () => {
          if (deleteId === null) return;
          try {
            await applicationsApi.remove(deleteId);
            toast.success("Application deleted");
            applications.refetch();
            analytics.refetch();
          } catch {
            toast.error("Could not delete");
          }
          setDeleteId(null);
        }}
      />
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: number | string }) {
  return (
    <Card>
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-1 text-xl font-bold text-primary">{value}</div>
    </Card>
  );
}

function ApplicationCard({
  application,
  onOpen,
  onMove,
  onDelete,
}: {
  application: Application;
  onOpen: () => void;
  onMove: (status: ApplicationStatus) => void;
  onDelete: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <Card className="cursor-pointer p-3 hover:border-accent/40" onClick={onOpen}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-primary">{application.job_title}</div>
          <div className="truncate text-xs text-muted">{application.company}</div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            setMenuOpen((o) => !o);
          }}
          className="text-muted hover:text-primary"
          aria-label="Move application"
        >
          ⋮
        </button>
      </div>
      {application.match_score != null && (
        <div className="mt-2">
          <div className="mb-0.5 flex justify-between text-[10px] text-muted">
            <span>Match</span>
            <span>{Math.round(application.match_score)}</span>
          </div>
          <Progress value={application.match_score} className="h-1" />
        </div>
      )}
      {application.deadline && (
        <div className="mt-2 flex items-center gap-1 text-[11px] text-muted">
          <Clock className="h-3 w-3" /> Deadline {application.deadline}
        </div>
      )}
      {menuOpen && (
        <div className="absolute z-10 mt-1 rounded-lg border border-border bg-surface p-1 shadow-xl" onClick={(e) => e.stopPropagation()}>
          {COLUMNS.filter((c) => c !== application.status).slice(0, 8).map((c) => (
            <button
              key={c}
              onClick={() => {
                onMove(c);
                setMenuOpen(false);
              }}
              className="block w-full rounded px-2 py-1 text-left text-xs text-secondary hover:bg-elevated hover:text-primary"
            >
              Move to {applicationStatusMeta[c]?.label || c}
            </button>
          ))}
          <button
            onClick={() => {
              onDelete();
              setMenuOpen(false);
            }}
            className="block w-full rounded px-2 py-1 text-left text-xs text-danger hover:bg-danger/10"
          >
            Delete
          </button>
        </div>
      )}
    </Card>
  );
}

function CreateApplicationModal({ jobs, onClose, onCreated }: { jobs: import("../types/api").JobListing[]; onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ job_listing_id: "", company: "", job_title: "", location: "", application_url: "", source_name: "manual", deadline: "" });
  const save = useAsync<Application, []>();
  const toast = useToast();

  const pickJob = (id: string) => {
    const job = jobs.find((j) => j.id === Number(id));
    if (job) {
      setForm((f) => ({
        ...f,
        job_listing_id: id,
        company: job.company,
        job_title: job.title,
        location: job.location || "",
        application_url: job.application_url || "",
        source_name: job.source_name || "manual",
      }));
    }
  };

  const submit = async () => {
    if (!form.company.trim() || !form.job_title.trim()) return;
    try {
      await save.run(() =>
        applicationsApi.create({
          job_listing_id: form.job_listing_id ? Number(form.job_listing_id) : null,
          company: form.company,
          job_title: form.job_title,
          location: form.location || null,
          application_url: form.application_url || null,
          source_name: form.source_name,
          deadline: form.deadline || null,
        })
      );
      toast.success("Application added");
      onCreated();
      onClose();
    } catch {
      toast.error("Could not add application");
    }
  };

  return (
    <Modal
      open
      onClose={onClose}
      title="Add application"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={submit} loading={save.loading} disabled={!form.company.trim() || !form.job_title.trim()}>Add</Button>
        </>
      }
    >
      <div className="space-y-3">
        <Select label="From saved job" value={form.job_listing_id} onChange={(e) => pickJob(e.target.value)} options={[{ value: "", label: "None - enter manually" }, ...jobs.map((j) => ({ value: String(j.id), label: `${j.title} · ${j.company}` }))]} />
        <div className="grid grid-cols-2 gap-3">
          <Input label="Company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
          <Input label="Job title" value={form.job_title} onChange={(e) => setForm({ ...form, job_title: e.target.value })} />
        </div>
        <Input label="Location" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
        <Input label="Application URL" value={form.application_url} onChange={(e) => setForm({ ...form, application_url: e.target.value })} />
        <Input label="Deadline" type="date" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} />
      </div>
    </Modal>
  );
}

function ApplicationDetail({ application, onClose, onDelete }: { application: Application; onClose: () => void; onDelete: () => void }) {
  const [status, setStatus] = useState(application.status);
  const [notes, setNotes] = useState("");
  const setStatusAsync = useAsync<Application, []>();
  const toast = useToast();
  const events = useApi(() => applicationsApi.events(application.id), [application.id]);

  const doSetStatus = async () => {
    try {
      await setStatusAsync.run(() => applicationsApi.setStatus(application.id, status as ApplicationStatus, notes));
      toast.success("Status updated");
      setNotes("");
      onClose();
    } catch {
      toast.error("Could not update");
    }
  };

  return (
    <Modal
      open
      onClose={onClose}
      title={`${application.job_title} · ${application.company}`}
      footer={
        <>
          <Button variant="danger" onClick={onDelete} className="mr-auto">Delete</Button>
          <Button variant="ghost" onClick={onClose}>Close</Button>
          <Button onClick={doSetStatus} loading={setStatusAsync.loading}>Save status</Button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <Select label="Status" value={status} onChange={(e) => setStatus(e.target.value as ApplicationStatus)} options={Object.entries(applicationStatusMeta).map(([v, m]) => ({ value: v, label: m.label }))} />
          <Input label="Deadline" type="date" value={application.deadline || ""} readOnly />
        </div>
        {application.match_score != null && (
          <div>
            <div className="mb-1 flex justify-between text-xs text-muted"><span>Match score</span><span>{Math.round(application.match_score)}</span></div>
            <Progress value={application.match_score} />
          </div>
        )}
        {application.application_url && (
          <a href={application.application_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-accent hover:underline">
            <ExternalLink className="h-3 w-3" /> Open application page
          </a>
        )}
        <Textarea label="Add a note" value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} placeholder="Recruiter name, next steps..." />
        {application.recruiter_name && (
          <p className="text-xs text-secondary">Recruiter: {application.recruiter_name}{application.recruiter_email ? ` (${application.recruiter_email})` : ""}</p>
        )}
        <div>
          <span className="mb-1 block text-xs font-medium text-secondary">History</span>
          <ul className="space-y-1">
            {(events.data || []).slice(0, 10).map((e) => (
              <li key={e.id} className="flex items-center gap-2 text-xs text-muted">
                <span className="rounded bg-secondary px-1.5 py-0.5">{e.event_type.replace(/_/g, " ")}</span>
                {e.to_status && <span className="text-secondary">→ {e.to_status}</span>}
                <span className="ml-auto">{new Date(e.occurred_at).toLocaleDateString()}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Modal>
  );
}
