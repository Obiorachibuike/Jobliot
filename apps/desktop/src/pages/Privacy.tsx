import { useState } from "react";
import {
  Download,
  Database,
  Upload,
  Trash2,
  ShieldCheck,
  FileCheck,
} from "lucide-react";
import { useAsync } from "../hooks/useApi";
import { privacyApi } from "../services/backend";
import {
  Button,
  Card,
  CardHeader,
  ConfirmDialog,
  Spinner,
} from "../components/ui/index";
import { useToast } from "../components/ui/Toast";

export default function PrivacyPage() {
  const toast = useToast();
  const exportData = useAsync<{ filename: string; content_b64: string; size_bytes: number }, []>();
  const backup = useAsync<{ ok: boolean; path: string; size_bytes: number }, []>();
  const integrity = useAsync<{ ok: boolean; detail?: string }, []>();
  const del = useAsync<unknown, []>();

  const [restoreFile, setRestoreFile] = useState<File | null>(null);
  const [restoreOpen, setRestoreOpen] = useState(false);
  const [deleteScope, setDeleteScope] = useState<"everything" | "documents" | "jobs" | "applications" | null>(null);

  const doExport = async () => {
    try {
      const result = await exportData.run(() => privacyApi.exportData());
      if (!result) return;
      const binary = atob(result.content_b64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      const blob = new Blob([bytes], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = result.filename;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`Exported ${result.filename}`);
    } catch {
      toast.error("Export failed");
    }
  };

  const doBackup = async () => {
    try {
      const result = await backup.run(() => privacyApi.backup());
      if (result) toast.success(`Backup created (${result.size_bytes} bytes)`);
    } catch {
      toast.error("Backup failed");
    }
  };

  const doRestore = async () => {
    if (!restoreFile) return;
    try {
      await privacyApi.restore(restoreFile);
      toast.success("Database restored - restart the backend to use it");
      setRestoreOpen(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Restore failed");
    }
  };

  const doDelete = async () => {
    if (!deleteScope) return;
    try {
      await del.run(() => privacyApi.deleteScope({ scope: deleteScope, confirm: true }));
      toast.success("Deleted");
      setDeleteScope(null);
    } catch {
      toast.error("Could not delete");
    }
  };

  return (
    <div className="mx-auto max-w-3xl p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-primary">Privacy & Data</h1>
        <p className="mt-1 text-sm text-muted">
          Your data lives on your machine. Export, back up, or delete
          it at any time.
        </p>
      </div>

      <div className="mb-4 rounded-lg border border-accent/30 bg-accent/5 px-4 py-3">
        <div className="flex items-start gap-2">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
          <p className="text-xs text-secondary">
            CareerPilot is local-first. Your career profile, documents,
            and application history are stored in a SQLite database on
            your computer. Nothing is uploaded anywhere unless you
            explicitly configure a cloud AI provider, and even then
            only the specific text being processed is sent.
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader title="Export all data" subtitle="Everything as JSON" />
          <p className="mb-3 text-xs text-muted">
            Includes your profile, jobs, documents, applications,
            interviews, and usage records. API keys are never
            included.
          </p>
          <Button onClick={doExport} loading={exportData.loading}>
            <Download className="h-4 w-4" /> Export JSON
          </Button>
        </Card>

        <Card>
          <CardHeader title="Database backup" subtitle="Copy the SQLite file" />
          <p className="mb-3 text-xs text-muted">
            A byte-for-byte copy of the local database for safekeeping.
          </p>
          <Button onClick={doBackup} loading={backup.loading}>
            <Database className="h-4 w-4" /> Create backup
          </Button>
        </Card>

        <Card>
          <CardHeader title="Restore backup" subtitle="Replace the database from a backup file" />
          <p className="mb-3 text-xs text-muted">
            The backup is integrity-checked before anything is replaced.
          </p>
          <input
            type="file"
            accept=".db,.sqlite,.sqlite3"
            onChange={(e) => setRestoreFile(e.target.files?.[0] || null)}
            className="mb-2 text-xs text-secondary"
            aria-label="Backup file"
          />
          <Button
            variant="secondary"
            disabled={!restoreFile}
            onClick={() => setRestoreOpen(true)}
          >
            <Upload className="h-4 w-4" /> Restore
          </Button>
        </Card>

        <Card>
          <CardHeader title="Database integrity" subtitle="Verify the SQLite file" />
          <p className="mb-3 text-xs text-muted">
            Run SQLite's integrity check on your database.
          </p>
          <Button variant="secondary" onClick={async () => {
            try {
              const result = await integrity.run(() => privacyApi.integrity());
              if (result) {
                if (result.ok) toast.success("Database integrity OK");
                else toast.error(result.detail || "Integrity check failed");
              }
            } catch {
              toast.error("Check failed");
            }
          }} loading={integrity.loading}>
            <FileCheck className="h-4 w-4" /> Check integrity
          </Button>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader title="Delete data" subtitle="Selective or complete deletion" />
        <p className="mb-3 text-xs text-muted">
          Deletion is permanent and requires explicit confirmation.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button variant="danger" onClick={() => setDeleteScope("everything")}>
            <Trash2 className="h-4 w-4" /> Delete everything
          </Button>
          <Button variant="outline" onClick={() => setDeleteScope("documents")}>Delete documents</Button>
          <Button variant="outline" onClick={() => setDeleteScope("jobs")}>Delete jobs</Button>
          <Button variant="outline" onClick={() => setDeleteScope("applications")}>Delete applications</Button>
        </div>
      </Card>

      <ConfirmDialog
        open={restoreOpen}
        title="Restore backup"
        message="This replaces your current database with the backup. Continue?"
        confirmLabel="Restore"
        destructive={false}
        onCancel={() => setRestoreOpen(false)}
        onConfirm={doRestore}
      />
      <ConfirmDialog
        open={deleteScope !== null}
        title={`Delete ${deleteScope || ""}`}
        message={
          deleteScope === "everything"
            ? "This permanently deletes your entire CareerPilot profile, jobs, documents, applications, and history. This cannot be undone."
            : `This permanently deletes the selected ${deleteScope}. This cannot be undone.`
        }
        confirmLabel="Delete permanently"
        onCancel={() => setDeleteScope(null)}
        onConfirm={doDelete}
      />
    </div>
  );
}
