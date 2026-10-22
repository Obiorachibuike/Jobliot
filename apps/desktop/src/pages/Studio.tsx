import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Sparkles,
  FileText,
  Download,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
  History,
  ShieldCheck,
  BrainCircuit,
  PenLine,
  SearchCheck,
  RefreshCw,
  ChevronDown,
} from "lucide-react";
import { useApi, useAsync } from "../hooks/useApi";
import { documentsApi, jobsApi, studioApi } from "../services/backend";
import type {
  CareerDocument,
  DocumentBlock,
  JobListing,
  ReviewResult,
  Strategy,
  StructuredDocument,
} from "../types/api";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  Progress,
  Select,
  Spinner,
  Tabs,
} from "../components/ui";
import { useToast } from "../components/ui/Toast";
import { cx } from "../components/ui";

type Stage = "strategy" | "draft" | "review" | "revision";

export default function Studio() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const toast = useToast();

  const [selectedJobId, setSelectedJobId] = useState<number | null>(
    jobId ? Number(jobId) : null
  );
  const [kind, setKind] = useState<"cv" | "cover_letter">("cv");
  const [templateId, setTemplateId] = useState("ats_friendly");
  const [letterLength, setLetterLength] = useState("standard");

  const jobs = useApi(() => jobsApi.list({ limit: 200 }), []);
  const templates = useApi(() => documentsApi.templates(), []);
  const existingDocs = useApi(() => documentsApi.list(), []);
  const generate = useAsync<
    {
      document_id: number;
      document: CareerDocument;
      strategy: Strategy;
      review: ReviewResult;
      status: string;
      readiness: string;
    },
    []
  >();

  const job: JobListing | null = useMemo(
    () => (jobs.data || []).find((j) => j.id === selectedJobId) || null,
    [jobs.data, selectedJobId]
  );

  const canGenerate =
    job !== null && !generate.loading && (kind === "cv" || kind === "cover_letter");

  const run = () => {
    if (!selectedJobId) return;
    generate
      .run(() =>
        studioApi.generate({
          job_listing_id: selectedJobId,
          kind,
          template_id: templateId,
          cover_letter_length: letterLength,
        })
      )
      .then((res) => {
        if (res) {
          const { readiness } = res;
          if (readiness === "ready") {
            toast.success("Draft ready for your review");
          } else {
            toast.info("Draft needs your confirmation on some points");
          }
        }
      })
      .catch(() => toast.error("Generation failed"));
  };

  const result = generate.data;
  const doc = result?.document;
  const strategy = result?.strategy;
  const review = result?.review;

  const stages: { id: Stage; label: string; icon: typeof BrainCircuit }[] = [
    { id: "strategy", label: "Strategy", icon: BrainCircuit },
    { id: "draft", label: "Draft", icon: PenLine },
    { id: "review", label: "Review", icon: SearchCheck },
    { id: "revision", label: "Revise", icon: RefreshCw },
  ];

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-primary">Application Studio</h1>
        <p className="mt-1 text-sm text-muted">
          A four-agent system drafts, reviews, and revises your
          application. You approve every document before it is used.
        </p>
      </div>

      {/* Setup panel */}
      <Card className="mb-6">
        <CardHeader
          title="New tailored document"
          subtitle="Pick a job, choose a document type and template"
        />
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <span className="mb-1 block text-xs font-medium text-secondary">Job</span>
            <Select
              value={selectedJobId ? String(selectedJobId) : ""}
              onChange={(e) => setSelectedJobId(e.target.value ? Number(e.target.value) : null)}
              options={[
                { value: "", label: "Select a job..." },
                ...(jobs.data || []).map((j) => ({
                  value: String(j.id),
                  label: `${j.title} · ${j.company}`,
                })),
              ]}
            />
            {jobs.data && jobs.data.length === 0 && (
              <p className="mt-1 text-[11px] text-muted">
                Add a job in Discover first.
              </p>
            )}
          </div>
          <div>
            <span className="mb-1 block text-xs font-medium text-secondary">Document type</span>
            <Select
              value={kind}
              onChange={(e) => setKind(e.target.value as "cv" | "cover_letter")}
              options={[
                { value: "cv", label: "Curriculum Vitae" },
                { value: "cover_letter", label: "Cover Letter" },
              ]}
            />
          </div>
          <div>
            <span className="mb-1 block text-xs font-medium text-secondary">Template</span>
            <Select
              value={templateId}
              onChange={(e) => setTemplateId(e.target.value)}
              options={(templates.data || []).map((t) => ({
                value: t.id,
                label: `${t.name}${t.ats_safe ? "" : " (visual)"}`,
              }))}
            />
          </div>
        </div>
        {kind === "cover_letter" && (
          <div className="mt-4">
            <span className="mb-1 block text-xs font-medium text-secondary">Length</span>
            <Select
              value={letterLength}
              onChange={(e) => setLetterLength(e.target.value)}
              options={[
                { value: "concise", label: "Concise (one paragraph)" },
                { value: "standard", label: "Standard (2-3 paragraphs)" },
                { value: "detailed", label: "Detailed" },
              ]}
              className="w-56"
            />
          </div>
        )}
        <div className="mt-4 flex items-center gap-3">
          <Button onClick={run} disabled={!canGenerate} loading={generate.loading}>
            <Sparkles className="h-4 w-4" />
            {generate.loading ? "Generating..." : "Generate application"}
          </Button>
          {!job && (
            <Button variant="outline" onClick={() => navigate("/jobs")}>
              Find a job <ArrowRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </Card>

      {generate.loading && (
        <Card className="mb-6">
          <div className="flex items-center gap-3">
            <Spinner className="h-5 w-5" />
            <div>
              <p className="text-sm font-medium text-primary">
                Running the agent pipeline...
              </p>
              <p className="text-xs text-muted">
                Strategy → Draft → Review → Revise (up to 2 rounds)
              </p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-4 gap-2">
            {stages.map((s) => (
              <div key={s.id} className="flex items-center gap-2 rounded-lg border border-border bg-elevated px-2 py-1.5">
                <s.icon className="h-3.5 w-3.5 animate-pulse-soft text-accent" />
                <span className="text-xs text-secondary">{s.label}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {generate.error && (
        <p className="mb-6 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
          {generate.error}
        </p>
      )}

      {result && doc && (
        <div className="space-y-6">
          {/* Readiness banner */}
          <ReadinessBanner readiness={result.readiness} status={result.status} />

          {/* Strategy */}
          {strategy && (
            <Card>
              <CardHeader
                title="Application strategy"
                subtitle={`Source: ${(strategy as unknown as { source?: string }).source === "ai" ? "AI provider" : "local deterministic engine"}`}
              />
              <div className="mb-3 rounded-lg border border-accent/30 bg-accent/5 px-3 py-2">
                <span className="text-xs font-medium text-accent">Positioning</span>
                <p className="mt-0.5 text-sm text-primary">{strategy.positioning}</p>
              </div>
              {strategy.key_messages.length > 0 && (
                <div className="mb-3">
                  <span className="text-xs font-medium text-secondary">Key messages</span>
                  <ul className="mt-1 space-y-1">
                    {strategy.key_messages.map((m, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                        {m}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="grid gap-4 md:grid-cols-2">
                {strategy.gaps.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-secondary">Gaps to address honestly</span>
                    <ul className="mt-1 space-y-1">
                      {strategy.gaps.map((g, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />
                          {g}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {strategy.keyword_targets.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-secondary">Keyword targets</span>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {strategy.keyword_targets.map((k, i) => (
                        <span key={i} className="rounded-full border border-border bg-secondary px-2 py-0.5 text-[11px] text-secondary">
                          {k}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Document + review side by side */}
          <div className="grid gap-6 lg:grid-cols-2">
            <DocumentPreview doc={doc} />
            {review && <ReviewPanel review={review} />}
          </div>

          {/* Actions */}
          <Card>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                onClick={() => doc.id && documentsApi.approve(doc.id).then(() => toast.success("Document approved"))}
                disabled={doc.status === "approved"}
              >
                <ShieldCheck className="h-4 w-4" /> Approve document
              </Button>
              <Button
                variant="secondary"
                onClick={() => doc.id && exportDoc(doc.id, "pdf", toast)}
              >
                <Download className="h-4 w-4" /> Export PDF
              </Button>
              <Button
                variant="secondary"
                onClick={() => doc.id && exportDoc(doc.id, "docx", toast)}
              >
                <Download className="h-4 w-4" /> Export DOCX
              </Button>
              <Button
                variant="secondary"
                onClick={() => doc.id && exportDoc(doc.id, "txt", toast)}
              >
                <Download className="h-4 w-4" /> Export TXT
              </Button>
              <span className="ml-auto text-xs text-muted">
                Status: <span className="font-medium text-primary">{doc.status.replace(/_/g, " ")}</span>
              </span>
            </div>
          </Card>

          <VersionHistory documentId={doc.id} />
        </div>
      )}

      {/* Existing documents */}
      {!result && (existingDocs.data || []).length > 0 && (
        <Card>
          <CardHeader title="Your documents" subtitle="Previously generated or edited documents" />
          <ul className="divide-y divide-border">
            {(existingDocs.data || []).slice(0, 10).map((d) => (
              <li key={d.id}>
                <button
                  onClick={() => navigate(`/documents`)}
                  className="flex w-full items-center gap-3 px-2 py-2.5 text-left hover:bg-elevated"
                >
                  <FileText className="h-4 w-4 text-muted" />
                  <span className="min-w-0 flex-1 truncate text-sm text-primary">{d.title}</span>
                  <Badge tone={d.status === "approved" ? "success" : d.status === "needs_user_confirmation" ? "warning" : "neutral"}>
                    {d.status.replace(/_/g, " ")}
                  </Badge>
                </button>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {!result && (existingDocs.data || []).length === 0 && !generate.loading && (
        <EmptyState
          icon={<Sparkles className="h-8 w-8" />}
          title="No documents yet"
          description="Select a job above and generate a tailored CV or cover letter. The strategy, draft, review, and revision steps all run locally."
        />
      )}
    </div>
  );
}

function ReadinessBanner({ readiness, status }: { readiness: string; status: string }) {
  const config = {
    ready: { icon: CheckCircle2, text: "Ready for your approval", cls: "border-success/40 bg-success/5 text-success" },
    needs_confirmation: { icon: AlertTriangle, text: "Needs your confirmation - review the flagged items below", cls: "border-warning/40 bg-warning/5 text-warning" },
    not_ready: { icon: XCircle, text: "Not ready - critical issues must be resolved", cls: "border-danger/40 bg-danger/5 text-danger" },
  }[readiness] || { icon: AlertTriangle, text: "Review needed", cls: "border-border bg-elevated text-secondary" };
  const Icon = config.icon;
  return (
    <div className={cx("flex items-center gap-3 rounded-xl border px-4 py-3", config.cls)}>
      <Icon className="h-5 w-5 shrink-0" />
      <div>
        <div className="text-sm font-semibold">{config.text}</div>
        <div className="text-xs opacity-80">
          Workflow status: {status.replace(/_/g, " ")} · The document is never submitted automatically.
        </div>
      </div>
    </div>
  );
}

function DocumentPreview({ doc }: { doc: CareerDocument }) {
  const content = (doc.content || {}) as StructuredDocument;
  return (
    <Card className="min-h-[420px]">
      <CardHeader
        title={content.title || doc.title}
        subtitle={content.subtitle || undefined}
        action={<Badge tone="neutral">{doc.kind === "cv" ? "CV" : "Cover letter"}</Badge>}
      />
      <div className="document-preview rounded-lg p-4 text-black">
        {content.contact_line && (
          <p className="mb-3 border-b border-gray-200 pb-2 text-xs text-gray-600">
            {content.contact_line}
          </p>
        )}
        {(content.sections || []).map((section) => (
          <div key={section.id} className="mb-4">
            {section.heading && (
              <h3 className="mb-2 border-b border-gray-300 pb-1 text-sm font-bold uppercase tracking-wide text-gray-800">
                {section.heading}
              </h3>
            )}
            {(section.blocks || []).map((block, i) => (
              <BlockPreview key={i} block={block} />
            ))}
          </div>
        ))}
      </div>
    </Card>
  );
}

function BlockPreview({ block }: { block: DocumentBlock }) {
  if (block.type === "paragraph") {
    return <p className="mb-2 text-sm text-gray-800">{block.text}</p>;
  }
  if (block.type === "bullets") {
    return (
      <ul className="mb-2 list-disc space-y-1 pl-5">
        {(block.items || []).map((item, i) => (
          <li key={i} className="text-sm text-gray-800">{item}</li>
        ))}
      </ul>
    );
  }
  if (block.type === "entry") {
    return (
      <div className="mb-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <span className="text-sm font-semibold text-gray-900">
            {block.title}
            {block.organization && <span className="font-normal text-gray-600"> · {block.organization}</span>}
          </span>
          {block.date_range && <span className="text-xs text-gray-500">{block.date_range}</span>}
        </div>
        {block.meta && <p className="text-xs italic text-gray-500">{block.meta}</p>}
        {(block.items || []).length > 0 && (
          <ul className="mt-1 list-disc space-y-0.5 pl-5">
            {(block.items || []).map((item, i) => (
              <li key={i} className="text-xs text-gray-700">{item}</li>
            ))}
          </ul>
        )}
      </div>
    );
  }
  return null;
}

function ReviewPanel({ review }: { review: ReviewResult }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const counts = [
    { label: "Critical", count: review.critical_count, cls: "text-danger" },
    { label: "Major", count: review.major_count, cls: "text-warning" },
    { label: "Minor", count: review.minor_count, cls: "text-secondary" },
    { label: "Suggestions", count: review.suggestion_count, cls: "text-accent" },
  ];
  return (
    <Card>
      <CardHeader
        title="Independent review"
        subtitle={review.overall_assessment || undefined}
        action={
          <Badge tone={review.readiness === "ready" ? "success" : review.readiness === "not_ready" ? "error" : "warning"}>
            {review.readiness.replace(/_/g, " ")}
          </Badge>
        }
      />
      <div className="mb-3 flex gap-4">
        {counts.map((c) => (
          <div key={c.label}>
            <div className={cx("text-xl font-bold", c.cls)}>{c.count}</div>
            <div className="text-[11px] text-muted">{c.label}</div>
          </div>
        ))}
      </div>
      <div className="max-h-96 space-y-2 overflow-y-auto">
        {review.findings.length === 0 && (
          <p className="text-sm text-muted">No findings. The draft passed all automated checks.</p>
        )}
        {review.findings.map((f) => (
          <div key={f.id} className="rounded-lg border border-border bg-elevated">
            <button
              onClick={() => setExpanded(expanded === f.id ? null : f.id)}
              className="flex w-full items-center gap-2 px-3 py-2 text-left"
            >
              <SeverityIcon severity={f.severity} />
              <span className="min-w-0 flex-1 truncate text-xs text-primary">{f.message}</span>
              {f.requires_user_confirmation && (
                <Badge tone="warning">needs you</Badge>
              )}
              <ChevronDown className={cx("h-3.5 w-3.5 text-muted transition-transform", expanded === f.id && "rotate-180")} />
            </button>
            {expanded === f.id && (
              <div className="space-y-2 border-t border-border px-3 py-2">
                <div className="text-xs text-muted">
                  <span className="font-medium">Evidence:</span> {f.evidence || "n/a"}
                </div>
                {f.recommendation && (
                  <div className="text-xs text-secondary">
                    <span className="font-medium">Fix:</span> {f.recommendation}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

function SeverityIcon({ severity }: { severity: string }) {
  switch (severity) {
    case "critical":
      return <XCircle className="h-4 w-4 shrink-0 text-danger" />;
    case "major":
      return <AlertTriangle className="h-4 w-4 shrink-0 text-warning" />;
    case "minor":
      return <AlertTriangle className="h-4 w-4 shrink-0 text-secondary" />;
    default:
      return <CheckCircle2 className="h-4 w-4 shrink-0 text-accent" />;
  }
}

function VersionHistory({ documentId }: { documentId: number }) {
  const versions = useApi(() => documentsApi.versions(documentId), [documentId]);
  const [open, setOpen] = useState(false);
  if (!open) {
    return (
      <Button variant="ghost" onClick={() => { versions.refetch(); setOpen(true); }}>
        <History className="h-4 w-4" /> View version history
      </Button>
    );
  }
  return (
    <Card>
      <CardHeader
        title="Version history"
        subtitle="Every agent stage and manual edit is versioned"
        action={<Button variant="ghost" size="sm" onClick={() => setOpen(false)}>Hide</Button>}
      />
      {versions.loading ? (
        <Spinner />
      ) : (
        <ul className="space-y-2">
          {(versions.data || []).map((v) => (
            <li key={v.id} className="rounded-lg border border-border bg-elevated px-3 py-2">
              <div className="flex items-center gap-2">
                <Badge tone="neutral">v{v.version_number}</Badge>
                <Badge tone={v.agent_stage === "review" ? "warning" : v.agent_stage === "revision" ? "accent" : "neutral"}>
                  {v.agent_stage}
                </Badge>
                <span className="text-xs text-muted">{new Date(v.created_at).toLocaleString()}</span>
              </div>
              {v.change_summary && <p className="mt-1 text-xs text-secondary">{v.change_summary}</p>}
              {(v.findings || []).length > 0 && (
                <p className="mt-1 text-[11px] text-muted">
                  {v.findings.length} finding(s) recorded this round
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

async function exportDoc(id: number, format: string, toast: ReturnType<typeof useToast>) {
  try {
    const result = await documentsApi.exportDocument(id, format);
    const binary = atob(result.content_b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    const blob = new Blob([bytes], { type: result.mime_type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = result.filename;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Exported ${result.filename}`);
  } catch (e) {
    toast.error(e instanceof Error ? e.message : "Export failed");
  }
}
