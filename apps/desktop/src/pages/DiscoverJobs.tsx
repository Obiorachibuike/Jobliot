import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Search,
  Plus,
  Link2,
  RefreshCw,
  Briefcase,
  MapPin,
  Globe,
  Building2,
} from "lucide-react";
import { useApi, useAsync } from "../hooks/useApi";
import { jobsApi } from "../services/backend";
import type { JobListing, JobSource } from "../types/api";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  Input,
  Modal,
  Select,
  Spinner,
  Textarea,
} from "../components/ui";
import { useToast } from "../components/ui/Toast";
import { matchCategoryMeta, scoreToCategory } from "../theme/match";
import { cx } from "../components/ui";

const WORKPLACE_TYPES = ["remote", "hybrid", "onsite"];
const EMPLOYMENT_TYPES = ["full-time", "contract", "part-time", "internship", "freelance"];

export default function DiscoverJobs() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();

  const [filters, setFilters] = useState({
    q: params.get("q") || "",
    title: "",
    company: "",
    location: "",
    workplace_type: "",
    min_match_score: "",
  });

  const listings = useApi(
    () =>
      jobsApi.list({
        q: filters.q || undefined,
        title: filters.title || undefined,
        company: filters.company || undefined,
        location: filters.location || undefined,
        workplace_type: filters.workplace_type || undefined,
        min_match_score: filters.min_match_score || undefined,
        limit: 200,
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [filters.q, filters.title, filters.company, filters.location, filters.workplace_type, filters.min_match_score]
  );

  const sources = useApi(() => jobsApi.sources(), []);
  const sourceTypes = useApi(() => jobsApi.availableSourceTypes(), []);
  const discover = useAsync<{ discovered: number; errors: string[] }, []>();
  const [importOpen, setImportOpen] = useState(false);
  const [manualOpen, setManualOpen] = useState(false);

  const results = listings.data || [];

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-primary">Discover Jobs</h1>
          <p className="mt-1 text-sm text-muted">
            Search saved listings, import from a URL, or connect a public
            job board.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setManualOpen(true)}>
            <Plus className="h-4 w-4" /> Add manually
          </Button>
          <Button variant="secondary" onClick={() => setImportOpen(true)}>
            <Link2 className="h-4 w-4" /> Import URL
          </Button>
          <Button
            onClick={async () => {
              const res = await discover.run(() => jobsApi.discover({ limit: 50 }));
              if (res) {
                if (res.errors.length) {
                  toast.error(`Some sources failed: ${res.errors[0]}`);
                }
                if (res.discovered > 0) {
                  toast.success(`Discovered ${res.discovered} listing(s)`);
                } else if (!res.errors.length) {
                  toast.info("No new listings found");
                }
                listings.refetch();
              }
            }}
            loading={discover.loading}
          >
            <RefreshCw className="h-4 w-4" /> Discover
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="mb-4">
        <div className="flex flex-wrap gap-3">
          <div className="relative min-w-52 flex-1">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
            <input
              value={filters.q}
              onChange={(e) => setFilters({ ...filters, q: e.target.value })}
              placeholder="Search title, company, description..."
              className="w-full rounded-lg border border-border bg-input py-2 pl-8 pr-3 text-sm text-primary placeholder:text-muted focus:border-accent/60 focus:outline-none"
              aria-label="Search jobs"
            />
          </div>
          <Select
            value={filters.workplace_type}
            onChange={(e) => setFilters({ ...filters, workplace_type: e.target.value })}
            options={[{ value: "", label: "All workplace types" }, ...WORKPLACE_TYPES.map((w) => ({ value: w, label: w[0].toUpperCase() + w.slice(1) }))]}
            className="w-44"
          />
          <Select
            value={filters.min_match_score}
            onChange={(e) => setFilters({ ...filters, min_match_score: e.target.value })}
            options={[
              { value: "", label: "Any match score" },
              { value: "75", label: "Strong (75+)" },
              { value: "55", label: "Worth considering (55+)" },
              { value: "35", label: "Stretch (35+)" },
            ]}
            className="w-48"
          />
        </div>
      </Card>

      {/* Source health strip */}
      {sources.data && sources.data.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {sources.data.map((s) => (
            <span
              key={s.id}
              className={cx(
                "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px]",
                s.health_status === "error"
                  ? "border-danger/30 text-danger"
                  : s.health_status === "ok"
                    ? "border-success/30 text-success"
                    : "border-border text-muted"
              )}
              title={s.error_message || undefined}
            >
              <span className={cx("h-1.5 w-1.5 rounded-full", s.health_status === "ok" ? "bg-success" : s.health_status === "error" ? "bg-danger" : "bg-muted")} />
              {s.name}
            </span>
          ))}
        </div>
      )}

      {listings.loading ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6" />
        </div>
      ) : results.length === 0 ? (
        <EmptyState
          icon={<Briefcase className="h-8 w-8" />}
          title="No job listings yet"
          description="Import a job URL, add one manually, or configure a public job board source (Greenhouse or Lever) to start discovering opportunities."
          action={
            <Button onClick={() => setImportOpen(true)}>
              <Link2 className="h-4 w-4" /> Import a job URL
            </Button>
          }
        />
      ) : (
        <div className="grid gap-3">
          {results.map((job) => (
            <JobCard key={job.id} job={job} onOpen={() => navigate(`/jobs/${job.id}`)} />
          ))}
        </div>
      )}

      <UrlImportModal open={importOpen} onClose={() => setImportOpen(false)} onImported={() => { listings.refetch(); }} />
      <ManualJobModal open={manualOpen} onClose={() => setManualOpen(false)} onCreated={() => { listings.refetch(); }} />
    </div>
  );
}

