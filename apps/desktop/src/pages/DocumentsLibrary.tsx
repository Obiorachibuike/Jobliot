import { useState } from "react";
import { FileText, Download, Trash2, CheckCircle2, Clock, Eye } from "lucide-react";
import { useApi, useAsync } from "../hooks/useApi";
import { documentsApi } from "../services/backend";
import type { CareerDocument, DocumentVersion } from "../types/api";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  ConfirmDialog,
  EmptyState,
  Modal,
  Spinner,
  Tabs,
} from "../components/ui/index";
import { useToast } from "../components/ui/Toast";
import { cx } from "../components/ui/index";

const statusTone: Record<string, "success" | "warning" | "accent" | "neutral"> = {
  draft: "neutral",
  under_review: "neutral",
  needs_user_confirmation: "warning",
  revision_required: "warning",
  ready_for_approval: "accent",
  approved: "success",
  exported: "success",
};

export default function DocumentsLibrary() {
  const [tab, setTab] = useState("all");
  const docs = useApi(() => documentsApi.list(), []);
  const [selected, setSelected] = useState<CareerDocument | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const del = useAsync<unknown, []>();
  const toast = useToast();

  const all = docs.data || [];
  const filtered = tab === "all" ? all : all.filter((d) => d.kind === tab);

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-primary">Documents</h1>
          <p className="mt-1 text-sm text-muted">
            Master CV, tailored documents, and exports.
          </p>
        </div>
      </div>

      <Tabs
        active={tab}
        onChange={setTab}
        tabs={[
          { id: "all", label: "All" },
          { id: "cv", label: "CVs" },
          { id: "cover_letter", label: "Cover letters" },
        ]}
      />

      <div className="mt-4">
        {docs.loading ? (
          <div className="flex justify-center py-16"><Spinner /></div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<FileText className="h-8 w-8" />}
            title="No documents yet"
            description="Generate a tailored CV or cover letter in the Application Studio."
          />
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {filtered.map((d) => (
              <Card key={d.id} className="cursor-pointer transition-colors hover:border-accent/40" onClick={() => setSelected(d)}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-primary">{d.title}</div>
                    <div className="mt-0.5 text-xs text-muted">
                      {d.kind === "cv" ? "CV" : "Cover letter"} · v{d.current_version} · {new Date(d.updated_at).toLocaleDateString()}
                    </div>
                  </div>
                  <Badge tone={statusTone[d.status] || "neutral"}>{d.status.replace(/_/g, " ")}</Badge>
                </div>
                {d.approved_by_user && (
                  <div className="mt-2 flex items-center gap-1 text-xs text-success">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Approved by you
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>

      {selected && (
        <DocumentModal
          document={selected}
          onClose={() => {
            setSelected(null);
            docs.refetch();
          }}
          onDelete={() => {
            setDeleteId(selected.id);
          }}
        />
      )}

      <ConfirmDialog
        open={deleteId !== null}
        title="Delete document"
        message="Delete this document and all its versions? This cannot be undone."
        confirmLabel="Delete"
        onCancel={() => setDeleteId(null)}
        onConfirm={async () => {
          if (deleteId === null) return;
          try {
            await documentsApi.remove(deleteId);
            toast.success("Document deleted");
            docs.refetch();
          } catch {
            toast.error("Could not delete");
          }
          setDeleteId(null);
        }}
      />
    </div>
  );
}

function DocumentModal({ document: doc, onClose, onDelete }: { document: CareerDocument; onClose: () => void; onDelete: () => void }) {
  const [tab, setTab] = useState("preview");
  const [exporting, setExporting] = useState(false);
  const toast = useToast();
  const versions = useApi(() => documentsApi.versions(doc.id), [doc.id]);

  const content = (doc.content || {}) as {
    title?: string;
    subtitle?: string;
    contact_line?: string;
    sections?: { id: string; heading: string; blocks: { type: string; text?: string | null; title?: string | null; organization?: string | null; date_range?: string | null; items?: string[] | null; meta?: string | null }[] }[];
  };

  const doExport = async (format: string) => {
    setExporting(true);
    try {
      const result = await documentsApi.exportDocument(doc.id, format);
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
    } finally {
      setExporting(false);
    }
  };

  return (
    <Modal
      open
      onClose={onClose}
      title={doc.title}
      footer={
        <>
          <Button variant="ghost" onClick={onDelete} className="mr-auto text-danger">Delete</Button>
          <Button variant="secondary" onClick={() => doExport("txt")} loading={exporting}>TXT</Button>
          <Button variant="secondary" onClick={() => doExport("docx")} loading={exporting}>DOCX</Button>
          <Button onClick={() => doExport("pdf")} loading={exporting}><Download className="h-4 w-4" /> PDF</Button>
        </>
      }
    >
      <Tabs active={tab} onChange={setTab} tabs={[{ id: "preview", label: "Preview" }, { id: "versions", label: `Versions (${versions.data?.length || 0})` }]} />
      <div className="mt-4">
        {tab === "preview" && (
          <div className="document-preview max-h-[55vh] overflow-y-auto rounded-lg p-5 text-black">
            <h2 className="text-lg font-bold">{content.title}</h2>
            {content.subtitle && <p className="text-sm italic text-gray-600">{content.subtitle}</p>}
            {content.contact_line && <p className="mt-1 text-xs text-gray-600">{content.contact_line}</p>}
            {(content.sections || []).map((s) => (
              <div key={s.id} className="mt-4">
                {s.heading && <h3 className="mb-1 border-b border-gray-300 pb-0.5 text-sm font-bold uppercase text-gray-800">{s.heading}</h3>}
                {s.blocks.map((b, i) => (
                  <div key={i} className="mb-1.5">
                    {b.type === "paragraph" && <p className="text-sm text-gray-800">{b.text}</p>}
                    {b.type === "bullets" && (
                      <ul className="list-disc space-y-0.5 pl-5">
                        {(b.items || []).map((it, j) => <li key={j} className="text-sm text-gray-800">{it}</li>)}
                      </ul>
                    )}
                    {b.type === "entry" && (
                      <div>
                        <div className="text-sm font-semibold text-gray-900">
                          {b.title}{b.organization ? ` · ${b.organization}` : ""}
                          {b.date_range ? <span className="ml-2 text-xs font-normal text-gray-500">{b.date_range}</span> : null}
                        </div>
                        {b.meta && <p className="text-xs italic text-gray-500">{b.meta}</p>}
                        {(b.items || []).length > 0 && (
                          <ul className="mt-0.5 list-disc space-y-0.5 pl-5">
                            {(b.items || []).map((it, j) => <li key={j} className="text-xs text-gray-700">{it}</li>)}
                          </ul>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
        {tab === "versions" && (
          <div className="space-y-2">
            {(versions.data || []).map((v) => (
              <div key={v.id} className="rounded-lg border border-border bg-elevated px-3 py-2">
                <div className="flex items-center gap-2">
                  <Badge tone="neutral">v{v.version_number}</Badge>
                  <Badge tone={v.agent_stage === "review" ? "warning" : "neutral"}>{v.agent_stage}</Badge>
                  <span className="text-[11px] text-muted">{new Date(v.created_at).toLocaleString()}</span>
                </div>
                {v.change_summary && <p className="mt-1 text-xs text-secondary">{v.change_summary}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}
