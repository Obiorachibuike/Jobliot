import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  MinusCircle,
  XCircle,
  ExternalLink,
  RefreshCw,
  Building2,
  MapPin,
  Globe,
  Calendar,
} from "lucide-react";
import { useApi, useAsync } from "../hooks/useApi";
import { applicationsApi, jobsApi } from "../services/backend";
import type { JobListing, MatchReport } from "../types/api";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  Spinner,
} from "../components/ui";
import { useToast } from "../components/ui/Toast";
import { matchCategoryMeta } from "../theme/match";
import { cx } from "../components/ui";

const dimensionStatusIcon = (status: string) => {
  switch (status) {
    case "match":
      return <CheckCircle2 className="h-4 w-4 text-success" />;
    case "partial":
      return <AlertTriangle className="h-4 w-4 text-warning" />;
    case "missing":
      return <MinusCircle className="h-4 w-4 text-danger" />;
    default:
      return <HelpCircle className="h-4 w-4 text-muted" />;
  }
};

export default function JobDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const listingId = Number(id);

  const listing = useApi(() => jobsApi.get(listingId), [listingId]);
  const match = useAsync<MatchReport, []>();
  const [computed, setComputed] = useState(false);

  const job = listing.data;

  const computeMatch = () => {
    match.run(() => jobsApi.match(listingId)).then((report) => {
      if (report) {
        setComputed(true);
        toast.success("Match analysis complete");
      }
    }).catch(() => toast.error("Match analysis failed"));
  };

  const addApplication = async () => {
    if (!job) return;
    try {
      await applicationsApi.create({
        job_listing_id: job.id,
        company: job.company,
        job_title: job.title,
        location: job.location,
        source_name: job.source_name,
        application_url: job.application_url,
        match_score: match.data?.overall_score,
      });
      toast.success("Added to Application Tracker");
      navigate("/applications");
    } catch {
      toast.error("Could not add application");
    }
  };

  if (listing.loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner className="h-6 w-6" />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="p-6">
        <EmptyState
          icon={<XCircle className="h-8 w-8" />}
          title="Job not found"
          action={
            <Button variant="secondary" onClick={() => navigate("/jobs")}>
              Back to jobs
            </Button>
          }
        />
      </div>
    );
  }

  const report = match.data;
  const cat = report
    ? report.category
    : job.match_category || "low_match";
  const meta = matchCategoryMeta[cat] || matchCategoryMeta.low_match;

  return (
    <div className="mx-auto max-w-4xl p-6">
      <button
        onClick={() => navigate("/jobs")}
        className="mb-4 inline-flex items-center text-sm text-muted hover:text-primary"
      >
        <ArrowLeft className="mr-1 h-4 w-4" /> Back to jobs
      </button>

      <Card className="mb-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-primary">{job.title}</h1>
            <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted">
              <span className="inline-flex items-center gap-1"><Building2 className="h-4 w-4" />{job.company}</span>
              {job.location && <span className="inline-flex items-center gap-1"><MapPin className="h-4 w-4" />{job.location}</span>}
              {job.workplace_type && <span className="inline-flex items-center gap-1"><Globe className="h-4 w-4" />{job.workplace_type}</span>}
              {job.publication_date && <span className="inline-flex items-center gap-1"><Calendar className="h-4 w-4" />{job.publication_date}</span>}
            </div>
          </div>
          <Badge tone={meta.tone as never}>{meta.label}</Badge>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <Button variant="secondary" onClick={computeMatch} loading={match.loading}>
            <Sparkles className="h-4 w-4" /> Analyze fit
          </Button>
          <Button variant="secondary" onClick={() => jobsApi.verify(job.id).then(() => { listing.refetch(); toast.success("Marked as verified"); })}>
            <RefreshCw className="h-4 w-4" /> Re-verify availability
          </Button>
          <Button onClick={addApplication}>
            Track application
          </Button>
          {job.application_url && (
            <Button
              variant="outline"
              onClick={() => window.open(job.application_url || undefined, "_blank", "noopener")}
            >
              <ExternalLink className="h-4 w-4" /> Open posting
            </Button>
          )}
        </div>
        <p className="mt-2 text-[11px] text-muted">
          CareerPilot never submits applications automatically. You
          review and submit through the employer's own site.
        </p>
      </Card>

      {job.description && (
        <Card className="mb-4">
          <CardHeader title="Description" />
          <p className="whitespace-pre-wrap text-sm text-secondary">
            {job.description}
          </p>
        </Card>
      )}

      {((job.requirements?.length ?? 0) > 0 || (job.preferred_qualifications?.length ?? 0) > 0) && (
        <div className="mb-4 grid gap-4 md:grid-cols-2">
          {(job.requirements?.length ?? 0) > 0 && (
            <Card>
              <CardHeader title="Requirements" />
              <ul className="space-y-1.5">
                { (job.requirements || []).map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                    {r}
                  </li>
                ))}
              </ul>
            </Card>
          )}
          {(job.preferred_qualifications?.length ?? 0) > 0 && (
            <Card>
              <CardHeader title="Preferred qualifications" />
              <ul className="space-y-1.5">
                { (job.preferred_qualifications || []).map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-muted" />
                    {r}
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      )}

      {match.loading && (
        <div className="flex items-center gap-3 rounded-xl border border-border bg-surface p-4">
          <Spinner className="h-5 w-5" />
          <span className="text-sm text-secondary">Analyzing fit against your verified profile...</span>
        </div>
      )}

      {match.error && (
        <p className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
          {match.error}
        </p>
      )}

      {report && <MatchReportView report={report} />}

      {computed && report && (
        <div className="mt-4 flex justify-end">
          <Button onClick={() => navigate(`/studio/${job.id}`)}>
            <Sparkles className="h-4 w-4" /> Open in Application Studio
          </Button>
        </div>
      )}
    </div>
  );
}