function JobCard({ job, onOpen }: { job: JobListing; onOpen: () => void }) {
  const cat = job.match_category || scoreToCategory(job.match_score ?? 0);
  const meta = matchCategoryMeta[cat] || matchCategoryMeta.low_match;
  return (
    <button
      onClick={onOpen}
      className="block w-full rounded-xl border border-border bg-surface p-4 text-left transition-colors hover:border-accent/40"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-primary">{job.title}</div>
          <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
            <span className="inline-flex items-center gap-1"><Building2 className="h-3 w-3" />{job.company}</span>
            {job.location && <span className="inline-flex items-center gap-1"><MapPin className="h-3 w-3" />{job.location}</span>}
            {job.workplace_type && <span className="inline-flex items-center gap-1"><Globe className="h-3 w-3" />{job.workplace_type}</span>}
            <span className="inline-flex items-center gap-1"><Briefcase className="h-3 w-3" />{job.source_name || "manual"}</span>
          </div>
        </div>
        {job.has_match && job.match_score != null && (
          <div className="flex shrink-0 flex-col items-end gap-1">
            <Badge tone={meta.tone as never}>{Math.round(job.match_score)}</Badge>
            <span className="text-[10px] text-muted">{meta.label}</span>
          </div>
        )}
      </div>
    </button>
  );
}

function UrlImportModal({ open, onClose, onImported }: { open: boolean; onClose: () => void; onImported: () => void }) {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<{ ok: boolean; extracted?: Record<string, unknown> | null; error?: string | null; partial?: boolean } | null>(null);
  const [saving, setSaving] = useState(false);
  const toast = useToast();
  const imp = useAsync<typeof result, [string]>();

  const doImport = () => {
    imp.run(() => jobsApi.importUrl(url), url).then((res) => {
      if (res) setResult(res);
    }).catch(() => {});
  };

  const saveListing = async () => {
    if (!result?.extracted) return;
    setSaving(true);
    try {
      const ex = result.extracted as Record<string, unknown>;
      await jobsApi.createManual({
        title: ex.title,
        company: ex.company,
        location: ex.location,
        workplace_type: ex.workplace_type,
        employment_type: ex.employment_type,
        description: ex.description,
        requirements: (ex.requirements as string[]) || [],
        application_url: url,
        url,
      });
      toast.success("Job saved to your listings");
      onImported();
      onClose();
    } catch {
      toast.error("Could not save job");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Import job from URL"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>Close</Button>
          {result?.extracted?.title && (
            <Button onClick={saveListing} loading={saving}>Save listing</Button>
          )}
        </>
      }
    >
      <p className="mb-3 text-sm text-secondary">
        Paste a public job posting URL. CareerPilot fetches it securely
        (SSRF-protected) and extracts structured details.
      </p>
      <div className="flex gap-2">
        <input
          className="flex-1 rounded-lg border border-border bg-input px-3 py-2 text-sm text-primary placeholder:text-muted focus:border-accent/60 focus:outline-none"
          placeholder="https://boards.greenhouse.io/..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          aria-label="Job URL"
        />
        <Button onClick={doImport} loading={imp.loading} disabled={!url.trim()}>
          Import
        </Button>
      </div>
      {imp.error && <p className="mt-3 text-xs text-danger">{imp.error}</p>}
      {result && !result.ok && (
        <p className="mt-3 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-xs text-danger">
          {result.error}
        </p>
      )}
      {result?.extracted && (
        <pre className="mt-3 max-h-56 overflow-auto rounded-lg bg-input p-3 text-[11px] text-secondary">
          {JSON.stringify(result.extracted, null, 2)}
        </pre>
      )}
      {result?.partial && (
        <p className="mt-2 text-xs text-warning">
          Some fields could not be extracted. Review and edit after saving.
        </p>
      )}
    </Modal>
  );
}

function ManualJobModal({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({
    title: "",
    company: "",
    location: "",
    workplace_type: "",
    employment_type: "",
    description: "",
    requirements: "",
    application_url: "",
  });
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  const save = async () => {
    if (!form.title.trim() || !form.company.trim()) return;
    setSaving(true);
    try {
      await jobsApi.createManual({
        ...form,
        requirements: form.requirements.split("\n").map((s) => s.trim()).filter(Boolean),
      });
      toast.success("Job added");
      onCreated();
      onClose();
    } catch {
      toast.error("Could not save job");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Add job manually"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={save} loading={saving} disabled={!form.title.trim() || !form.company.trim()}>Save</Button>
        </>
      }
    >
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <Input label="Job title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <Input label="Company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input label="Location" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
          <Select label="Workplace type" value={form.workplace_type} onChange={(e) => setForm({ ...form, workplace_type: e.target.value })} options={[{ value: "", label: "Unknown" }, ...WORKPLACE_TYPES.map((w) => ({ value: w, label: w }))]} />
        </div>
        <Select label="Employment type" value={form.employment_type} onChange={(e) => setForm({ ...form, employment_type: e.target.value })} options={[{ value: "", label: "Unknown" }, ...EMPLOYMENT_TYPES.map((w) => ({ value: w, label: w }))]} />
        <Input label="Application URL" value={form.application_url} onChange={(e) => setForm({ ...form, application_url: e.target.value })} placeholder="https://..." />
        <Textarea label="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <Textarea label="Requirements (one per line)" value={form.requirements} onChange={(e) => setForm({ ...form, requirements: e.target.value })} />
      </div>
    </Modal>
  );
}