export function MatchReportView({ report }: { report: MatchReport }) {
  const meta = matchCategoryMeta[report.category] || matchCategoryMeta.low_match;
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader
          title={`Suitability: ${report.overall_score}/100`}
          subtitle={meta.label}
        />
        <div className="mb-4">
          <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className={cx(
                "h-full rounded-full",
                report.overall_score >= 75 ? "bg-success" : report.overall_score >= 55 ? "bg-accent" : report.overall_score >= 35 ? "bg-warning" : "bg-danger"
              )}
              style={{ width: `${report.overall_score}%` }}
            />
          </div>
        </div>
        <p className="text-sm text-secondary">{report.narrative}</p>
        {report.unknown_items?.length > 0 && (
          <p className="mt-2 rounded-lg border border-border bg-elevated px-3 py-2 text-xs text-muted">
            Could not be assessed (missing data, not a deficiency):{" "}
            {report.unknown_items.join(", ")}
          </p>
        )}
      </Card>

      <Card>
        <CardHeader
          title="Dimension breakdown"
          subtitle="Every score is computed from structured data - select a dimension for its evidence"
        />
        <div className="space-y-2">
          {report.dimensions.map((d) => (
            <div key={d.name} className="rounded-lg border border-border bg-elevated px-3 py-2.5">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  {dimensionStatusIcon(d.status)}
                  <span className="text-sm font-medium text-primary">{d.label}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-muted">weight {Math.round(d.weight * 100)}%</span>
                  <span className="text-sm font-semibold text-primary">{d.score}</span>
                </div>
              </div>
              <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                <div
                  className={cx(
                    "h-full rounded-full",
                    d.status === "match" ? "bg-success" : d.status === "partial" ? "bg-warning" : d.status === "missing" ? "bg-danger" : "bg-muted"
                  )}
                  style={{ width: `${d.score}%` }}
                />
              </div>
              <ul className="mt-2 space-y-1">
                {(d.evidence || []).map((e, i) => (
                  <li key={i} className="text-xs text-muted">{e}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Card>

      {report.strong_matches?.length > 0 && (
        <Card>
          <CardHeader title="Strong matches" />
          <ul className="space-y-1.5">
            {report.strong_matches.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                {s}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {report.missing_requirements?.length > 0 && (
        <Card>
          <CardHeader title="Requirements not yet evidenced" subtitle="Gaps in evidence - not proof you lack the skill" />
          <ul className="space-y-1.5">
            {report.missing_requirements.map((m, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                <MinusCircle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
                {m}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
